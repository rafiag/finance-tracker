from datetime import datetime
import logging

from logic.gsheets_handler import get_sheets_handler, GoogleSheetsHandler
from logic.ai_processor import get_ai_processor
from logic.telegram_utils import get_telegram_handler
from logic.exchange_rate import get_usd_to_idr_rate, convert_usd_to_idr
from models.enums import TransactionType, TransactionStatus, Currency

logger = logging.getLogger(__name__)

def create_transfer_pair(
    sheets: GoogleSheetsHandler,
    date: str,
    from_account: str,
    to_account: str,
    amount: float,
    note_prefix: str = "Transfer",
    status: str = TransactionStatus.NORMAL.value
) -> None:
    """Create a matched pair of Transfer-In and Transfer-Out transactions (Issue 5.1).
    
    Args:
        sheets: GoogleSheetsHandler instance
        date: Transaction date in YYYY-MM-DD format
        from_account: Source account name
        to_account: Destination account name
        amount: Transfer amount
        note_prefix: Prefix for transfer notes (e.g., "Transfer", "Transfer for AAPL purchase")
        status: Transaction status (Normal/Flagged)
    """
    # Transfer-Out from source account
    sheets.append_transaction(
        date=date,
        account=from_account,
        category="Transfer",
        subcategory="Transfer-Out",
        note=f"{note_prefix} to {to_account}",
        amount=amount,
        transaction_type=TransactionType.TRANSFER.value,
        status=status
    )
    # Transfer-In to destination account
    sheets.append_transaction(
        date=date,
        account=to_account,
        category="Transfer",
        subcategory="Transfer-In",
        note=f"{note_prefix} from {from_account}",
        amount=amount,
        transaction_type=TransactionType.TRANSFER.value,
        status=status
    )


