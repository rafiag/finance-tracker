"""
Telegram Utilities for Finance Tracker
Handles all Telegram Bot API interactions
"""

import os
from typing import Optional
import httpx


class TelegramHandler:
    """Handles all Telegram Bot API operations."""
    
    BASE_URL = "https://api.telegram.org/bot{token}"
    
    def __init__(self):
        """Initialize the Telegram handler."""
        self.bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.authorized_chat_id = os.getenv('MY_TELEGRAM_CHAT_ID')
        
        if not self.bot_token:
            raise ValueError("TELEGRAM_BOT_TOKEN environment variable is not set")
        if not self.authorized_chat_id:
            raise ValueError("MY_TELEGRAM_CHAT_ID environment variable is not set")
        
        self.api_url = self.BASE_URL.format(token=self.bot_token)
    
    def is_authorized(self, chat_id: int | str) -> bool:
        """
        Check if a message is from the authorized user.
        
        Args:
            chat_id: The chat ID from the incoming message
            
        Returns:
            True if authorized, False otherwise
        """
        return str(chat_id) == str(self.authorized_chat_id)
    
    async def send_message(
        self,
        text: str,
        chat_id: Optional[str] = None,
        parse_mode: str = "HTML"
    ) -> bool:
        """
        Send a text message to Telegram.
        
        Args:
            text: Message text to send
            chat_id: Target chat ID (defaults to authorized user)
            parse_mode: Telegram parse mode ('HTML' or 'Markdown')
            
        Returns:
            True if successful, False otherwise
        """
        if chat_id is None:
            chat_id = self.authorized_chat_id
        
        url = f"{self.api_url}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": parse_mode
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload)
            return response.status_code == 200
    
    async def send_confirmation(
        self,
        amount: float,
        category: str,
        subcategory: str,
        account: str,
        is_flagged: bool = False,
        investment_symbol: Optional[str] = None,
        shares: Optional[float] = None,
        price_per_share: Optional[float] = None,
        currency: str = "IDR",
        flag_reason: Optional[str] = None,
        source_account: Optional[str] = None
    ) -> bool:
        """
        Send a transaction confirmation message.
        """
        # Format amount based on currency
        if currency == "USD":
            formatted_amount = f"${amount:,.2f}"
            price_formatted = f"${price_per_share:,.2f}" if price_per_share else ""
        else:
            formatted_amount = f"Rp {amount:,.0f}".replace(",", ".")
            price_formatted = f"Rp {price_per_share:,.0f}".replace(",", ".") if price_per_share else ""

        if investment_symbol and shares and price_per_share:
            # Trade confirmation
            type_label = "Trade"
            # Format shares - show decimals only if needed (for fractional shares in USD)
            if shares == int(shares):
                shares_str = str(int(shares))
            else:
                shares_str = f"{shares:.4f}".rstrip('0').rstrip('.')
            detail_line = f"📈 {investment_symbol}: {shares_str} @ {price_formatted}"

            # Show money flow for stock purchases
            if source_account:
                flow_line = f"💸 {source_account} → {account}"
            else:
                flow_line = f"💳 {account}"

            if is_flagged:
                message = (
                    f"⚠️ <b>{type_label} saved (needs review)</b>\n\n"
                    f"💰 {formatted_amount}\n"
                    f"{detail_line}\n"
                    f"📁 {category} → {subcategory}\n"
                    f"{flow_line}\n\n"
                    f"<i>This transaction was flagged for review.</i>\n"
                    f"<i>Reason: {flag_reason if flag_reason else 'Unspecified check required'}</i>"
                )
            else:
                message = (
                    f"✅ <b>{type_label} saved</b>\n\n"
                    f"💰 {formatted_amount}\n"
                    f"{detail_line}\n"
                    f"📁 {category} → {subcategory}\n"
                    f"{flow_line}"
                )
        else:
            # Regular transaction
            if is_flagged:
                message = (
                    f"⚠️ <b>Transaction saved (needs review)</b>\n\n"
                    f"💰 {formatted_amount}\n"
                    f"📁 {category} → {subcategory}\n"
                    f"💳 {account}\n\n"
                    f"<i>This transaction was flagged for review.</i>\n"
                    f"<i>Reason: {flag_reason if flag_reason else 'Unspecified check required'}</i>"
                )
            else:
                message = (
                    f"✅ <b>Transaction saved</b>\n\n"
                    f"💰 {formatted_amount}\n"
                    f"📁 {category} → {subcategory}\n"
                    f"💳 {account}"
                )
        
        return await self.send_message(message)
    
    async def send_error(self, error_description: str) -> bool:
        """
        Send an error notification.
        
        Args:
            error_description: Brief description of the error
            
        Returns:
            True if successful
        """
        message = f"⚠️ <b>Finance Tracker Error</b>\n\n{error_description}"
        return await self.send_message(message)
    
    async def download_file(self, file_id: str) -> tuple[bytes, str]:
        """
        Download a file from Telegram (e.g., photos).
        
        Args:
            file_id: Telegram file ID
            
        Returns:
            Tuple of (file_bytes, mime_type)
        """
        # First, get the file path from Telegram
        url = f"{self.api_url}/getFile"
        params = {"file_id": file_id}
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            result = response.json()
            
            file_path = result["result"]["file_path"]
            
            # Download the actual file
            download_url = f"https://api.telegram.org/file/bot{self.bot_token}/{file_path}"
            file_response = await client.get(download_url)
            file_response.raise_for_status()
            
            # Determine MIME type from file path
            if file_path.endswith('.jpg') or file_path.endswith('.jpeg'):
                mime_type = 'image/jpeg'
            elif file_path.endswith('.png'):
                mime_type = 'image/png'
            elif file_path.endswith('.webp'):
                mime_type = 'image/webp'
            else:
                mime_type = 'image/jpeg'  # Default
            
            return file_response.content, mime_type
    
    def extract_message_data(self, update: dict) -> dict:
        """
        Extract relevant data from a Telegram update.
        
        Args:
            update: Telegram update object (webhook payload)
            
        Returns:
            Dict with: chat_id, text, photo_file_id, has_photo
        """
        message = update.get('message', {})
        
        # Handle caption for photos (text sent with image)
        text = message.get('text') or message.get('caption')
        
        # Get the largest photo if present (Telegram sends multiple sizes)
        photo_file_id = None
        photos = message.get('photo', [])
        if photos:
            # Photos are sorted by size, get the largest
            photo_file_id = photos[-1].get('file_id')
        
        return {
            'chat_id': message.get('chat', {}).get('id'),
            'text': text,
            'photo_file_id': photo_file_id,
            'has_photo': photo_file_id is not None,
            'message_id': message.get('message_id'),
            'date': message.get('date')
        }


# Singleton instance
_handler: Optional[TelegramHandler] = None


def get_telegram_handler() -> TelegramHandler:
    """Get the singleton TelegramHandler instance."""
    global _handler
    if _handler is None:
        _handler = TelegramHandler()
    return _handler
