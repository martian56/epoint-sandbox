"""Documented response fields, generated from the scraped epoint docs.

Regenerate with scripts/extract_contracts.py. Do not edit by hand.
"""

DOCUMENTED_RESPONSE_FIELDS: dict[str, frozenset[str]] = {
    "/api/1/amex-request": frozenset(
        {"message", "redirect_url", "status", "trace_id", "transaction"}
    ),
    "/api/1/b2b/payment": frozenset({"bulkId", "order_id", "status"}),
    "/api/1/b2b/payment/{order_id}": frozenset(
        {
            "amount",
            "bulkId",
            "created_at",
            "order_id",
            "payee_iban",
            "payee_name",
            "status",
            "webhook_sent",
        }
    ),
    "/api/1/card-registration": frozenset(
        {"bank_response", "bank_transaction", "card_id", "code", "message", "status", "trace_id"}
    ),
    "/api/1/card-registration-with-pay": frozenset(
        {
            "amount",
            "bank_response",
            "bank_transaction",
            "card_id",
            "card_mask",
            "card_name",
            "code",
            "operation_code",
            "order_id",
            "other_attr",
            "rrn",
            "status",
            "trace_id",
            "transaction",
        }
    ),
    "/api/1/execute-pay": frozenset(
        {
            "amount",
            "bank_response",
            "bank_transaction",
            "card_mask",
            "card_name",
            "message",
            "rrn",
            "status",
            "trace_id",
            "transaction",
        }
    ),
    "/api/1/get-installment-request": frozenset(
        {"installment_card_id", "installment_months", "name"}
    ),
    "/api/1/get-status": frozenset(
        {
            "amount",
            "bank_response",
            "bank_transaction",
            "card_mask",
            "card_name",
            "code",
            "message",
            "operation_code",
            "other_attr",
            "rrn",
            "status",
            "trace_id",
            "transaction",
        }
    ),
    "/api/1/get-status-card": frozenset(
        {"description", "expired_date", "id", "mask", "name", "status", "trace_id"}
    ),
    "/api/1/installment-request": frozenset(
        {"message", "redirect_url", "status", "trace_id", "transaction"}
    ),
    "/api/1/invoices/create": frozenset({"id", "message", "status", "trace_id"}),
    "/api/1/invoices/list": frozenset({"invoices", "message", "status", "trace_id"}),
    "/api/1/invoices/send-email": frozenset({"message", "status", "trace_id"}),
    "/api/1/invoices/send-sms": frozenset({"message", "status", "trace_id"}),
    "/api/1/invoices/update": frozenset({"message", "status", "trace_id"}),
    "/api/1/invoices/view": frozenset({"invoice", "message", "status", "trace_id"}),
    "/api/1/payment-change-sum": frozenset({"message", "redirect_url", "status", "trace_id"}),
    "/api/1/payment-request": frozenset(
        {"message", "redirect_url", "status", "trace_id", "transaction"}
    ),
    "/api/1/pre-auth-complete": frozenset({"message", "status", "trace_id", "transaction"}),
    "/api/1/pre-auth-request": frozenset(
        {"message", "redirect_url", "status", "trace_id", "transaction"}
    ),
    "/api/1/refund-request": frozenset(
        {
            "amount",
            "bank_response",
            "bank_transaction",
            "card_mask",
            "card_name",
            "message",
            "rrn",
            "status",
            "trace_id",
            "transaction",
        }
    ),
    "/api/1/request": frozenset({"message", "redirect_url", "status", "trace_id", "transaction"}),
    "/api/1/reverse": frozenset({"message", "status", "trace_id"}),
    "/api/1/split-execute-pay": frozenset(
        {
            "amount",
            "bank_response",
            "bank_transaction",
            "card_mask",
            "card_name",
            "message",
            "rrn",
            "split_amount",
            "status",
            "trace_id",
            "transaction",
        }
    ),
    "/api/1/split-request": frozenset(
        {"message", "redirect_url", "status", "trace_id", "transaction"}
    ),
    "/api/1/wallet/payment": frozenset(
        {"message", "redirect_url", "status", "trace_id", "transaction"}
    ),
}

# Extras the sandbox adds deliberately. Reasons live in the generator.
SANCTIONED_EXTRAS: dict[str, frozenset[str]] = {
    "/api/1/amex-request": frozenset({"redirect_url"}),
    "/api/1/card-registration": frozenset({"redirect_url"}),
    "/api/1/card-registration-with-pay": frozenset({"redirect_url"}),
    "/api/1/installment-request": frozenset({"redirect_url"}),
    "/api/1/payment-change-sum": frozenset({"redirect_url"}),
    "/api/1/payment-request": frozenset({"redirect_url"}),
    "/api/1/pre-auth-request": frozenset({"redirect_url"}),
    "/api/1/request": frozenset({"redirect_url"}),
    "/api/1/split-request": frozenset({"redirect_url"}),
    "/api/1/token/widget": frozenset({"transaction", "widget_url"}),
    "/api/1/wallet/payment": frozenset({"redirect_url"}),
}

# Rests on documentation alone, never seen from the real gateway.
UNVERIFIED: dict[str, str] = {
    "/api/1/b2b/payment": "not exercised against production",
    "/api/1/b2b/payment/{order_id}": "not exercised against production",
    "/api/1/card-registration": "redirect_url is undocumented; confirm against production",
    "/api/1/payment-change-sum": (
        "docs omit transaction where siblings include it; the sandbox withholds it as "
        "the safe direction, but production may send it"
    ),
    "/api/1/refund-request": "payout mode is inferred from the card flag; unverified",
    "/api/1/request": (
        "the sandbox accepts any language value; whether production validates it "
        "against az, en and ru is unknown"
    ),
}
