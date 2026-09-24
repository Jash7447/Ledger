# Ledger — Product Specification

## 1. Product Vision

Ledger is a personal finance application for tracking where money comes from, where it goes, what has been budgeted, and what is owed between people.

The application is designed primarily for a student/young professional living in Canada.

The product should make it easy to answer questions such as:

* How much money do I currently have?
* How much did I spend this month?
* Where did my money go?
* Am I within my monthly budget?
* How much did I spend on education?
* How much did I spend on large purchases?
* How much do I owe my family or friends?
* How much do others owe me?
* How much did I earn?
* How much do I have left for the month?
* How much am I spending on recurring expenses?
* How much have I spent on tuition and university expenses?

---

# 2. Target User

The initial target user is an individual living in Canada who wants a detailed but easy-to-use personal finance tracker.

The user may have:

* Rent
* Groceries
* Transportation expenses
* Tuition
* Student fees
* Subscriptions
* Personal purchases
* Leisure spending
* Income
* Family support
* Money borrowed from or lent to others
* Savings goals
* Large one-time purchases

---

# 3. Currency

## Canonical Currency

CAD is the application's source-of-truth currency.

All monetary records are stored in CAD.

Example:

```text
Transaction:
amount_cad = 42.50
```

## INR Display

Users may toggle monetary displays between:

```text
CAD
INR
```

Initial conversion:

```text
1 CAD = 70 INR
```

The exchange rate should be configurable.

INR is a display layer and must not become an independent stored transaction amount.

Future versions may support live exchange rates.

---

# 4. Authentication

Users must have individual accounts.

Each user must only be able to access their own financial data.

Authentication may use Supabase Auth or another suitable authentication mechanism, while FastAPI remains responsible for backend authorization and business logic.

Required capabilities:

* Sign up
* Sign in
* Sign out
* Session handling
* Protected application routes
* Backend authorization

---

# 5. Accounts

Users should be able to create financial accounts.

## Account Types

Initial types:

* Chequing
* Savings
* Credit Card
* Cash
* Other

Each account should contain information such as:

```text
id
user_id
name
type
currency
is_active
created_at
updated_at
```

Although CAD is the initial canonical currency, the schema should not unnecessarily prevent future multi-currency support.

## Account Balance

Account balances should be derived from transactions.

Do not make a manually entered balance the authoritative source of truth.

---

# 6. Transactions

Transactions are the core of Ledger.

## Transaction Types

### Expense

Money leaves the user's account.

Examples:

* Rent
* Groceries
* Dinner
* Shoes
* Tuition

### Income

Money enters the user's account.

Examples:

* Salary
* Freelance payment
* Scholarship
* Interest
* Refund

### Transfer

Money moves between accounts owned by the user.

Example:

```text
Chequing → Savings
```

Transfers must not affect total spending or total income.

---

# 7. Transaction Fields

A transaction should support fields such as:

```text
id
user_id
account_id
type
amount_cad
date
description
bucket_id
category_id
notes
is_major_purchase
created_at
updated_at
```

Potential future fields:

```text
merchant
location
tags
recurring_transaction_id
```

Do not add fields without a concrete product requirement.

---

# 8. Spending Buckets

Buckets represent broad financial areas.

Initial buckets:

### Essentials

For necessary recurring or day-to-day expenses.

Categories:

* Rent
* Groceries
* Utilities
* Phone
* Internet
* Transportation
* Insurance
* Healthcare
* Household

### Education

Categories:

* Tuition
* Student Fees
* Health Fees
* Books
* Course Materials
* Software
* Exams
* Certifications
* Other Education

### Lifestyle

Categories:

* Clothing
* Shoes
* Electronics
* Personal Care
* Shopping
* Gifts

### Leisure

Categories:

* Restaurants
* Coffee
* Takeout
* Entertainment
* Movies
* Events
* Gaming

### Travel

Categories:

