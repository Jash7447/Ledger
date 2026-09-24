# Ledger — Agent Instructions

## Project Overview

Ledger is a personal finance web application designed to help a user track income, expenses, budgets, accounts, education costs, major purchases, and money owed to/from other people.

The application is Canada-first:

* CAD is the source-of-truth currency.
* INR is an optional display/conversion currency.
* Initial CAD → INR conversion uses a manually configurable exchange rate.
* Initial default rate: `1 CAD = 70 INR`.
* Never store INR as an independent financial source of truth.

Ledger should be useful as a normal finance tracker first, while having a clean architecture that can later support natural-language financial entry, mobile clients, widgets, and other interfaces.

---

## Tech Stack

### Frontend

* Next.js
* TypeScript
* Tailwind CSS
* shadcn/ui
* Recharts

### Backend

* Python
* FastAPI
* SQLAlchemy
* Alembic

### Database

* PostgreSQL
* Supabase-hosted PostgreSQL

### Development

* Docker where appropriate
* Environment variables for secrets and configuration

---

## Architecture

Use the following architecture:

```text
Next.js Frontend
       |
       | HTTP / JSON
       v
FastAPI Backend
       |
       | SQLAlchemy
       v
PostgreSQL
   (Supabase)
```

### Architectural rules

1. FastAPI is the primary business/API layer.
2. Do not put financial business logic directly in Next.js.
3. Do not couple the application's core business logic to Supabase-specific APIs.
4. PostgreSQL is the source of truth for financial data.
5. Use SQLAlchemy for database access.
6. Use Alembic for schema migrations.
7. Keep frontend and backend concerns separated.
8. Design APIs so that future mobile applications can use the same backend.
9. Business rules should live in reusable backend services rather than inside API route handlers.
10. Prefer simple, maintainable architecture over unnecessary abstraction.

---

## Financial Data Principles

### Currency

CAD is the canonical currency.

Store monetary values in CAD.

INR should be calculated at display time using the configured exchange rate.

Example:

```text
Stored:
amount_cad = 100

Display:
CAD = $100
INR = ₹7,000
```

Do not store both CAD and INR transaction amounts.

The exchange rate must be configurable.

---

### Transactions

Transactions are the financial source of truth.

Supported transaction types:

* `expense`
* `income`
* `transfer`

Transfers must not count as expenses or income.

Account balances should be derived from transactions rather than maintained as an independent authoritative balance.

Every transaction should belong to an account.

---

### Accounts

Support at minimum:

* Chequing
* Savings
* Credit Card
* Cash
* Other

The data model should allow additional account types later.

---

### Buckets vs Categories

Buckets represent broad spending areas.

Categories represent specific spending types.

Do not combine these concepts.

Example:

```text
Bucket: Essentials
Category: Rent
```

Recommended buckets:

* Essentials
* Education
* Lifestyle
* Leisure
* Travel
* Financial
* Other

Categories should be defined in `docs/PRODUCT_SPEC.md`.

---

### Major Purchases

Major purchases are normal transactions with an additional flag.

Do not create a separate financial system for major purchases.

Use something similar to:

```text
is_major_purchase: boolean
```

The threshold should be configurable.

Initial suggested threshold:

```text
$150 CAD
```

Examples:

* Phone
* Laptop
* Shoes
* Jacket
* Electronics

---

### Education Expenses

Education-related expenses are first-class financial categories.

Examples:

* Tuition
* Student Fees
* Health Fees
* Books
* Course Materials
* Software
* Exams
* Certifications
* Other Education

The system should eventually support semester-based education tracking, but this is not required for the first implementation.

---

### Budgets

Budgets should support monthly limits.

A budget may apply to:

* a bucket
* a category

The UI should show:

```text
Budget
Spent
Remaining
Percentage Used
```

Support fixed and variable expense classification where practical.

---

### Recurring Transactions

Recurring expenses should be represented separately from actual completed transactions.

Examples:

* Rent
* Phone
* Internet
* Streaming subscriptions

An expected recurring expense must not automatically become a completed transaction unless explicitly configured to do so.

---

### People / IOUs

Money owed to or from other people must not be represented by manually editing one mutable balance.

Instead, store individual events.

Examples:

```text
Borrowed from Alex: $100
Repaid Alex: $40
```

Outstanding amount:

```text
$60
```

Support both:

* User owes another person
* Another person owes user

The balance should be calculated from the underlying events.

---

### Income vs Funding

Distinguish earned income from external funding.

Possible income types:

* Salary
* Freelance
* Scholarship
* Interest
* Refund
* Other

Possible funding sources:

