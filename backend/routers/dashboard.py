import logging
from fastapi import APIRouter, Request, HTTPException, Security, Depends
from dependencies import verify_api_key, limiter
from logic.gsheets_handler import get_sheets_handler
from services.cache import cache, summary_cache
from models.schemas import CategoriesResponse, AccountsResponse
import yfinance as yf
from typing import Dict

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["dashboard"])

@router.get("/transactions")
@limiter.limit("30/minute")
async def get_transactions(
    request: Request,
    year: int = None,
    month: int = None,
    api_key: str = Security(verify_api_key)
):
    """
    Get all transactions, optionally filtered by year and month.
    Rate limited to 30 requests per minute (Issue 3.2).
    Protected with API key authentication (Issue 3.3).
    """
    try:
        sheets = get_sheets_handler()
        transactions = sheets.get_transactions(year=year, month=month)
        return {"transactions": transactions, "count": len(transactions)}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching transactions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/investments")
@limiter.limit("100/minute")
async def get_investments(request: Request, api_key: str = Security(verify_api_key)):
    """
    Get all investment holdings.
    Rate limited to 30 requests per minute (Issue 3.2).
    Protected with API key authentication (Issue 3.3).
    """
    try:
        sheets = get_sheets_handler()
        investments = sheets.get_investments()
        return {"investments": investments, "count": len(investments)}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching investments: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/categories", response_model=CategoriesResponse)
