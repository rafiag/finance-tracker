"""
AI Processor for Finance Tracker
Uses Gemini AI to extract transaction details from messages and images
"""

import os
import json
import asyncio
import logging
from datetime import datetime
from typing import Optional, List, Union
from dataclasses import dataclass

from google import genai
from google.genai import types

logger = logging.getLogger(__name__)


@dataclass
class TransactionData:
    """Structured transaction data extracted by AI."""
    amount: float
    category: str
    subcategory: str
    account: str
    note: str
    transaction_type: str  # 'Expense', 'Income', 'Transfer', 'Trade_Buy', 'Trade_Sell'
    is_flagged: bool
    flag_reason: Optional[str] = None
    confidence: float = 1.0
    investment_symbol: Optional[str] = None
    shares: Optional[float] = None
    price_per_share: Optional[float] = None
    # For transfers: destination account
    destination_account: Optional[str] = None
    # Currency for investments (USD or IDR)
    currency: str = "IDR"
    # For Trade_Buy: source bank account (where money comes from before going to RDN)
    source_account: Optional[str] = None


class AIProcessor:
    """Processes messages and images using Gemini AI to extract transaction data."""
    
    def __init__(self):
        """Initialize the AI processor with Gemini API key."""
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable is not set")
        
        # Initialize the new Google GenAI Client
        self.client = genai.Client(api_key=api_key)
        self.models = [
            'gemini-3-flash',          # Main
            'gemini-2.5-flash',        # 1st Fallback
            'gemini-2.5-flash-lite'    # 2nd Fallback
        ]
    
    def _build_prompt(
        self,
        user_message: Optional[str],
        categories_context: str,
        accounts_context: str,
        current_investments: str,
        current_date: str
    ) -> str:
        """Build the prompt for Gemini AI."""
        
        prompt = f"""You are a financial transaction parser for an Indonesian user.
Extract transaction details from the user's message and/or image (if provided).

CURRENT DATE: {current_date}

VALID CATEGORIES:
{categories_context}

VALID ACCOUNTS:
{accounts_context}

CURRENT PORTFOLIO:
{current_investments}

RULES:
1. Amount: Parse Indonesian Rupiah formats (20k=20,000, 1.5jt=1,500,000, etc.) or USD formats ($100, 100 USD).
2. Category/Subcategory: Use only from the provided list.
3. Account (CRITICAL): You MUST only use account names from the VALID ACCOUNTS list above. Never invent or guess account names.
   - If the user mentions an account not in the list, flag the transaction and use the closest match.
   - If no account is mentioned, use a sensible default from the list based on transaction type.
4. Transaction Type:
   - "Expense", "Income" for regular transactions.
   - "Transfer" for money movement between accounts (e.g., "transfer 500k from BCA to Jago").
   - "Trade_Buy" when adding to an investment (e.g., "Buy 1000 ARCI at 350").
   - "Trade_Sell" when selling an investment (e.g., "Sell 500 ARCI at 400").
5. Note: Include relevant details (ticker symbol, store name, etc.).
6. Investment Details: If it's a trade, extract the Symbol, Shares, and Price per share.
7. Transfer Details: For transfers, "account" is the SOURCE, "destination_account" is the TARGET. Both must be from VALID ACCOUNTS.
8. Trade_Buy Account Flow (IMPORTANT):
   - "account" = the RDN/investment account where the stock will be held. Must be from VALID ACCOUNTS.
   - "source_account" = the bank account where money comes from. Must be from VALID ACCOUNTS or null.
   - If user says "buy BBCA using BCA", then account should be the appropriate investment account from VALID ACCOUNTS and source_account="BCA".
   - If investment account is not clear, set account to null (system will assign based on currency).
   - If source_account is not mentioned, set it to null (system will handle it).
9. Currency Detection (IMPORTANT for Trade_Buy/Trade_Sell):
   - Detect currency from the image or message context.
   - Indonesian stocks (e.g., BBCA, ARCI, TLKM, BMRI) use "IDR".
   - US/International stocks (e.g., AAPL, GOOGL, TSM, MSFT, NVDA) use "USD".
   - Look for currency symbols ($, Rp), app interface language, or broker name.
   - Common Indonesian brokers: Stockbit, Ajaib, IPOT, Mandiri Sekuritas, BCA Sekuritas.
   - Common US brokers: Pluang, Robinhood, Interactive Brokers, TD Ameritrade, Charles Schwab, Gotrade.
   - Default to "IDR" if unclear.
10. Flag transactions when uncertain or data is messy.

USER MESSAGE: {user_message if user_message else "(No text message, only image)"}

Respond ONLY with valid JSON in this exact format:
{{
    "amount": 400000,
    "category": "Investment",
    "subcategory": "Stocks",
    "account": "RDN Wallet - Jago",
    "destination_account": null,
    "source_account": null,
    "note": "Sell 1000 ARCI",
    "transaction_type": "Trade_Sell",
    "investment_symbol": "ARCI",
    "shares": 1000,
    "price_per_share": 400,
    "currency": "IDR",
    "is_flagged": false,
    "flag_reason": null,
    "confidence": 0.95
}}

For Trade_Buy with source account:
{{
    "amount": 900000,
    "category": "Investment",
    "subcategory": "Stocks",
    "account": "RDN Wallet - Jago",
    "destination_account": null,
    "source_account": "BCA",
    "note": "Buy 100 BBCA",
    "transaction_type": "Trade_Buy",
    "investment_symbol": "BBCA",
    "shares": 100,
    "price_per_share": 9000,
    "currency": "IDR",
    "is_flagged": false,
    "flag_reason": null,
    "confidence": 0.95
}}
"""
        return prompt
    
    def _parse_float(self, value: Union[str, float, int, None]) -> Optional[float]:
        """Safely parse a float value from potential strings."""
        if value is None:
            return None
        if isinstance(value, (int, float)):
            return float(value)
        try:
            # Handle "20k", "1.5jt" (Indonesian specific)
            s = str(value).lower().replace(',', '').replace('$', '').replace('rp', '').strip()
            if 'k' in s:
                return float(s.replace('k', '')) * 1000
            if 'jt' in s:
                return float(s.replace('jt', '')) * 1000000
            return float(s)
        except ValueError:
            return None

    async def process_transaction(
        self,
        user_message: Optional[str] = None,
        image_data: Optional[bytes] = None,
        image_mime_type: str = "image/jpeg",
        categories_context: str = "",
        accounts_context: str = "",
        current_investments: str = "",
        current_date: Optional[str] = None
    ) -> TransactionData:
        """
        Process a transaction message and/or image.
        
        Args:
            user_message: Text message from user (optional if image provided)
            image_data: Image bytes (optional if message provided)
            image_mime_type: MIME type of the image
            categories_context: Formatted string of valid categories
            accounts_context: Formatted string of valid accounts
            current_date: Current date string (defaults to today)
            
        Returns:
            TransactionData with extracted transaction details
        """
        if not user_message and not image_data:
            raise ValueError("Either user_message or image_data must be provided")
        
        if current_date is None:
            current_date = datetime.now().strftime("%Y-%m-%d %H:%M")
        
        prompt = self._build_prompt(
            user_message=user_message,
            categories_context=categories_context,
            accounts_context=accounts_context,
            current_investments=current_investments,
            current_date=current_date
        )
        
        # Build contents for new SDK
        contents = []
        
        # Add text prompt
        contents.append(types.Content(
            role="user",
            parts=[types.Part.from_text(text=prompt)]
        ))
        
        if image_data:
            # Add image to the request
            # New SDK handles it via Part.from_bytes
            contents[0].parts.append(
                types.Part.from_bytes(data=image_data, mime_type=image_mime_type)
            )
        
        # Generate response from Gemini with fallback model support
        models_to_try = self.models
        response = None
        last_error = None

        for model_name in models_to_try:
            max_retries = 2
            retry_delay = 2  # Start with 2 seconds

            for attempt in range(max_retries):
                try:
                    logger.info(f"Trying model: {model_name} (attempt {attempt + 1}/{max_retries})")
                    response = self.client.models.generate_content(
                        model=model_name,
                        contents=contents
                    )
                    logger.info(f"Successfully generated response with {model_name}")
                    break  # Success, exit retry loop
                except Exception as e:
                    last_error = e
                    error_str = str(e).lower()
                    if '429' in str(e) or 'quota' in error_str or 'rate' in error_str or 'resource_exhausted' in error_str:
                        if attempt < max_retries - 1:
                            logger.warning(f"Rate limited on {model_name}, retrying in {retry_delay}s")
                            await asyncio.sleep(retry_delay)
                            retry_delay *= 2  # Exponential backoff
                        else:
                            logger.warning(f"Rate limit exceeded on {model_name}, trying fallback model")
                            break  # Exit retry loop, try next model
                    else:
                        logger.error(f"Non-rate-limit error on {model_name}: {e}")
                        break  # Exit retry loop, try next model

            if response is not None:
                break  # Successfully got a response, exit model loop

        if response is None:
            logger.error(f"All models failed. Last error: {last_error}")
            raise last_error or Exception("Failed to generate response from any model")
        
        # Parse the JSON response
        try:
            # Extract JSON from response text (handle potential markdown code blocks)
            # New SDK: response.text is directly accessible
            response_text = response.text.strip()
            if response_text.startswith('```'):
                # Remove markdown code block formatting
                lines = response_text.split('\n')
                # Check if first line is ```json
                if lines[0].startswith('```'):
                     lines = lines[1:]
                # Check if last line is ```
                if lines[-1].startswith('```'):
                    lines = lines[:-1]
                response_text = '\n'.join(lines)
            
            data = json.loads(response_text)
            
            amount_val = self._parse_float(data.get('amount')) or 0.0
            shares_val = self._parse_float(data.get('shares'))
            price_val = self._parse_float(data.get('price_per_share'))
            
            return TransactionData(
                amount=amount_val,
                category=data.get('category', 'Miscellaneous'),
                subcategory=data.get('subcategory', 'Other'),
                account=data.get('account', 'Wallet'),
                note=data.get('note', ''),
                transaction_type=data.get('transaction_type', 'Expense'),
                is_flagged=data.get('is_flagged', False),
                flag_reason=data.get('flag_reason'),
                confidence=float(data.get('confidence', 0.5)),
                investment_symbol=data.get('investment_symbol'),
                shares=shares_val,
                price_per_share=price_val,
                destination_account=data.get('destination_account'),
                currency=data.get('currency', 'IDR'),
                source_account=data.get('source_account')
            )
            
        except (json.JSONDecodeError, Exception) as e:
            logger.error(f"AI parsing error: {e}")
            return TransactionData(
                amount=0,
                category='Miscellaneous',
                subcategory='Other',
                account='Wallet',
                note=f"Failed to parse extraction",
                transaction_type='Expense',
                is_flagged=True,
                flag_reason=f"AI response parsing error: {str(e)}",
                confidence=0.0
            )


# Singleton instance
_processor: Optional[AIProcessor] = None


def get_ai_processor() -> AIProcessor:
    """Get the singleton AIProcessor instance."""
    global _processor
    if _processor is None:
        _processor = AIProcessor()
    return _processor
