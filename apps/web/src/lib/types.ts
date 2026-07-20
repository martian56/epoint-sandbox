export interface SessionState {
  auth_required: boolean
  authenticated: boolean
  email: string | null
}

export type TransactionStatus = 'new' | 'success' | 'failed' | 'error' | 'returned' | 'server_error'

export type CallbackStatus = 'pending' | 'delivered' | 'failed' | 'dropped'

export interface Merchant {
  public_key: string
  private_key: string
  name: string
  tin: string | null
  contact_phone: string | null
  result_url: string | null
  success_url: string | null
  error_url: string | null
  site_url: string | null
  balance: number
  features: MerchantFeatures
  created_at: string
}

/** Granted per merchant by epoint. */
export interface MerchantFeatures {
  amex_enabled: boolean
  token_payments_enabled: boolean
  installments_enabled: boolean
  wallets_enabled: boolean
  b2b_enabled: boolean
}

/** Editable on the API Management page. */
export interface MerchantInput {
  name?: string
  tin?: string
  contact_phone?: string
  site_url?: string
  success_url?: string
  error_url?: string
  result_url?: string
  amex_enabled?: boolean
  token_payments_enabled?: boolean
  installments_enabled?: boolean
  wallets_enabled?: boolean
  b2b_enabled?: boolean
}

export interface Transaction {
  transaction: string
  order_id: string
  status: TransactionStatus
  code: string | null
  amount: number
  currency: string
  description: string | null
  card_mask: string | null
  rrn: string | null
  endpoint: string
  trace_id: string
  created_at: string
}

export interface CallbackAttempt {
  id: number
  target_url: string
  attempt: number
  status: CallbackStatus
  data: string
  signature: string
  decoded: Record<string, unknown>
  response_status: number | null
  response_body: string | null
  error: string | null
  duration_ms: number | null
  created_at: string
}

export interface RequestLogEntry {
  trace_id: string
  method: string
  path: string
  status_code: number
  duration_ms: number
  signature_valid: boolean | null
  request: Record<string, unknown> | null
  response: Record<string, unknown> | null
  created_at: string
}

export interface TestCard {
  number: string
  code: string
  outcome: string
  approved: boolean
}

export interface SignatureExplanation {
  concatenated: string
  concatenated_length: number
  sha1_hex: string
  expected_signature: string
  formula: string
  decoded_payload: Record<string, unknown> | null
  decode_error?: string
  provided_signature?: string
  matches?: boolean
  hint?: string
}

export type CardStatus = 'new' | 'active' | 'pending' | 'rejected' | 'expired' | 'session_expired'

export type InvoiceStatus = 'waiting_for_payment' | 'paid' | 'canceled'

export type B2BStatus = 'PENDING' | 'PROCESSING' | 'SUCCESS' | 'FAILED'

export interface SavedCard {
  card_id: string
  mask: string | null
  holder_name: string | null
  expiry: string | null
  status: CardStatus
  is_payout_card: boolean
  bank_code: string | null
  description: string | null
  created_at: string
}

export interface InvoiceRow {
  id: number
  total: number
  status: InvoiceStatus
  recipient_name: string | null
  description: string | null
  phone: string | null
  email: string | null
  is_template: boolean
  allow_installment: boolean
  period_from: string | null
  period_to: string | null
  created_at: string
}

export interface BalanceRow {
  id: number
  amount: number
  balance_after: number
  kind: string
  description: string | null
  transaction_id: number | null
  created_at: string
}

export interface NotificationRow {
  id: number
  invoice_id: number
  channel: string
  recipient: string
  subject: string | null
  body: string
  trace_id: string
  created_at: string
}

export interface B2BRow {
  order_id: string
  status: B2BStatus
  amount: number
  payee_name: string
  payee_iban: string
  bank_code: string
  webhook_sent: boolean
  bulk_id: string | null
  created_at: string
}