async def get_categories(api_key: str = Security(verify_api_key)):
    """
    Get all categories and subcategories with caching (Issue 4.3).
    Protected with API key authentication (Issue 3.3).
    """
    try:
        # Check cache first
        if cached := cache.get("categories"):
            return CategoriesResponse(
                categories=cached,
                count=len(cached),
                cached=True
            )
        
        # Fetch from sheets
        sheets = get_sheets_handler()
        categories = sheets.get_categories()
        
        # Update cache
        cache.set("categories", categories)
        
        return CategoriesResponse(
            categories=categories,
            count=len(categories),
            cached=False
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching categories: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/accounts", response_model=AccountsResponse)
async def get_accounts(api_key: str = Security(verify_api_key)):
    """
    Get all accounts with caching (Issue 4.3).
    Protected with API key authentication (Issue 3.3).
    """
    try:
        # Check cache first
        if cached := cache.get("accounts"):
            return AccountsResponse(
                accounts=cached,
                count=len(cached),
                cached=True
            )
        
        # Fetch from sheets
        sheets = get_sheets_handler()
        accounts = sheets.get_accounts()
        
        # Update cache
        cache.set("accounts", accounts)
        
        return AccountsResponse(
            accounts=accounts,
            count=len(accounts),
            cached=False
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching accounts: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/budgets")
@limiter.limit("100/minute")
async def get_budgets(request: Request, api_key: str = Security(verify_api_key)):
    """
    Get all budget records.
    Rate limited to 30 requests per minute (Issue 3.2).
    Protected with API key authentication (Issue 3.3).
    """
    try:
        sheets = get_sheets_handler()
        budgets = sheets.get_budgets()
        return {"budgets": budgets, "count": len(budgets)}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching budgets: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/summary")
@limiter.limit("100/minute")
async def get_summary(
    request: Request,
    year: int = None,
    month: int = None,
    api_key: str = Security(verify_api_key)
):
    """
    Get financial summary stats for the dashboard.
    Rate limited to 30 requests per minute (Issue 3.2).
    Cached for 2 minutes to optimize performance (Issue 4.2).
    Protected with API key authentication (Issue 3.3).
    """
    try:
        # Generate cache key based on parameters
        cache_key = f"summary_{year}_{month}"
        
        # Check cache first (Issue 4.2)
        if cached := summary_cache.get(cache_key):
            cached["cached"] = True
            return cached
        
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

        result = {
            "total_income": total_income,
            "total_expense": total_expense,
            "total_savings": total_savings,
            "flagged_count": flagged_count,
            "transaction_count": len(transactions),
            "expense_by_category": expense_by_category,
            "income_by_category": income_by_category,
            "cached": False
        }
        
        # Update cache
        summary_cache.set(cache_key, result)
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/account-balances")
@limiter.limit("100/minute")
async def get_account_balances(request: Request, api_key: str = Security(verify_api_key)):
    """
    Get account balances from the Settings_Accounts sheet.
    Balance is calculated via Google Sheets formula for accuracy.
    Rate limited to 30 requests per minute (Issue 3.2).
    Protected with API key authentication (Issue 3.3).
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
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching account balances: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/daily-expenses")
@limiter.limit("100/minute")
async def get_daily_expenses(
    request: Request,
    year: int = None,
    month: int = None,
    api_key: str = Security(verify_api_key)
):
    """
    Get daily expense totals for the activity chart.
    Rate limited to 30 requests per minute (Issue 3.2).
    Protected with API key authentication (Issue 3.3).
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
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching daily expenses: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/budget-progress")
@limiter.limit("100/minute")
async def get_budget_progress(
    request: Request,
    year: int = None,
    month: int = None,
    api_key: str = Security(verify_api_key)
):
    """
    Get budget vs actual spending per category.
    Rate limited to 30 requests per minute (Issue 3.2).
    Cached for 2 minutes to optimize performance (Issue 4.2).
    Protected with API key authentication (Issue 3.3).
    """
    try:
        # Generate cache key based on parameters
        cache_key = f"budget_progress_{year}_{month}"
        
        # Check cache first (Issue 4.2)
        if cached := summary_cache.get(cache_key):
            cached["cached"] = True
            return cached
        
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

        result = {"budget_progress": progress, "count": len(progress), "cached": False}
        
        # Update cache
        summary_cache.set(cache_key, result)
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching budget progress: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/market-data")
@limiter.limit("20/minute")
async def get_market_data(
    request: Request,
    symbols: str,
    api_key: str = Security(verify_api_key)
):
    """
    Get real-time market data for stock symbols using yfinance.
    Rate limited to 20 requests per minute to avoid API abuse.
    Protected with API key authentication (Issue 3.3).

    Args:
        symbols: Comma-separated list of stock symbols (e.g., "AAPL,GOOGL,MSFT")

    Returns:
        Dictionary with symbol as key and market data as value
    """
    try:
        if not symbols:
            raise HTTPException(status_code=400, detail="symbols parameter is required")

        # Parse symbols
        symbol_list = [s.strip().upper() for s in symbols.split(',')]

        if len(symbol_list) > 20:
            raise HTTPException(status_code=400, detail="Maximum 20 symbols allowed per request")

        # Check cache first (5 minute TTL)
        cache_key = f"market_data_{symbols}"
        if cached := summary_cache.get(cache_key):
            logger.info(f"Returning cached market data for {len(symbol_list)} symbols")
            return {"market_data": cached, "cached": True}

        # Fetch market data
        market_data = {}

        for symbol in symbol_list:
            try:
                ticker = yf.Ticker(symbol)
                info = ticker.info
                history = ticker.history(period="1d")

                if history.empty:
                    logger.warning(f"No data available for {symbol}")
                    continue

                current_price = history['Close'].iloc[-1]
                open_price = history['Open'].iloc[-1]
                change_percent = ((current_price - open_price) / open_price * 100) if open_price > 0 else 0

                market_data[symbol] = {
                    "symbol": symbol,
                    "current_price": round(float(current_price), 2),
                    "change_percent": round(float(change_percent), 2),
                    "currency": info.get("currency", "USD")
                }

                logger.info(f"Fetched market data for {symbol}: ${current_price:.2f}")

            except Exception as e:
                logger.error(f"Error fetching data for {symbol}: {e}")
                # Continue with other symbols even if one fails
                continue

        # Cache the result for 5 minutes
        summary_cache.set(cache_key, market_data, ttl=300)

        return {"market_data": market_data, "cached": False, "count": len(market_data)}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching market data: {e}")
        raise HTTPException(status_code=500, detail=str(e))
