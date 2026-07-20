import type {
  B2BRow,
  BalanceRow,
  CallbackAttempt,
  InvoiceRow,
  Merchant,
  MerchantInput,
  NotificationRow,
  RequestLogEntry,
  SavedCard,
  SignatureExplanation,
  TestCard,
  Transaction,
} from './types'

export class ApiError extends Error {
  constructor(
    message: string,
    readonly status: number,
  ) {
    super(message)
    this.name = 'ApiError'
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`/_sandbox${path}`, {
    headers: init?.body ? { 'Content-Type': 'application/json' } : undefined,
    ...init,
  })

  if (!response.ok) {
    const detail = await response
      .json()
      .then((body) => body?.detail)
      .catch(() => null)
    throw new ApiError(detail ?? `Request to ${path} failed`, response.status)
  }
  return response.status === 204 ? (undefined as T) : (response.json() as Promise<T>)
}

function post<T>(path: string, body: unknown): Promise<T> {
  return request<T>(path, { method: 'POST', body: JSON.stringify(body) })
}

export interface ListOptions {
  limit?: number
  merchant?: string | undefined
}

function listPath(base: string, { limit = 50, merchant }: ListOptions = {}): string {
  const params = new URLSearchParams({ limit: String(limit) })
  if (merchant) params.set('merchant', merchant)
  return `${base}?${params}`
}

export const api = {
  merchants: () => request<Merchant[]>('/merchants'),

  createMerchant: (input: MerchantInput) =>
    request<Merchant>('/merchants', { method: 'POST', body: JSON.stringify(input) }),

  updateMerchant: (publicKey: string, changes: MerchantInput) =>
    request<Merchant>(`/merchants/${publicKey}`, {
      method: 'PATCH',
      body: JSON.stringify(changes),
    }),

  deleteMerchant: (publicKey: string) =>
    request<void>(`/merchants/${publicKey}`, { method: 'DELETE' }),

  rotateKey: (publicKey: string) =>
    request<Merchant>(`/merchants/${publicKey}/rotate-key`, { method: 'POST' }),
  transactions: (options?: ListOptions) =>
    request<Transaction[]>(listPath('/transactions', options)),
  callbacks: (options?: ListOptions) => request<CallbackAttempt[]>(listPath('/callbacks', options)),
  requests: (options?: ListOptions) => request<RequestLogEntry[]>(listPath('/requests', options)),
  testCards: () => request<{ scheme: string; cards: TestCard[] }>('/cards'),
  savedCards: (options?: ListOptions) => request<SavedCard[]>(listPath('/saved-cards', options)),
  invoices: (options?: ListOptions) => request<InvoiceRow[]>(listPath('/invoices', options)),
  balance: (options?: ListOptions) => request<BalanceRow[]>(listPath('/balance', options)),
  notifications: (options?: ListOptions) =>
    request<NotificationRow[]>(listPath('/notifications', options)),
  b2b: (options?: ListOptions) => request<B2BRow[]>(listPath('/b2b', options)),

  verifySignature: (privateKey: string, data: string, signature?: string) =>
    post<SignatureExplanation>('/signature/verify', {
      private_key: privateKey,
      data,
      signature: signature || null,
    }),

  buildSignature: (privateKey: string, payload: Record<string, unknown>) =>
    post<{ data: string; signature: string; payload: Record<string, unknown> }>(
      '/signature/build',
      { private_key: privateKey, payload },
    ),
}
