# Ledger — Development Roadmap

## Development Philosophy

Build Ledger from the financial core outward.

The order should be:

```text
Foundation
    ↓
Data Model
    ↓
Transactions
    ↓
Dashboard
    ↓
Budgets
    ↓
Recurring + Education
    ↓
People / IOUs
    ↓
Currency
    ↓
Analytics
    ↓
Goals + Runway
    ↓
Natural Language
    ↓
Future Interfaces
```

Do not start with AI.

The core financial data model must be reliable before adding intelligent interfaces.

---

# Phase 0 — Repository Audit

## Objective

Understand the existing repository before making changes.

## Tasks

* Inspect repository structure.
* Identify existing frontend.
* Identify existing backend.
* Identify package managers.
* Identify existing database configuration.
* Identify environment configuration.
* Identify existing authentication.
* Identify existing tests.
* Identify Docker configuration.
* Identify deployment configuration.
* Identify existing UI components.

## Deliverable

A short architecture assessment containing:

```text
Current architecture
Existing functionality
Missing pieces
Potential conflicts
Recommended Phase 1 changes
```

Do not rewrite the application during this phase.

---

# Phase 1 — Project Foundation

## Objective

Establish a clean development architecture.

## Tasks

### Frontend

Set up:

* Next.js
* TypeScript
* Tailwind CSS
* shadcn/ui
* Basic application layout
* Navigation
* Protected application shell

### Backend

Set up:

* FastAPI
* Configuration management
* API structure
* SQLAlchemy
* PostgreSQL connection
* Health endpoint
* Error handling
* Basic service structure

### Database

Set up:

* PostgreSQL connection
* Alembic
* Initial migration infrastructure

### Development

Set up:

* Environment variables
* `.env.example`
* Basic Docker configuration if useful
* Formatting/linting
* Basic tests

## Done When

Frontend can communicate with FastAPI and FastAPI can successfully communicate with PostgreSQL.

---

# Phase 2 — Authentication and User Ownership

## Objective

Create secure user accounts and establish ownership boundaries.

## Tasks

* Authentication
* Login
* Signup
* Logout
* Session handling
* Protected frontend routes
* Backend authorization
* User model/profile
* User-owned database records
* RLS where appropriate

## Done When

A user can authenticate and cannot access another user's financial records.

---

# Phase 3 — Core Financial Data Model

## Objective

Create the foundational financial schema.

## Models

At minimum:

```text
User
Account
Bucket
Category
Transaction
```

Potential supporting models:

```text
CurrencySetting
AppSetting
```

## Tasks

* Design schema.
* Add migrations.
* Add foreign keys.
* Add indexes.
* Add constraints.
* Add SQLAlchemy models.
* Add Pydantic schemas.
* Add repositories/services where appropriate.
* Add tests.

## Important Rules

* Money uses NUMERIC/DECIMAL.
* Transactions are the source of truth.
* Transfers are distinct from income/expenses.
* User ownership is enforced.

## Done When

Database can represent the complete basic financial model without UI-specific hacks.

---

# Phase 4 — Accounts and Transactions

## Objective

Allow the user to actually track money.

## Tasks

### Accounts

* Create account
* Edit account
* Archive account
* List accounts
* Calculate account balance

### Transactions

* Create expense
* Create income
* Create transfer
* Edit transaction
* Delete transaction
* View transaction
* List transactions

### Classification

Support:

* Bucket
* Category
* Notes
* Date
* Major purchase flag

## Done When

A user can accurately reproduce their current finances through accounts and transactions.

---

# Phase 5 — Transaction History

## Objective

Make financial records easy to inspect.

## Tasks

Build transaction history with:

* Search
* Filtering
* Sorting
* Pagination
* Date ranges
* Account filter
* Bucket filter
* Category filter
* Transaction type filter
* Major purchase filter

## Done When

The user can quickly locate any transaction.

---

# Phase 6 — Dashboard

## Objective

Create the primary financial overview.

## Dashboard Components

### Summary

* Current balance
* Monthly income
* Monthly expenses
* Monthly savings

### Budget

* Budget progress

### Spending

* Spending by bucket
* Spending by category

### Activity

* Recent transactions
* Major purchases

### IOUs

* Money owed
* Money others owe

## Charts

Use Recharts where appropriate.

Avoid unnecessary charts.

Every chart should answer a useful financial question.

---

# Phase 7 — Budgets

## Objective

Help the user control monthly spending.

## Tasks

* Budget model
* Monthly budget creation
* Bucket budgets
* Category budgets
* Budget editing
* Budget deletion
* Budget progress calculation
* Dashboard budget cards
* Over-budget states

## Done When

The user can set monthly limits and immediately see how spending compares with those limits.

---

# Phase 8 — Recurring Expenses and Education

## Objective

Handle recurring obligations and student-specific expenses.

## Recurring

Implement:

* Recurring transaction definitions
* Frequency
* Start date
* Optional end date
* Expected amount
* Category
* Account
* Active/inactive state

Do not automatically record completed transactions unless explicitly confirmed.

## Education

Ensure categories exist for:

* Tuition
* Student Fees
* Health Fees
* Books
* Course Materials
* Software
* Exams
* Certifications
* Other Education

Add education-focused dashboard/reporting where practical.

---

# Phase 9 — People and IOUs

## Objective

Track money owed between the user and other people.

## Tasks

Create:

```text
Person
IOU Event
```

Support:

* Borrowed
* Lent
* Repayment
* Adjustment

Calculate outstanding balances from events.

## UI

Create a People page showing:

```text
Person
Direction
Outstanding Amount
Last Activity
```

Clicking a person should show the complete history.

## Done When

The user can accurately track both money they owe and money owed to them.

---

# Phase 10 — Currency Display

## Objective

Support CAD-first finances with INR display.

## Tasks

* Currency settings
* CAD/INR toggle
* Configurable exchange rate
* Global display formatting
* Dashboard conversion
* Transaction conversion
* Budget conversion
* Analytics conversion

## Rule

All stored transaction values remain CAD.

Example:

```text
Stored:
100 CAD

Display:
CAD → $100
INR → ₹7,000
```

Do not duplicate monetary values in the database.

---

# Phase 11 — Analytics

## Objective

Turn transaction data into useful historical insight.

## Reports

Implement:

* Spending by bucket
* Spending by category
* Income vs expenses
* Monthly spending trend
* Fixed vs variable expenses
* Major purchases
* Education spending
* Savings

## Requirements

Reports should support:

* Date ranges
* Monthly comparison
* Useful empty states
* CAD/INR display

Do not add charts simply for visual decoration.

---

# Phase 12 — Savings Goals

## Objective

Allow users to track financial goals.

## Tasks

Create:

```text
Goal
```

Support:

* Name
* Target amount
* Current progress
* Target date
* Status

Example:

```text
New Laptop
$850 / $2,000
42.5%
```

Integrate goals into the dashboard.

---

# Phase 13 — Financial Runway

## Objective

Provide an optional estimate of how long current funds could last.

## Calculation

A basic implementation may use:

```text
Available Funds
÷
Average Monthly Spending
```

Use a configurable historical period.

Example:

```text
Available funds: $4,000
Average monthly spending: $1,000

Estimated runway: 4 months
```

Clearly label the result as an estimate.

Do not present it as a prediction or guarantee.

---

# Phase 14 — Natural Language Transactions

## Objective

Allow users to enter transactions naturally.

Example:

```text
Spent $42.50 on dinner with friends yesterday.
```

## Processing Pipeline

```text
User Input
    ↓
LLM Extraction
    ↓
Structured Transaction Proposal
    ↓
Backend Validation
    ↓
User Preview
    ↓
Confirmation
    ↓
Existing Transaction Service
    ↓
Database
```

## Critical Rule

The LLM must never directly write to the database.

It only produces structured data.

The backend validates and processes that data.

## Initial AI Scope

Support:

* Expense entry
* Income entry
* Date interpretation
* Category suggestion
* Bucket suggestion
* Account suggestion

Do not initially build an autonomous finance agent.

---

# Phase 15 — Natural Language Read Queries

## Objective

Allow users to ask questions about their own data.

Examples:

```text
How much did I spend this month?

How much did I spend on food?

What were my biggest purchases?

How much did I spend on tuition?

How much do I owe Alex?
```

Initially these should be read-only.

The AI should retrieve structured financial information through controlled backend APIs rather than receiving unrestricted database access.

---

# Phase 16 — Mobile / Widget / Additional Interfaces

## Future

Once the web application and backend are stable:

```text
FastAPI Backend
       |
       +-- Web
       |
       +-- Mobile
       |
       +-- Widget
       |
       +-- AI
```

Potential future features:

* Mobile application
* Home-screen widget
* Quick-add widget
* Voice transaction entry
* Browser extension
* Notification reminders

These should reuse the existing backend rather than duplicate business logic.

---

# Explicitly Deferred Features

The following should remain outside the initial implementation unless requirements change:

* Bank synchronization
* Automated bank imports
* Investment portfolio tracking
* Cryptocurrency
* Live financial-market data
* Advanced tax functionality
* Live FX infrastructure
* Automated financial advice
* Autonomous AI financial agent
* Complex forecasting
* Mobile application
* Browser extension
* Home-screen widget

---

# Definition of Done

A phase is complete only when:

1. The feature is implemented.
2. The database migration is complete if needed.
3. Backend validation exists.
4. Relevant business logic is tested.
5. Frontend behavior works against the real API.
6. Authentication/authorization is respected.
7. Loading and error states exist.
8. Empty states exist where relevant.
9. No secrets are exposed.
10. Existing functionality still works.

---

# Implementation Rule for Codex

Do not implement the entire roadmap in one pass.

Work phase-by-phase.

For each phase:

```text
Inspect
  ↓
Plan
  ↓
Implement
  ↓
Test
  ↓
Review
  ↓
Run
  ↓
Proceed
```

Before beginning a phase, inspect the existing implementation and identify what is already present.

Never replace working functionality simply because a different architecture is possible.