* Flights
* Hotels
* Local Transport
* Travel Food
* Visa/Immigration
* Other Travel

### Financial

Categories:

* Savings
* Investments
* Debt Repayment

### Other

Categories:

* Miscellaneous

Buckets and categories must remain separate concepts.

---

# 9. Income

Income should be tracked separately from expenses.

Initial income categories:

* Salary
* Freelance
* Scholarship
* Interest
* Refund
* Other Income

External funding should be distinguishable from earned income.

Initial funding categories:

* Family Support
* Gift
* Loan
* Other Funding

---

# 10. Major Purchases

Large purchases should be easy to identify.

A major purchase is still a normal transaction.

Use:

```text
is_major_purchase = true
```

The initial configurable threshold should be:

```text
$150 CAD
```

The user should be able to view major purchases separately.

Examples:

* Phone
* Laptop
* Shoes
* Jacket
* Electronics
* Furniture

Major purchases should not require a separate financial category.

---

# 11. Budgets

Users can create monthly budgets.

A budget can apply to either:

* A bucket
* A category

Example:

```text
Leisure budget: $300/month
Restaurants budget: $150/month
```

## Budget Dashboard

Show:

```text
Budget:      $300
Spent:       $215
Remaining:   $85
Used:        71.7%
```

The system should support:

* Monthly budgets
* Budget start/end period
* Bucket-level budgets
* Category-level budgets
* Budget progress
* Over-budget indicators

Future versions may support custom periods.

---

# 12. Fixed vs Variable Expenses

Expenses should eventually be distinguishable as:

```text
Fixed
Variable
```

Examples:

Fixed:

* Rent
* Phone
* Internet
* Subscription

Variable:

* Groceries
* Restaurants
* Shopping
* Entertainment

This distinction should support analytics.

---

# 13. Recurring Transactions

Users can define recurring financial events.

Examples:

* Rent every month
* Phone bill every month
* Netflix every month
* Internet every month

A recurring transaction definition represents an expected event.

It should not automatically create a completed financial transaction unless the product explicitly supports automated posting.

The system should eventually support:

```text
Recurring Transaction
    ↓
Expected occurrence
    ↓
User confirms / records actual transaction
```

---

# 14. Education Tracking

Education expenses are important enough to receive dedicated reporting.

Track:

* Tuition
* Student Fees
* Health Fees
* Books
* Course Materials
* Software
* Exams
* Certifications
* Other Education

Future versions should support:

```text
Academic Year
    ↓
Semester
    ↓
Education Expenses
```

The MVP does not require full semester management.

---

# 15. People and IOUs

Users can track money owed to and from other people.

Example:

```text
Alex owes me $50
```

or:

```text
I owe Alex $120
```

## Event-based model

Do not store only:

```text
Alex balance = $120
```

Instead record events.

Example:

```text
Borrowed from Alex: +$100
Repaid Alex: -$40
```

Calculated outstanding amount:

```text
$60
```

Possible event types:

* Borrowed
* Lent
* Repayment Received
* Repayment Made
* Adjustment

The system should support a transaction/event history per person.

---

# 16. Dashboard

The dashboard is the primary landing page after authentication.

It should show:

## Financial Summary

* Current available balance
* Monthly income
* Monthly expenses
* Monthly savings
* Money owed to others
* Money others owe the user

## Budget Summary

Show progress for important budgets.

Example:

```text
Essentials
$1,050 / $1,500

Leisure
$210 / $300

Education
$1,800 / $2,000
```

## Spending Breakdown

Use charts for:

* Spending by bucket
* Spending by category

## Recent Transactions

Show the most recent transactions.

## Major Purchases

Show recent major purchases.

## Education

Show education spending for the current period.

## Goals

Show savings-goal progress when goals are implemented.

---

# 17. Transaction History

Users should have a dedicated transaction history page.

Required functionality:

