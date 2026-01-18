import logging
from datetime import datetime
from fastapi import APIRouter, Request, HTTPException, Security, Depends
from dependencies import verify_api_key, limiter
from logic.gsheets_handler import get_sheets_handler
from logic.exchange_rate import get_usd_to_idr_rate, convert_usd_to_idr
from models.schemas import TransactionCreate, TransactionUpdate, InvestmentCreate, TransferCreate
from services.transaction_service import create_transfer_pair
from models.enums import Currency

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["transactions"])

@router.post("/transactions")
@limiter.limit("10/minute")
async def create_transaction(
    request: Request,
    transaction: TransactionCreate,
    api_key: str = Security(verify_api_key)
):
    """
    Create a new transaction manually using Pydantic model (Issue 1.2).
    Rate limited to 10 requests per minute (Issue 3.2).
    Protected with API key authentication (Issue 3.3).
    """
    try:
        sheets = get_sheets_handler()
        
        new_id = sheets.append_transaction(
            date=transaction.date,
            account=transaction.account,
            category=transaction.category,
            subcategory=transaction.subcategory,
            note=transaction.description,
            amount=transaction.amount,
            transaction_type=transaction.type,
            status=transaction.status
        )
        return {"status": "success", "message": "Transaction created", "id": new_id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating transaction: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/transactions/{transaction_id}")
async def update_transaction(
    transaction_id: str,
    transaction: TransactionUpdate,
    api_key: str = Security(verify_api_key)
):
    """
    Update a transaction by ID using Pydantic model (Issue 1.2 & 2.1).
    Protected with API key authentication (Issue 3.3).
    """
    try:
        sheets = get_sheets_handler()
        # Convert Pydantic model to dict, excluding None values
        data = transaction.model_dump(exclude_none=True)
        if sheets.update_transaction_by_id(transaction_id, data):
            return {"status": "success", "message": "Transaction updated"}
        else:
            raise HTTPException(status_code=404, detail="Transaction not found")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating transaction: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/transactions/{transaction_id}")
async def delete_transaction(transaction_id: str, api_key: str = Security(verify_api_key)):
    """
    Delete a transaction by ID.
    Protected with API key authentication (Issue 3.3).
    """
    try:
        sheets = get_sheets_handler()
        if sheets.delete_transaction_by_id(transaction_id):
            return {"status": "success", "message": "Transaction deleted"}
        else:
            raise HTTPException(status_code=404, detail="Transaction not found")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting transaction: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/investments")
@limiter.limit("10/minute")
async def create_investment(
    request: Request,
    investment: InvestmentCreate,
    api_key: str = Security(verify_api_key)
):
    """
    Create a new investment using Pydantic model (Issue 1.2).
    Supports optional source_account for tracking money flow from bank to RDN.
    Rate limited to 10 requests per minute (Issue 3.2).
    Protected with API key authentication (Issue 3.3).
    """
    try:
        sheets = get_sheets_handler()

        # Extract and validate values
        symbol = investment.symbol.upper()
        shares = investment.shares
        price = investment.price
        account = investment.account
        source_account = investment.source_account
        currency = investment.currency
        purchase_date = investment.date or datetime.now().strftime('%Y-%m-%d')

        total_cost = shares * price

        # Get exchange rate for USD transactions (Issue 2.2 fix)
        exchange_rate = 1.0
        if currency == Currency.USD.value:
            exchange_rate = await get_usd_to_idr_rate()
            logger.info(f"Dashboard investment: Using USD/IDR exchange rate: {exchange_rate}")

        # Convert to IDR for transaction log (all transactions stored in IDR)
        total_cost_idr = convert_usd_to_idr(total_cost, exchange_rate) if currency == Currency.USD.value else total_cost

        # Track flag reasons
        flag_reasons = []

        # Default investment account based on currency if not specified
        if not account:
            if currency == Currency.USD.value:
                account = "Pluang"
                flag_reasons.append("Investment account defaulted to Pluang (USD)")
            else:
                account = "Stockbit"
                flag_reasons.append("Investment account defaulted to Stockbit (IDR)")
            logger.info(f"Dashboard: No investment account for {symbol}, defaulting to {account}")

        # Default to BCA if no source account specified
        if not source_account:
            source_account = "BCA"
            flag_reasons.append("Source account defaulted to BCA")
            logger.info(f"Dashboard: No source account for {symbol} purchase, defaulting to BCA")

        is_flagged = len(flag_reasons) > 0
        status = "Flagged" if is_flagged else "Normal"

        # Create transfer entries for money flow tracking using helper function (Issue 5.1)
        create_transfer_pair(
            sheets=sheets,
            date=purchase_date,
            from_account=source_account,
            to_account=account,
            amount=total_cost_idr,
            note_prefix=f"Transfer for {symbol} purchase",
            status=status
        )

        # Create Asset transaction from RDN account (in IDR)
        sheets.append_transaction(
            date=purchase_date,
            account=account,
            category='Investment',
            subcategory='Stocks',
            note=f"Buy {symbol} ({currency})",
            amount=total_cost_idr,
            transaction_type='Asset',
            status=status
        )

        # Update investments sheet with currency and exchange rate (Issue 2.3 fix)
        sheets.update_investment(
            symbol=symbol,
            shares_change=shares,
            price=price,
            account=account,
            purchase_date=purchase_date,
            currency=currency,
            exchange_rate=exchange_rate
        )

        flagged_note = f" (flagged: {'; '.join(flag_reasons)})" if is_flagged else ""
        return {
            "status": "success",
            "message": f"Added {shares} shares of {symbol} to {account} (funded from {source_account}){flagged_note}",
            "investment": {
                "symbol": symbol,
                "shares": shares,
                "price": price,
                "total_cost": total_cost,
                "account": account,
                "source_account": source_account,
                "currency": currency,
                "is_flagged": is_flagged,
                "flag_reasons": flag_reasons if is_flagged else None
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating investment: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/transfers")
@limiter.limit("10/minute")
async def create_transfer(
    request: Request,
    transfer: TransferCreate,
    api_key: str = Security(verify_api_key)
):
    """
    Create a transfer between accounts using Pydantic model and helper function (Issues 1.2 and 5.1).
    Rate limited to 10 requests per minute (Issue 3.2).
    Protected with API key authentication (Issue 3.3).
    """
    try:
        sheets = get_sheets_handler()

        # Use helper function to create transfer pair
        create_transfer_pair(
            sheets=sheets,
            date=transfer.date,
            from_account=transfer.from_account,
            to_account=transfer.to_account,
            amount=transfer.amount,
            note_prefix=transfer.note or "Transfer",
            status="Normal"
        )

        return {
            "status": "success",
            "message": f"Transferred {transfer.amount} from {transfer.from_account} to {transfer.to_account}"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating transfer: {e}")
        raise HTTPException(status_code=500, detail=str(e))
