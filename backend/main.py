"""
Finance Tracker - Main FastAPI Application
Handles Telegram webhooks and orchestrates the transaction processing pipeline
"""

import os
import logging
from datetime import datetime
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from logic.gsheets_handler import get_sheets_handler
from logic.ai_processor import get_ai_processor
from logic.telegram_utils import get_telegram_handler
from logic.exchange_rate import get_usd_to_idr_rate, convert_usd_to_idr

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup/shutdown tasks."""
    # Startup: Initialize connections
    logger.info("Starting Finance Tracker...")
    
    try:
        # Verify Google Sheets connection
        sheets = get_sheets_handler()
        sheets.connect()
        logger.info("✅ Google Sheets connected")
        
        # Verify AI processor
        _ = get_ai_processor()
        logger.info("✅ Gemini AI configured")
        
        # Verify Telegram handler
        _ = get_telegram_handler()
        logger.info("✅ Telegram handler ready")
        
    except Exception as e:
        logger.error(f"❌ Startup error: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down Finance Tracker...")


app = FastAPI(
    title="Finance Tracker",
    description="Personal finance tracker with Telegram integration",
    version="1.0.0",
    lifespan=lifespan
)

# CORS configuration for dashboard frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        os.getenv("FRONTEND_URL", ""),
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "status": "ok",
        "service": "Finance Tracker",
        "timestamp": datetime.now().isoformat()
    }


@app.get("/health")
async def health_check():
    """Detailed health check endpoint."""
    health = {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "checks": {}
    }
    
    # Check Google Sheets
    try:
        sheets = get_sheets_handler()
        sheets.connect()
        categories = sheets.get_categories()
        health["checks"]["google_sheets"] = {
            "status": "ok",
            "categories_count": len(categories)
        }
    except Exception as e:
        health["status"] = "degraded"
        health["checks"]["google_sheets"] = {
            "status": "error",
            "message": str(e)
        }
    
    return health


@app.post("/webhook/telegram")
async def telegram_webhook(request: Request):
    """
    Handle incoming Telegram webhook updates.
    This is the main entry point for processing transactions.
    """
    try:
        update = await request.json()
        logger.info(f"Received Telegram update: {update.get('update_id')}")
        
        # Security: Ignore updates that are not messages (e.g. edited_message, my_chat_member)
        if 'message' not in update:
            logger.info("Ignoring update without 'message' field")
            return JSONResponse({"status": "ignored", "reason": "not_a_message"})
        
        telegram = get_telegram_handler()
        message_data = telegram.extract_message_data(update)
        
        # Security: Check if message is from authorized user
        chat_id = message_data.get('chat_id')
        if not chat_id or not telegram.is_authorized(chat_id):
            logger.warning(f"Unauthorized message from chat_id: {chat_id}")
            return JSONResponse({"status": "ignored", "reason": "unauthorized"})
        
        # Extract message content
        text = message_data.get('text')
        photo_file_id = message_data.get('photo_file_id')
        
        # Must have either text or photo
        if not text and not photo_file_id:
            logger.info("Message has no text or photo, ignoring")
            return JSONResponse({"status": "ignored", "reason": "no_content"})
        
        # Process the transaction
        try:
            transaction = await process_transaction(text, photo_file_id)
            
            # Send confirmation
            await telegram.send_confirmation(
                amount=transaction['amount'],
                category=transaction['category'],
                subcategory=transaction['subcategory'],
                account=transaction['account'],
                is_flagged=transaction['is_flagged'],
                investment_symbol=transaction.get('investment_symbol'),
                shares=transaction.get('shares'),
                price_per_share=transaction.get('price_per_share'),
                currency=transaction.get('currency', 'IDR'),
                flag_reason=transaction.get('flag_reason')
            )
            
            return JSONResponse({
                "status": "success",
                "transaction": transaction
            })
            
        except Exception as e:
            logger.error(f"Error processing transaction: {e}")
            await telegram.send_error(
                f"Could not process your transaction. Please try again.\n\n"
                f"If this keeps happening, check that your message format is correct "
                f"(e.g., 'coffee 20k')."
            )
            return JSONResponse({
                "status": "error",
                "message": str(e)
            }, status_code=200)
    
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return JSONResponse({
            "status": "error",
            "message": str(e)
        }, status_code=200)


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
    status = "Flagged" if transaction_data.is_flagged else "Normal"
    
    # --- Get exchange rate for USD transactions ---
    currency = transaction_data.currency
    exchange_rate = 1.0
    if currency == "USD":
        exchange_rate = await get_usd_to_idr_rate()
        logger.info(f"Using USD/IDR exchange rate: {exchange_rate}")

    # --- Investment Orchestration ---
    if transaction_data.transaction_type == "Trade_Buy":
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
        amount_idr = convert_usd_to_idr(total_cost, exchange_rate) if currency == "USD" else total_cost

        # Log as Asset acquisition (always in IDR)
        sheets.append_transaction(
            date=current_date, account=transaction_data.account,
            category=transaction_data.category, subcategory=transaction_data.subcategory,
            note=f"Buy {transaction_data.investment_symbol} ({currency})", amount=amount_idr,
            transaction_type="Asset", status=status
        )
        # Update Portfolio (keeps native currency for accurate tracking)
        sheets.update_investment(
            symbol=transaction_data.investment_symbol,
            shares_change=shares,
            price=price,
            account=transaction_data.account,
            purchase_date=current_date,
            currency=currency,
            exchange_rate=exchange_rate
        )
    
    elif transaction_data.transaction_type == "Trade_Sell":
        # Find avg price to calculate split
        portfolio = sheets.get_investments()
        inv = next((i for i in portfolio if i['symbol'] == transaction_data.investment_symbol), None)

        # Use existing investment's currency if available
        inv_currency = inv.get('currency', 'IDR') if inv else currency

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
        sell_exchange_rate = exchange_rate if inv_currency == "USD" else 1.0

        # Convert to IDR for transaction log
        base_cost_idr = convert_usd_to_idr(base_cost, sell_exchange_rate) if inv_currency == "USD" else base_cost
        capital_gain_idr = convert_usd_to_idr(capital_gain, sell_exchange_rate) if inv_currency == "USD" else capital_gain

        # 1. Log Return of Capital (Asset) - in IDR
        sheets.append_transaction(
            date=current_date, account=transaction_data.account,
            category=transaction_data.category, subcategory=transaction_data.subcategory,
            note=f"Sell {transaction_data.investment_symbol} (Return of Capital) ({inv_currency})",
            amount=base_cost_idr, transaction_type="Asset", status=status
        )
        # 2. Log Capital Gain (Income) - in IDR
        sheets.append_transaction(
            date=current_date, account=transaction_data.account,
            category="Income", subcategory="Capital Gains",
            note=f"Sell {transaction_data.investment_symbol} (Gain) ({inv_currency})",
            amount=capital_gain_idr, transaction_type="Income", status=status
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
    
    elif transaction_data.transaction_type == "Transfer":
        # Transfer: create two transactions (debit from source, credit to destination)
        destination = transaction_data.destination_account or "Unknown"

        # Debit from source account (negative/outflow)
        sheets.append_transaction(
            date=current_date,
            account=transaction_data.account,
            category=transaction_data.category,
            subcategory=transaction_data.subcategory,
            note=f"Transfer to {destination}",
            amount=transaction_data.amount,
            transaction_type="Transfer",
            status=status
        )

        # Credit to destination account (positive/inflow)
        sheets.append_transaction(
            date=current_date,
            account=destination,
            category=transaction_data.category,
            subcategory=transaction_data.subcategory,
            note=f"Transfer from {transaction_data.account}",
            amount=transaction_data.amount,
            transaction_type="Transfer",
            status=status
        )

    else:
        # Regular transaction (Expense, Income)
        
        final_amount = transaction_data.amount
        final_note = transaction_data.note or text
        
        # Convert to IDR if needed
        if currency == "USD":
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
    
    return {
        "amount": transaction_data.amount,
        "category": transaction_data.category,
        "subcategory": transaction_data.subcategory,
        "account": transaction_data.account,
        "destination_account": transaction_data.destination_account,
        "note": transaction_data.note,
        "transaction_type": transaction_data.transaction_type,
        "is_flagged": transaction_data.is_flagged,
        "investment_symbol": transaction_data.investment_symbol,
        "shares": transaction_data.shares,
        "price_per_share": transaction_data.price_per_share,
        "currency": transaction_data.currency
    }


@app.post("/test/transaction")
async def test_transaction(request: Request):
    """
    Test endpoint to simulate a transaction without Telegram.
    For development/debugging only.
    """
    try:
        data = await request.json()
        text = data.get('text')
        
        if not text:
            raise HTTPException(status_code=400, detail="'text' field is required")
        
        transaction = await process_transaction(text, None)
        return transaction
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Test transaction error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# Dashboard API Endpoints
# =============================================================================

@app.get("/api/transactions")
async def get_transactions(year: int = None, month: int = None):
    """
    Get all transactions, optionally filtered by year and month.
    """
    try:
        sheets = get_sheets_handler()
        transactions = sheets.get_transactions(year=year, month=month)
        return {"transactions": transactions, "count": len(transactions)}
    except Exception as e:
        logger.error(f"Error fetching transactions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/investments")
async def get_investments():
    """
    Get all investment holdings.
    """
    try:
        sheets = get_sheets_handler()
        investments = sheets.get_investments()
        return {"investments": investments, "count": len(investments)}
    except Exception as e:
        logger.error(f"Error fetching investments: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/categories")
async def get_categories():
    """
    Get all categories and subcategories.
    """
    try:
        sheets = get_sheets_handler()
        categories = sheets.get_categories()
        return {"categories": categories, "count": len(categories)}
    except Exception as e:
        logger.error(f"Error fetching categories: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/accounts")
async def get_accounts():
    """
    Get all accounts.
    """
    try:
        sheets = get_sheets_handler()
        accounts = sheets.get_accounts()
        return {"accounts": accounts, "count": len(accounts)}
    except Exception as e:
        logger.error(f"Error fetching accounts: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/budgets")
async def get_budgets():
    """
    Get all budget records.
    """
    try:
        sheets = get_sheets_handler()
        budgets = sheets.get_budgets()
        return {"budgets": budgets, "count": len(budgets)}
    except Exception as e:
        logger.error(f"Error fetching budgets: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/summary")
async def get_summary(year: int = None, month: int = None):
    """
    Get financial summary stats for the dashboard.
    """
    try:
        sheets = get_sheets_handler()
        transactions = sheets.get_transactions(year=year, month=month)

        total_income = sum(t['amount'] for t in transactions if t['type'] == 'Income')
        total_expense = sum(t['amount'] for t in transactions if t['type'] == 'Expense')
        total_savings = total_income - total_expense

        # Count flagged transactions needing review
        flagged_count = sum(1 for t in transactions if t['status'].lower() == 'flagged')

        # Category breakdown for expenses
        expense_by_category = {}
        for t in transactions:
            if t['type'] == 'Expense':
                cat = t['category']
                expense_by_category[cat] = expense_by_category.get(cat, 0) + t['amount']

        # Income breakdown by category
        income_by_category = {}
        for t in transactions:
            if t['type'] == 'Income':
                cat = t['category']
                income_by_category[cat] = income_by_category.get(cat, 0) + t['amount']

        return {
            "total_income": total_income,
            "total_expense": total_expense,
            "total_savings": total_savings,
            "flagged_count": flagged_count,
            "transaction_count": len(transactions),
            "expense_by_category": expense_by_category,
            "income_by_category": income_by_category
        }
    except Exception as e:
        logger.error(f"Error fetching summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/api/transactions/{row_index}")
async def update_transaction(row_index: int, request: Request):
    """
    Update a transaction by row index.
    """
    try:
        data = await request.json()
        sheets = get_sheets_handler()
        sheets.update_transaction(row_index, data)
        return {"status": "success", "message": "Transaction updated"}
    except Exception as e:
        logger.error(f"Error updating transaction: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/transactions/{row_index}")
async def delete_transaction(row_index: int):
    """
    Delete a transaction by row index.
    """
    try:
        sheets = get_sheets_handler()
        sheets.delete_transaction(row_index)
        return {"status": "success", "message": "Transaction deleted"}
    except Exception as e:
        logger.error(f"Error deleting transaction: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/transactions")
async def create_transaction(request: Request):
    """
    Create a new transaction manually (from dashboard).
    """
    try:
        data = await request.json()
        sheets = get_sheets_handler()

        sheets.append_transaction(
            date=data.get('date', ''),
            account=data.get('account', ''),
            category=data.get('category', ''),
            subcategory=data.get('subcategory', ''),
            note=data.get('description', ''),
            amount=float(data.get('amount', 0)),
            transaction_type=data.get('type', 'Expense'),
            status=data.get('status', 'Normal')
        )
        return {"status": "success", "message": "Transaction created"}
    except Exception as e:
        logger.error(f"Error creating transaction: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/account-balances")
async def get_account_balances():
    """
    Get account balances from the Settings_Accounts sheet.
    Balance is calculated via Google Sheets formula for accuracy.
    """
    try:
        sheets = get_sheets_handler()
        accounts = sheets.get_accounts()

        # Return accounts with their balances (from sheet formula)
        balances = [
            {
                'name': acc['name'],
                'type': acc['type'],
                'currency': acc['currency'],
                'balance': acc['balance']
            }
            for acc in accounts
        ]

        return {"balances": balances, "count": len(balances)}
    except Exception as e:
        logger.error(f"Error fetching account balances: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/daily-expenses")
async def get_daily_expenses(year: int = None, month: int = None):
    """
    Get daily expense totals for the activity chart.
    """
    try:
        sheets = get_sheets_handler()
        transactions = sheets.get_transactions(year=year, month=month)

        # Aggregate by date
        daily = {}
        for t in transactions:
            if t['type'] == 'Expense':
                date = t['date']
                daily[date] = daily.get(date, 0) + t['amount']

        # Convert to sorted list
        result = [{'date': d, 'amount': a} for d, a in sorted(daily.items())]

        return {"daily_expenses": result, "count": len(result)}
    except Exception as e:
        logger.error(f"Error fetching daily expenses: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/budget-progress")
async def get_budget_progress(year: int = None, month: int = None):
    """
    Get budget vs actual spending per category.
    """
    try:
        sheets = get_sheets_handler()
        budgets = sheets.get_budgets()
        transactions = sheets.get_transactions(year=year, month=month)

        # Calculate actual spending per category
        spending = {}
        for t in transactions:
            if t['type'] == 'Expense':
                cat = t['category']
                spending[cat] = spending.get(cat, 0) + t['amount']

        # Combine with budgets
        progress = []
        for b in budgets:
            cat = b['category']
            budget_amount = b['monthly_budget']
            spent = spending.get(cat, 0)
            remaining = budget_amount - spent
            percentage = (spent / budget_amount * 100) if budget_amount > 0 else 0

            progress.append({
                'category': cat,
                'budget': budget_amount,
                'spent': spent,
                'remaining': remaining,
                'percentage': round(percentage, 1),
                'status': 'over' if spent > budget_amount else 'safe'
            })

        return {"budget_progress": progress, "count": len(progress)}
    except Exception as e:
        logger.error(f"Error fetching budget progress: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/investments")
async def create_investment(request: Request):
    """
    Create a new investment (stock purchase) from dashboard.
    """
    try:
        data = await request.json()
        sheets = get_sheets_handler()

        symbol = data.get('symbol', '').upper()
        shares = float(data.get('shares', 0))
        price = float(data.get('price', 0))
        account = data.get('account', '')
        purchase_date = data.get('date', datetime.now().strftime('%Y-%m-%d'))

        if not symbol or shares <= 0 or price <= 0:
            raise HTTPException(status_code=400, detail="Symbol, shares, and price are required")

        total_cost = shares * price

        # Create Asset transaction
        sheets.append_transaction(
            date=purchase_date,
            account=account,
            category='Investment',
            subcategory='Stocks',
            note=f"Buy {symbol}",
            amount=total_cost,
            transaction_type='Asset',
            status='Normal'
        )

        # Update investments sheet
        sheets.update_investment(
            symbol=symbol,
            shares_change=shares,
            price=price,
            account=account,
            purchase_date=purchase_date
        )

        return {
            "status": "success",
            "message": f"Added {shares} shares of {symbol}",
            "investment": {
                "symbol": symbol,
                "shares": shares,
                "price": price,
                "total_cost": total_cost
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating investment: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/transfers")
async def create_transfer(request: Request):
    """
    Create a transfer between accounts from dashboard.
    """
    try:
        data = await request.json()
        sheets = get_sheets_handler()

        from_account = data.get('from_account', '')
        to_account = data.get('to_account', '')
        amount = float(data.get('amount', 0))
        date = data.get('date', datetime.now().strftime('%Y-%m-%d'))

        if not from_account or not to_account or amount <= 0:
            raise HTTPException(status_code=400, detail="From account, to account, and amount are required")

        # Debit from source
        sheets.append_transaction(
            date=date,
            account=from_account,
            category='Transfer',
            subcategory='Internal Transfer',
            note=f"Transfer to {to_account}",
            amount=amount,
            transaction_type='Transfer',
            status='Normal'
        )

        # Credit to destination
        sheets.append_transaction(
            date=date,
            account=to_account,
            category='Transfer',
            subcategory='Internal Transfer',
            note=f"Transfer from {from_account}",
            amount=amount,
            transaction_type='Transfer',
            status='Normal'
        )

        return {
            "status": "success",
            "message": f"Transferred {amount} from {from_account} to {to_account}"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating transfer: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
