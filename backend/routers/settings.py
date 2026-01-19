import logging
from datetime import datetime, timedelta
from fastapi import APIRouter, Request, HTTPException, Security
from dependencies import verify_api_key, limiter
from logic.gsheets_handler import get_sheets_handler
from services.cache import cache
from pydantic import BaseModel
from typing import Optional

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["settings"])


# =============================================================================
# Pydantic Models
# =============================================================================

class AccountCreate(BaseModel):
    name: str
    type: str
    currency: str = 'IDR'


class AccountUpdate(BaseModel):
    new_name: Optional[str] = None
    type: Optional[str] = None
    balance: Optional[float] = None


class CategoryCreate(BaseModel):
    category: str
    type: str
    subcategory: Optional[str] = ''


class CategoryUpdate(BaseModel):
    new_category: Optional[str] = None
    new_subcategory: Optional[str] = None


class BudgetUpdate(BaseModel):
    category: str
    monthly_budget: float
    effective_from: Optional[str] = None


# =============================================================================
# Accounts Endpoints
# =============================================================================

@router.post("/accounts")
@limiter.limit("10/minute")
async def create_account(
    request: Request,
    account: AccountCreate,
    api_key: str = Security(verify_api_key)
):
    """Create a new account."""
    try:
        sheets = get_sheets_handler()
        sheets.add_account(account.name, account.type, account.currency)

        # Clear accounts cache
        cache.delete("accounts")

        return {"status": "success", "message": f"Account '{account.name}' created"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating account: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/accounts/{account_name}")
@limiter.limit("10/minute")
async def update_account(
    request: Request,
    account_name: str,
    updates: AccountUpdate,
    api_key: str = Security(verify_api_key)
):
    """Update an account."""
    try:
        sheets = get_sheets_handler()

        # Get account type to check if it's investment account
        accounts = sheets.get_accounts()
        account_data = next((acc for acc in accounts if acc['name'] == account_name), None)

        if not account_data:
            raise HTTPException(status_code=404, detail=f"Account '{account_name}' not found")

        # Prevent balance editing for investment accounts
        if updates.balance is not None and account_data['type'] == 'Investment':
            raise HTTPException(
                status_code=400,
                detail="Cannot manually adjust balance for investment accounts"
            )

        result = sheets.update_account(
            old_name=account_name,
            new_name=updates.new_name,
            account_type=updates.type,
            balance=updates.balance
        )

        # If balance was adjusted, create adjustment transaction
        if result['adjustment_amount'] is not None:
            adjustment_amount = result['adjustment_amount']
            account_for_transaction = updates.new_name if result['renamed'] else account_name

            # Determine transaction type based on positive or negative adjustment
            if adjustment_amount > 0:
                trans_type = 'Income'
                category = 'Adjustment'
            else:
                trans_type = 'Expense'
                category = 'Adjustment'
                adjustment_amount = abs(adjustment_amount)

            # Ensure Adjustment category exists
            existing_categories = sheets.get_categories()
            if not any(cat['category'] == 'Adjustment' and cat['type'] == trans_type for cat in existing_categories):
                sheets.add_category('Adjustment', trans_type, '')

            # Create adjustment transaction
            sheets.append_transaction(
                date=datetime.now().strftime('%Y-%m-%d'),
                account=account_for_transaction,
                category='Adjustment',
                subcategory='',
                note=f"Balance adjustment for {account_for_transaction}",
                amount=adjustment_amount,
                transaction_type=trans_type,
                status='Normal'
            )

        # Clear caches
        cache.delete("accounts")

        return {
            "status": "success",
            "message": f"Account updated successfully",
            "balance_adjusted": result['adjustment_amount'] is not None,
            "adjustment_amount": result['adjustment_amount']
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating account: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/accounts/{account_name}")
@limiter.limit("10/minute")
async def delete_account(
    request: Request,
    account_name: str,
    api_key: str = Security(verify_api_key)
):
    """Delete an account and reassign its transactions to 'Uncategorized'."""
    try:
        sheets = get_sheets_handler()
        sheets.delete_account(account_name)

        # Clear cache
        cache.delete("accounts")

        return {
            "status": "success",
            "message": f"Account '{account_name}' deleted. Transactions reassigned to 'Uncategorized'."
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error deleting account: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# Categories Endpoints
# =============================================================================

@router.post("/categories")
@limiter.limit("10/minute")
async def create_category(
    request: Request,
    category: CategoryCreate,
    api_key: str = Security(verify_api_key)
):
    """Create a new category or subcategory."""
    try:
        sheets = get_sheets_handler()
        sheets.add_category(category.category, category.type, category.subcategory or '')

        # Clear cache
        cache.delete("categories")

        return {
            "status": "success",
            "message": f"Category '{category.category}' created"
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating category: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/categories/{category_name}")
@limiter.limit("10/minute")
async def update_category(
    request: Request,
    category_name: str,
    subcategory_name: str = '',
    updates: CategoryUpdate = None,
    api_key: str = Security(verify_api_key)
):
    """Update a category or subcategory name."""
    try:
        sheets = get_sheets_handler()
        sheets.update_category(
            old_category=category_name,
            old_subcategory=subcategory_name,
            new_category=updates.new_category,
            new_subcategory=updates.new_subcategory
        )

        # Clear cache
        cache.delete("categories")

        return {"status": "success", "message": "Category updated successfully"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating category: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/categories/{category_name}")
@limiter.limit("10/minute")
async def delete_category(
    request: Request,
    category_name: str,
    subcategory_name: str = '',
    api_key: str = Security(verify_api_key)
):
    """Delete a category/subcategory and reassign its transactions to 'Uncategorized'."""
    try:
        sheets = get_sheets_handler()
        sheets.delete_category(category_name, subcategory_name)

        # Clear cache
        cache.delete("categories")

        return {
            "status": "success",
            "message": f"Category '{category_name}' deleted. Transactions reassigned to 'Uncategorized'."
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error deleting category: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# Budgets Endpoints
# =============================================================================

@router.put("/budgets")
@limiter.limit("10/minute")
async def update_budgets(
    request: Request,
    budgets: list[BudgetUpdate],
    api_key: str = Security(verify_api_key)
):
    """Update multiple budgets at once."""
    try:
        sheets = get_sheets_handler()

        # Calculate next month's date
        next_month = datetime.now() + timedelta(days=32)
        next_month = next_month.replace(day=1)
        default_effective_from = next_month.strftime('%Y-%m-%d')

        updated_count = 0
        for budget in budgets:
            effective_from = budget.effective_from or default_effective_from
            sheets.update_budget(budget.category, budget.monthly_budget, effective_from)
            updated_count += 1

        return {
            "status": "success",
            "message": f"Updated {updated_count} budget(s)",
            "count": updated_count
        }
    except Exception as e:
        logger.error(f"Error updating budgets: {e}")
        raise HTTPException(status_code=500, detail=str(e))