* Search
* Filter
* Sort
* Pagination
* Date filtering
* Account filtering
* Bucket filtering
* Category filtering
* Transaction type filtering
* Major purchase filtering

Each transaction should clearly show:

```text
Date
Description
Category
Account
Amount
```

---

# 18. Analytics

Analytics should help users understand historical behavior.

Required reports:

### Spending by Bucket

Example:

```text
Essentials    $1,250
Leisure         $280
Education       $900
Travel          $150
```

### Spending by Category

Example:

```text
Rent        $900
Groceries   $320
Restaurants $180
```

### Income vs Expenses

Monthly comparison.

### Spending Trend

Display spending over time.

### Fixed vs Variable

Compare fixed and variable expenses.

### Major Purchases

Display major purchases over a selected date range.

### Education Spending

Display education expenses separately.

### Savings

Show income minus expenses and goal progress.

All analytics should support useful date ranges.

---

# 19. Savings Goals

Users can define savings goals.

Example:

```text
Goal: New Laptop
Target: $2,000
Saved: $850
Progress: 42.5%
```

Goals should support:

* Name
* Target amount
* Current amount/progress
* Target date
* Status

The exact mechanism for associating transactions with goals can be decided during implementation.

---

# 20. Financial Runway

A future dashboard metric can estimate financial runway.

Example:

```text
Available funds: $4,000
Average monthly spending: $1,000

Estimated runway: 4 months
```

The UI must clearly label this as an estimate.

The calculation should use a configurable historical period.

---

# 21. Settings

Settings should include:

### Currency

```text
Display currency:
CAD / INR
```

### Exchange Rate

```text
CAD → INR
70
```

### Major Purchase Threshold

```text
$150 CAD
```

Future settings may include:

* Budget defaults
* Date preferences
* Notification preferences
* Theme

---

# 22. Natural Language Input — Future

The application should eventually allow users to enter:

```text
Spent $42.50 on dinner with friends yesterday.
```

The system should convert this into a proposed transaction:

```text
Type: Expense
Amount: $42.50 CAD
Category: Restaurants
Bucket: Leisure
Date: Yesterday
Description: Dinner with friends
```

The user must review and confirm before saving.

AI should not directly write to the database.

The existing transaction service must be used after confirmation.

---

# 23. Future AI Queries

Future read-only queries could include:

```text
How much did I spend this month?

How much did I spend on restaurants?

How much did I spend on education this semester?

What were my biggest purchases this year?

How much do I owe my family?
```

These queries should initially be read-only.

---

# 24. Future Interfaces

Ledger should eventually support multiple interfaces:

```text
Web
 |
 +-- Next.js

Mobile
 |
 +-- Future mobile application

Widget
 |
 +-- Future widget

AI
 |
 +-- Natural language interface
```

All interfaces should communicate with the same FastAPI backend.

---

# 25. Non-Goals for MVP

Do not build these initially:

* Bank synchronization
* Automatic bank transaction imports
* Investment portfolio management
* Cryptocurrency tracking
* Live financial-market data
* Complex tax filing
* Automated financial advice
* Mobile application
* Browser extension
* Home-screen widget
* Complex AI agent
* Fully automated transaction creation
* Advanced forecasting

These may be considered later.

---

# 26. MVP Definition

The MVP is complete when a user can:

1. Create an account.
2. Sign in securely.
3. Create financial accounts.
4. Record expenses.
5. Record income.
6. Record transfers.
7. Categorize transactions.
8. Assign transactions to buckets.
9. View account balances.
10. View monthly spending.
11. Set monthly budgets.
12. View budget progress.
13. Record recurring expenses.
14. Track tuition and education expenses.
15. Mark major purchases.
16. Add people.
17. Track money owed to/from people.
18. View a useful dashboard.
19. Search/filter transaction history.
20. Toggle CAD/INR display.
21. Configure the CAD → INR exchange rate.
22. View basic spending analytics.

The application should be usable without any AI functionality.
