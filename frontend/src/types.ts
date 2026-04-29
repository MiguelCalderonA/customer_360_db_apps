export type ChannelKey = "mobile_app" | "partner_checkout" | "web_portal" | "cobranded_card";

export interface CustomerSummary {
  customer_id: string;
  email: string;
  first_name: string;
  last_name: string;
  channel_count: number;
  channels_used: ChannelKey[];
  mobile_app_order_count: number;
  partner_loan_count: number;
  web_application_count: number;
  card_account_count: number;
}

export interface MobileEvent {
  order_id: string;
  merchant_category: string;
  bnpl_plan: string;
  order_amount: number;
  status: string;
  order_ts: string;
}

export interface PartnerEvent {
  loan_id: string;
  partner_name: string;
  principal_amount: number;
  apr_pct: number;
  term_months: number;
  approval_status: string;
  originated_date: string;
}

export interface WebEvent {
  application_id: string;
  utm_source: string;
  loan_purpose: string;
  requested_amount: number;
  funded_amount: number;
  credit_score: number;
  kyc_status: string;
  applied_date: string;
}

export interface CardEvent {
  account_id: string;
  card_partner: string;
  credit_limit: number;
  current_balance: number;
  utilization_pct: number;
  rewards_tier: string;
  payment_behavior: string;
  delinquency_days: number;
  account_status: string;
  account_opened: string;
}

export interface CustomerProfile extends CustomerSummary {
  mobile_app_total_spend: number;
  partner_total_principal: number;
  web_total_funded: number;
  web_max_credit_score: number;
  card_total_credit_limit: number;
  card_total_balance: number;
  card_max_delinquency_days: number;
  mobile_app_events: MobileEvent[];
  partner_loan_events: PartnerEvent[];
  web_application_events: WebEvent[];
  card_account_events: CardEvent[];
  profile_last_updated: string;
}

export interface Stats {
  total_customers: number;
  multi_channel_customers: number;
  total_mobile_orders: number;
  total_partner_loans: number;
  total_web_applications: number;
  total_card_accounts: number;
  total_mobile_spend: number;
  total_partner_principal: number;
  total_web_funded: number;
  total_card_balance: number;
}
