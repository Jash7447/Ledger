export type AccountType = "chequing" | "savings" | "credit_card" | "cash" | "other";

export type Account = {
  id: string;
  name: string;
  type: AccountType;
  currency: "CAD";
  is_active: boolean;
  balance_cad: string;
  created_at: string;
  updated_at: string;
};

export type Category = {
  id: string;
  name: string;
  kind: "expense" | "income" | "funding";
  bucket_id: string | null;
};

export type Bucket = {
  id: string;
  name: string;
  categories: Category[];
};

export type ClassificationCatalog = {
  buckets: Bucket[];
  income_categories: Category[];
  funding_categories: Category[];
};

export type TransactionType = "expense" | "income" | "transfer";

export type LedgerTransaction = {
  id: string;
  account_id: string;
  destination_account_id: string | null;
  type: TransactionType;
  amount_cad: string;
  date: string;
  description: string;
  bucket_id: string | null;
  category_id: string | null;
  notes: string | null;
  expense_classification: "fixed" | "variable" | null;
  is_major_purchase: boolean;
  created_at: string;
  updated_at: string;
};

export type TransactionPage = {
  items: LedgerTransaction[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
};

export type SpendingBreakdownItem = {
  id: string | null;
  name: string;
  amount_cad: string;
};

export type DashboardData = {
  period_start: string;
  period_end: string;
  summary: {
    current_balance_cad: string;
    monthly_income_cad: string;
    monthly_expenses_cad: string;
    monthly_savings_cad: string;
    education_spending_cad: string;
  };
  spending_by_bucket: SpendingBreakdownItem[];
  spending_by_category: SpendingBreakdownItem[];
  budget_progress: BudgetProgress[];
  recent_transactions: LedgerTransaction[];
  major_purchases: LedgerTransaction[];
};

export type BudgetProgress = {
  id: string;
  bucket_id: string | null;
  category_id: string | null;
  scope_type: "bucket" | "category";
  scope_name: string;
  amount_cad: string;
  period_start: string;
  period_end: string;
  spent_cad: string;
  remaining_cad: string;
  percentage_used: string;
  is_over_budget: boolean;
  created_at: string;
  updated_at: string;
};
