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
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from logic.gsheets_handler import get_sheets_handler
from logic.ai_processor import get_ai_processor
from logic.telegram_utils import get_telegram_handler

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
                price_per_share=transaction.get('price_per_share')
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
    
    # --- Investment Orchestration ---
    if transaction_data.transaction_type == "Trade_Buy":
        total_cost = transaction_data.amount
        # Log as Asset acquisition
        sheets.append_transaction(
            date=current_date, account=transaction_data.account,
            category=transaction_data.category, subcategory=transaction_data.subcategory,
            note=f"Buy {transaction_data.investment_symbol}", amount=total_cost,
            transaction_type="Asset", status=status
        )
        # Update Portfolio
        sheets.update_investment(
            symbol=transaction_data.investment_symbol,
            shares_change=transaction_data.shares,
            price=transaction_data.price_per_share
        )
    
    elif transaction_data.transaction_type == "Trade_Sell":
        # Find avg price to calculate split
        portfolio = sheets.get_investments()
        inv = next((i for i in portfolio if i['symbol'] == transaction_data.investment_symbol), None)
        
        avg_buy_price = inv['avg_price'] if inv else transaction_data.price_per_share
        base_cost = transaction_data.shares * avg_buy_price
        capital_gain = transaction_data.amount - base_cost
        
        # 1. Log Return of Capital (Asset)
        sheets.append_transaction(
            date=current_date, account=transaction_data.account,
            category=transaction_data.category, subcategory=transaction_data.subcategory,
            note=f"Sell {transaction_data.investment_symbol} (Return of Capital)",
            amount=base_cost, transaction_type="Asset", status=status
        )
        # 2. Log Capital Gain (Income)
        sheets.append_transaction(
            date=current_date, account=transaction_data.account,
            category="Income", subcategory="Capital Gains",
            note=f"Sell {transaction_data.investment_symbol} (Gain)",
            amount=capital_gain, transaction_type="Income", status=status
        )
        # Update Portfolio
        sheets.update_investment(
            symbol=transaction_data.investment_symbol,
            shares_change=-transaction_data.shares,
            price=transaction_data.price_per_share,
            realized_pl=capital_gain
        )
    
    else:
        # Regular transaction (Expense, Income, Transfer)
        sheets.append_transaction(
            date=current_date,
            account=transaction_data.account,
            category=transaction_data.category,
            subcategory=transaction_data.subcategory,
            note=transaction_data.note or text,
            amount=transaction_data.amount,
            transaction_type=transaction_data.transaction_type,
            status=status
        )
    
    return {
        "amount": transaction_data.amount,
        "category": transaction_data.category,
        "subcategory": transaction_data.subcategory,
        "account": transaction_data.account,
        "note": transaction_data.note,
        "transaction_type": transaction_data.transaction_type,
        "is_flagged": transaction_data.is_flagged,
        "investment_symbol": transaction_data.investment_symbol,
        "shares": transaction_data.shares,
        "price_per_share": transaction_data.price_per_share
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


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
