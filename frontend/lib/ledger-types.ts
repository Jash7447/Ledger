export type AccountType = "chequing" | "savings" | "credit_card" | "cash" | "other";

export type DisplayCurrency = "CAD" | "INR";

export type CurrencySettings = {
  display_currency: DisplayCurrency;
  cad_to_inr_rate: string;
  updated_at: string;
};

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
    money_owed_to_user_cad: string;
    money_owed_to_others_cad: string;
  };
  spending_by_bucket: SpendingBreakdownItem[];
  spending_by_category: SpendingBreakdownItem[];
  budget_progress: BudgetProgress[];
  recent_transactions: LedgerTransaction[];
  major_purchases: LedgerTransaction[];
  goals: Goal[];
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

export type RecurringFrequency = "weekly" | "biweekly" | "monthly" | "quarterly" | "yearly";

export type RecurringDefinition = {
  id: string;
  account_id: string;
  category_id: string;
  bucket_id: string;
  account_name: string;
  category_name: string;
  bucket_name: string;
  description: string;
  expected_amount_cad: string;
  frequency: RecurringFrequency;
  start_date: string;
  end_date: string | null;
  is_active: boolean;
  notes: string | null;
  next_occurrence_date: string | null;
  created_at: string;
  updated_at: string;
};

export type EducationReport = {
  date_from: string;
  date_to: string;
  total_spent_cad: string;
  transaction_count: number;
  spending_by_category: Array<{
    category_id: string;
    category_name: string;
    amount_cad: string;
  }>;
  transactions: LedgerTransaction[];
};

export type MonthlyAnalyticsItem = {
  month: string;
  income_cad: string;
  expenses_cad: string;
  savings_cad: string;
};

export type AnalyticsData = {
  date_from: string;
  date_to: string;
  summary: {
    income_cad: string;
    expenses_cad: string;
    savings_cad: string;
    education_spending_cad: string;
    major_purchase_spending_cad: string;
  };
  spending_by_bucket: SpendingBreakdownItem[];
  spending_by_category: SpendingBreakdownItem[];
  fixed_vs_variable: SpendingBreakdownItem[];
  monthly_trend: MonthlyAnalyticsItem[];
  major_purchases: LedgerTransaction[];
};

export type GoalStatus = "active" | "paused" | "completed" | "cancelled";

export type Goal = {
  id: string;
  name: string;
  target_amount_cad: string;
  current_amount_cad: string;
  remaining_amount_cad: string;
  percentage_complete: string;
  target_date: string | null;
  status: GoalStatus;
  created_at: string;
  updated_at: string;
};

export type IOUEventType = "borrowed" | "lent" | "repayment_received" | "repayment_made" | "adjustment";
export type IOUAdjustmentDirection = "owes_user" | "user_owes";
export type IOUDirection = "owed_to_user" | "user_owes" | "settled";

export type PersonSummary = {
  id: string;
  name: string;
  direction: IOUDirection;
  outstanding_amount_cad: string;
  last_activity: string | null;
  event_count: number;
};

export type IOUEvent = {
  id: string;
  person_id: string;
  event_type: IOUEventType;
  adjustment_direction: IOUAdjustmentDirection | null;
  amount_cad: string;
  effect_cad: string;
  running_balance_cad: string;
  date: string;
  notes: string | null;
  created_at: string;
  updated_at: string;
};

export type PersonDetail = PersonSummary & {
  notes: string | null;
  created_at: string;
  updated_at: string;
  events: IOUEvent[];
};
