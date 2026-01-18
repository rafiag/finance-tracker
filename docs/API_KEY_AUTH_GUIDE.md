# API Key Authentication Setup Guide

## Overview
As of 2026-01-18, all dashboard API endpoints (`/api/*`) are now protected with API key authentication using the `X-API-Key` header.

## Quick Start

### 1. Generate an API Key

**Using OpenSSL (recommended):**
```bash
openssl rand -hex 32
```

**Using Python:**
```python
import secrets
print(secrets.token_hex(32))
```

**Example output:**
```
a7f3e9d2c8b1456789abcdef01234567890abcdef1234567890abcdef123456
```

### 2. Set Environment Variable

**Local Development (.env file):**
```bash
DASHBOARD_API_KEY=a7f3e9d2c8b1456789abcdef01234567890abcdef1234567890abcdef123456
```

**Docker Compose (docker-compose.yml):**
```yaml
backend:
  environment:
    - DASHBOARD_API_KEY=a7f3e9d2c8b1456789abcdef01234567890abcdef1234567890abcdef123456
```

**Railway/Production:**
Add `DASHBOARD_API_KEY` as an environment variable in your deployment settings.

### 3. Use in Frontend/API Calls

**JavaScript/Fetch:**
```javascript
fetch('http://localhost:8000/api/transactions', {
  headers: {
    'X-API-Key': 'a7f3e9d2c8b1456789abcdef01234567890abcdef1234567890abcdef123456'
  }
})
```

**Axios:**
```javascript
axios.get('http://localhost:8000/api/transactions', {
  headers: {
    'X-API-Key': 'a7f3e9d2c8b1456789abcdef01234567890abcdef1234567890abcdef123456'
  }
})
```

**cURL:**
```bash
curl -H "X-API-Key: a7f3e9d2c8b1456789abcdef01234567890abcdef1234567890abcdef123456" \
  http://localhost:8000/api/transactions
```

**Python Requests:**
```python
import requests

headers = {
    'X-API-Key': 'a7f3e9d2c8b1456789abcdef01234567890abcdef1234567890abcdef123456'
}

response = requests.get('http://localhost:8000/api/transactions', headers=headers)
```

## Protected Endpoints

All of the following endpoints now require the `X-API-Key` header:

### GET Endpoints
- `/api/transactions` - Get all transactions
- `/api/investments` - Get investment holdings
- `/api/categories` - Get categories and subcategories
- `/api/accounts` - Get accounts
- `/api/budgets` - Get budgets
- `/api/summary` - Get financial summary
- `/api/account-balances` - Get account balances
- `/api/daily-expenses` - Get daily expense data
- `/api/budget-progress` - Get budget progress

### POST Endpoints
- `/api/transactions` - Create transaction
- `/api/investments` - Create investment
- `/api/transfers` - Create transfer

### PUT Endpoints
- `/api/transactions/{row_index}` - Update transaction

### DELETE Endpoints
- `/api/transactions/{row_index}` - Delete transaction

## Error Responses

### 401 Unauthorized - Missing API Key
```json
{
  "detail": "Missing API key. Please provide X-API-Key header."
}
```

### 403 Forbidden - Invalid API Key
```json
{
  "detail": "Invalid API key"
}
```

## Backward Compatibility

If `DASHBOARD_API_KEY` environment variable is **not set**, the API will:
1. Log a warning message
2. Allow all requests through (unprotected mode)

This ensures backward compatibility for existing deployments.

**⚠️ Warning:** For production deployments, always set `DASHBOARD_API_KEY` to enable protection.

## Security Best Practices

1. **Generate Strong Keys**: Use at least 32 bytes of randomness
2. **Keep Keys Secret**: Never commit API keys to version control
3. **Use HTTPS**: Always use HTTPS in production to prevent key interception
4. **Rotate Keys**: Change API keys periodically
5. **Different Keys Per Environment**: Use different keys for dev/staging/production

## Frontend Integration Example

For Next.js frontend, store the API key in `.env.local`:

```bash
# .env.local
NEXT_PUBLIC_API_KEY=a7f3e9d2c8b1456789abcdef01234567890abcdef1234567890abcdef123456
```

Create an API client:

```javascript
// lib/api.js
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
const API_KEY = process.env.NEXT_PUBLIC_API_KEY;

export async function fetchAPI(endpoint, options = {}) {
  const headers = {
    'Content-Type': 'application/json',
    'X-API-Key': API_KEY,
    ...options.headers,
  };

  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    ...options,
    headers,
  });

  if (!response.ok) {
    throw new Error(`API error: ${response.status}`);
  }

  return response.json();
}

// Usage
const transactions = await fetchAPI('/api/transactions');
```

## Testing

Test the authentication using curl:

```bash
# Should fail with 401
curl http://localhost:8000/api/transactions

# Should succeed
curl -H "X-API-Key: your-key-here" http://localhost:8000/api/transactions
```

## Future Enhancements

This simple API key implementation can be upgraded to:
- **JWT Authentication** for multi-user support
- **OAuth 2.0** (Google) for social login
- **NextAuth.js integration** for session-based auth

See `docs/BACKEND_CODE_REVIEW.md` issue 3.3 for detailed implementation options.