* Family Support
* Gift
* Loan
* Other External Funding

Family support should not automatically be treated as earned income.

---

### Savings Goals

The architecture should eventually support goals such as:

* Emergency Fund
* Laptop
* Vacation
* Other savings goals

Do not implement complex investment functionality unless explicitly requested.

---

### Runway

A future runway metric may estimate how long available funds could last based on historical spending.

It must be clearly labeled as an estimate.

Never present an estimated runway as a guaranteed forecast.

---

## Natural Language / AI

Natural-language financial entry is a future feature.

Example:

```text
Spent $42.50 on dinner with friends yesterday.
```

The intended flow is:

```text
Natural language
      ↓
Structured extraction
      ↓
Validation
      ↓
Preview
      ↓
User confirmation
      ↓
Existing transaction service
      ↓
Database
```

AI must never directly write financial records to the database.

All AI-created transactions must go through the same validation and transaction service used by normal UI requests.

Future read-only queries may include:

```text
How much did I spend on food this month?
```

Do not implement the AI system before the core finance system is stable.

---

## Security

Financial data must be treated as sensitive.

Follow these rules:

* Never expose secrets in frontend code.
* Use environment variables for secrets.
* Validate API inputs.
* Enforce authorization on the backend.
* Use authentication before exposing personal financial data.
* Use appropriate PostgreSQL/Supabase Row Level Security where applicable.
* Never trust user IDs supplied by the client.
* Never allow one user to access another user's financial records.
* Use database constraints where they protect financial integrity.
* Avoid sending unnecessary financial data to external AI services.
* Never let an AI model bypass normal authorization or validation.

---

## Code Quality

Prefer:

* Small focused modules
* Clear names
* Explicit types
* Reusable backend services
* Reusable frontend components
* Validation at API boundaries
* Database constraints
* Meaningful error messages
* Automated tests for important business logic

Avoid:

* Premature abstractions
* Giant components
* Giant API route files
* Duplicated business logic
* Hardcoded financial calculations
* Storing derived financial values unnecessarily
* Overengineering

---

## API Design

Use RESTful APIs where practical.

Examples:

```text
GET    /accounts
POST   /accounts

GET    /transactions
POST   /transactions
GET    /transactions/{id}
PATCH  /transactions/{id}
DELETE /transactions/{id}

GET    /budgets
POST   /budgets

GET    /people
POST   /people

GET    /goals
POST   /goals
```

Exact API structure may evolve as implementation progresses.

Keep APIs versionable and suitable for future mobile clients.

---

## Database Design

Use UUIDs or another robust identifier strategy consistently.

Every user-owned financial entity must be associated with the authenticated user.

Use:

* Foreign keys
* Appropriate indexes
* Check constraints where useful
* Unique constraints where appropriate
* Timestamps
* Decimal/numeric types for monetary values

Do not use floating-point types for money.

Use PostgreSQL `NUMERIC`/`DECIMAL` for monetary values.

---

## Frontend Principles

The UI should feel:

* Modern
* Clean
* Financial
* Slightly technical
* Information-dense without being overwhelming

Prioritize:

* Clear dashboards
* Useful charts
* Fast transaction entry
* Strong filtering
* Good empty states
* Responsive design
* Accessibility

Do not sacrifice usability for visual complexity.

---

## Development Workflow

Before implementing a major feature:

1. Read `AGENTS.md`.
2. Read the relevant section of `docs/PRODUCT_SPEC.md`.
3. Read `docs/ROADMAP.md`.
4. Inspect the existing repository.
5. Understand existing architecture before changing it.
6. Identify dependencies and affected files.
7. Implement the smallest coherent change.
8. Add/update tests.
9. Run relevant validation.
10. Summarize what changed.

Do not rebuild existing functionality unnecessarily.

---

## Important Product Rule

Ledger is a tracking and organization tool.

Do not turn Ledger into a financial-advice application.

The application should report and visualize the user's financial data without making unsupported financial recommendations.

---

## Current Scope

The initial product should focus on:

* Authentication
* Accounts
* Transactions
* Income
* Expenses
* Transfers
* Buckets
* Categories
* Monthly budgets
* Dashboard
* Transaction history
* CAD/INR display toggle
* Configurable CAD → INR exchange rate
* Recurring expenses
* Education expenses
* Major purchases
* People / IOUs

Do not implement the following in the initial MVP:

* Bank account synchronization
* Investment portfolio management
* Live exchange-rate infrastructure
* Mobile application
* Browser extension
* Home-screen widget
* Complex AI assistant
* Automated financial advice

Build a strong foundation for these features instead.
