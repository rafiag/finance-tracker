import logging
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import JSONResponse
from dependencies import limiter
from logic.telegram_utils import get_telegram_handler
from services.transaction_service import process_transaction

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/webhook/telegram")
@limiter.limit("5/minute")  # Aligned with Gemini API free tier (gemini-3-flash, gemini-2.5-flash: 5 RPM)
async def telegram_webhook(request: Request):
    """
    Handle incoming Telegram webhook updates.
    This is the main entry point for processing transactions.
    Rate limited to 5 requests/minute to align with Google AI Studio free tier limits.
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
                flag_reason=transaction.get('flag_reason'),
                source_account=transaction.get('source_account')
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


@router.post("/test/transaction")
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