async def process_transaction(
    text: str | None,
    photo_file_id: str | None
) -> dict:
    """
    Process a transaction from Telegram message.
    """
    sheets = get_sheets_handler()
    ai = get_ai_processor()
    telegram = get_telegram_handler()
    
    # Get context for AI
    categories_context = sheets.get_category_list_for_prompt()
    accounts_context = sheets.get_account_list_for_prompt()
    investments_context = sheets.get_investment_list_for_prompt()
    
    # Download image if present
    image_data = None
    image_mime_type = "image/jpeg"
    if photo_file_id:
        image_data, image_mime_type = await telegram.download_file(photo_file_id)
    
    # Process with AI
    transaction_data = await ai.process_transaction(
        user_message=text,
        image_data=image_data,
        image_mime_type=image_mime_type,
        categories_context=categories_context,
        accounts_context=accounts_context,
        current_investments=investments_context
    )
    
    current_date = datetime.now().strftime("%Y-%m-%d")
    status = TransactionStatus.FLAGGED.value if transaction_data.is_flagged else TransactionStatus.NORMAL.value
    
    # --- Get exchange rate for USD transactions ---
    currency = transaction_data.currency
    exchange_rate = 1.0
    if currency == Currency.USD.value:
        exchange_rate = await get_usd_to_idr_rate()
        logger.info(f"Using USD/IDR exchange rate: {exchange_rate}")

    # --- Investment Orchestration ---
    if transaction_data.transaction_type == TransactionType.TRADE_BUY.value:
        total_cost = transaction_data.amount

        # Calculate shares if not provided (when user gives total amount instead of shares)
        shares = transaction_data.shares
        price = transaction_data.price_per_share

        if shares is None and price is not None and price > 0:
            # User provided total amount and price, calculate shares
            shares = total_cost / price
        elif shares is None and price is None:
            # Neither provided - flag the transaction and use defaults
            logger.warning(f"Trade_Buy missing shares and price, using amount as placeholder")
            shares = 1
            price = total_cost
        elif price is None and shares is not None and shares > 0:
            # User provided shares but not price
            price = total_cost / shares

        # Convert to IDR for transaction log (keeps all transactions in IDR)
        amount_idr = convert_usd_to_idr(total_cost, exchange_rate) if currency == Currency.USD.value else total_cost

        # Get source account (bank account where money comes from)
        source_account = transaction_data.source_account
        rdn_account = transaction_data.account  # Investment/RDN account

        # Default investment account based on currency if not specified
        if not rdn_account:
            if currency == Currency.USD.value:
                rdn_account = "Pluang"
                logger.info(f"No investment account specified for USD stock, defaulting to Pluang")
            else:
                rdn_account = "Stockbit"
                logger.info(f"No investment account specified for IDR stock, defaulting to Stockbit")
            status = TransactionStatus.FLAGGED.value  # Flag because investment account was assumed

        # Default to BCA if no source account specified, and flag for review
        if not source_account:
            source_account = "BCA"
            status = TransactionStatus.FLAGGED.value  # Flag because source account was assumed
            logger.info(f"No source account specified for Trade_Buy, defaulting to BCA and flagging")

        # Create transfer entries for money flow tracking using helper function (Issue 5.1)
        if source_account:
            create_transfer_pair(
                sheets=sheets,
                date=current_date,
                from_account=source_account,
                to_account=rdn_account,
                amount=amount_idr,
                note_prefix=f"Transfer for {transaction_data.investment_symbol} purchase",
                status=status
            )
            logger.info(f"Created transfer entries: {source_account} -> {rdn_account} for {amount_idr} IDR")

        # Step 3: Log as Asset acquisition from RDN (always in IDR)
        asset_note = f"Buy {transaction_data.investment_symbol} ({currency})"
        if currency == Currency.USD.value:
            asset_note += f" @ Rate {exchange_rate:,.0f}"

        sheets.append_transaction(
            date=current_date, account=rdn_account,
            category=transaction_data.category, subcategory=transaction_data.subcategory,
            note=asset_note, amount=amount_idr,
            transaction_type=TransactionType.ASSET.value, status=status
        )
        # Update Portfolio (keeps native currency for accurate tracking)
        sheets.update_investment(
            symbol=transaction_data.investment_symbol,
            shares_change=shares,
            price=price,
            account=rdn_account,
            purchase_date=current_date,
            currency=currency,
            exchange_rate=exchange_rate
        )
    
    elif transaction_data.transaction_type == TransactionType.TRADE_SELL.value:
        # Find avg price to calculate split
        portfolio = sheets.get_investments()
        inv = next((i for i in portfolio if i['symbol'] == transaction_data.investment_symbol), None)

        # Use existing investment's currency if available
        inv_currency = inv.get('currency', Currency.IDR.value) if inv else currency

        # Calculate shares/price if not provided
        shares = transaction_data.shares
        price = transaction_data.price_per_share
        total_amount = transaction_data.amount

        if shares is None and price is not None and price > 0:
            shares = total_amount / price
        elif price is None and shares is not None and shares > 0:
            price = total_amount / shares
        elif shares is None and price is None:
            # Fallback: use portfolio avg price if available
            if inv and inv.get('avg_price'):
                price = inv['avg_price']
                shares = total_amount / price
            else:
                logger.warning(f"Trade_Sell missing shares and price, using amount as placeholder")
                shares = 1
                price = total_amount

        avg_buy_price = inv['avg_price'] if inv else price
        base_cost = shares * avg_buy_price
        capital_gain = total_amount - base_cost

        # Get exchange rate for this currency
        sell_exchange_rate = exchange_rate if inv_currency == Currency.USD.value else 1.0

        # Convert to IDR for transaction log
        base_cost_idr = convert_usd_to_idr(base_cost, sell_exchange_rate) if inv_currency == Currency.USD.value else base_cost
        capital_gain_idr = convert_usd_to_idr(capital_gain, sell_exchange_rate) if inv_currency == Currency.USD.value else capital_gain

        # 1. Log Return of Capital (Asset) - in IDR
        roc_note = f"Sell {transaction_data.investment_symbol} (Return of Capital) ({inv_currency})"
        if inv_currency == Currency.USD.value:
            roc_note += f" @ Rate {sell_exchange_rate:,.0f}"

        sheets.append_transaction(
            date=current_date, account=transaction_data.account,
            category=transaction_data.category, subcategory=transaction_data.subcategory,
            note=roc_note,
            amount=base_cost_idr, transaction_type=TransactionType.ASSET.value, status=status
        )
        # 2. Log Capital Gain (Income) - in IDR
        gain_note = f"Sell {transaction_data.investment_symbol} (Gain) ({inv_currency})"
        if inv_currency == Currency.USD.value:
            gain_note += f" @ Rate {sell_exchange_rate:,.0f}"

        sheets.append_transaction(
            date=current_date, account=transaction_data.account,
            category="Income", subcategory="Capital Gains",
            note=gain_note,
            amount=capital_gain_idr, transaction_type=TransactionType.INCOME.value, status=status
        )
        # Update Portfolio (native currency)
        sheets.update_investment(
            symbol=transaction_data.investment_symbol,
            shares_change=-shares,
            price=price,
            realized_pl=capital_gain,
            currency=inv_currency,
            exchange_rate=sell_exchange_rate
        )
    
    elif transaction_data.transaction_type == TransactionType.TRANSFER.value:
        # Transfer: create two transactions (debit from source, credit to destination) using helper (Issue 5.1)
        destination = transaction_data.destination_account or "Unknown"
        create_transfer_pair(
            sheets=sheets,
            date=current_date,
            from_account=transaction_data.account,
            to_account=destination,
            amount=transaction_data.amount,
            note_prefix="Transfer",
            status=status
        )

    else:
        # Regular transaction (Expense, Income)
        
        final_amount = transaction_data.amount
        final_note = transaction_data.note or text
        
        # Convert to IDR if needed
        if currency == Currency.USD.value:
            final_amount = convert_usd_to_idr(transaction_data.amount, exchange_rate)
            # Add original USD amount to note for reference
            usd_note = f" (${transaction_data.amount:,.2f})"
            if final_note:
                final_note += usd_note
            else:
                final_note = usd_note.strip()
            
            logger.info(f"Converted regular USD transaction: ${transaction_data.amount} -> Rp {final_amount:,.0f}")

        sheets.append_transaction(
            date=current_date,
            account=transaction_data.account,
            category=transaction_data.category,
            subcategory=transaction_data.subcategory,
            note=final_note,
            amount=final_amount,
            transaction_type=transaction_data.transaction_type,
            status=status
        )
    
    # Determine actual values used (may differ from AI output due to defaults)
    actual_account = transaction_data.account
    actual_source_account = transaction_data.source_account
    actual_is_flagged = transaction_data.is_flagged
    actual_flag_reason = transaction_data.flag_reason

    # For Trade_Buy, accounts may have been defaulted
    if transaction_data.transaction_type == TransactionType.TRADE_BUY.value:
        flag_reasons = []

        # Check if investment account was defaulted
        if not transaction_data.account:
            if transaction_data.currency == Currency.USD.value:
                actual_account = "Pluang"
                flag_reasons.append("Investment account defaulted to Pluang (USD)")
            else:
                actual_account = "Stockbit"
                flag_reasons.append("Investment account defaulted to Stockbit (IDR)")
            actual_is_flagged = True

        # Check if source account was defaulted
        if not transaction_data.source_account:
            actual_source_account = "BCA"
            flag_reasons.append("Source account defaulted to BCA")
            actual_is_flagged = True

        if flag_reasons:
            actual_flag_reason = "; ".join(flag_reasons)

    return {
        "amount": transaction_data.amount,
        "category": transaction_data.category,
        "subcategory": transaction_data.subcategory,
        "account": actual_account,
        "destination_account": transaction_data.destination_account,
        "source_account": actual_source_account,
        "note": transaction_data.note,
        "transaction_type": transaction_data.transaction_type,
        "is_flagged": actual_is_flagged,
        "flag_reason": actual_flag_reason,
        "investment_symbol": transaction_data.investment_symbol,
        "shares": transaction_data.shares,
        "price_per_share": transaction_data.price_per_share,
        "currency": transaction_data.currency
    }
