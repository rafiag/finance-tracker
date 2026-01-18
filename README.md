# Personal Finance Tracker

A simple way to track your spending using Telegram. Just send a message about what you bought, and the system handles the rest.

## What It Does

**The Problem:** Manually logging expenses into finance apps takes forever (30+ minutes per week) and usually happens days after the fact when you're trying to remember what you spent.

**The Solution:** Send a quick Telegram message whenever you spend money. The system automatically figures out the amount, category, and saves it for you.

## How It Works

### Logging Transactions

Send a message to your Telegram bot in any of these ways:

- **Text only:** `coffee 20k`
- **Photo only:** Take a picture of your receipt
- **Both:** Send a receipt photo with a caption like `lunch 45k`

You'll get an instant confirmation that your transaction was saved.

### Viewing Your Finances

Open the dashboard to see:

- **Overview:** Total assets, income, and expenses for the month
- **Budget Status:** How much you've spent in each category vs. your limits
- **Transaction List:** Everything you've logged, with the ability to edit or delete

### Smart Features

- **Automatic Categorization:** The system figures out whether that coffee belongs under "Food & Drink" or "Entertainment"
- **Account Detection:** If your receipt shows which card/wallet you used, it picks that up automatically
- **Review Flags:** When something's unclear (like which category fits best), it flags the transaction for you to review later instead of guessing wrong

## Dashboard

The dashboard is designed for deep financial insight and monthly reviews:

- **Next.js Power**: A premium, responsive web app with a stunning dark theme.
- **Visual Analytics**: Interactive charts showing spending patterns, asset growth, and budget tracking.
- **Budget Status**: Visual indicators (Safe vs Over Budget) for category spending.
- **Stock Tracking**: Real-time portfolio valuation using market data services.
- **Review Queue**: Verify transactions that the AI wasn't 100% sure about.
- **Management**: A full settings page to manage your categories, accounts, and budget goals.

Works beautifully on desktop for deep reviews, but also fully responsive for checking your status on the go.

## Your Data

- All your financial data is stored in a Google Sheet that only you can access
- The dashboard requires authentication - only you can see your information
- You can download or backup your data anytime directly from Google Sheets

## Getting Started

1. Set up your Telegram bot
2. Connect it to your Google Sheet
3. Configure your categories, accounts, and budgets
4. Start logging transactions!

Detailed setup instructions are provided separately.

---

*Built for personal use - a single-user system designed to make expense tracking effortless.*
