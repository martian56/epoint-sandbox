from datetime import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import (
    JSON,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from epoint_sandbox.models.base import Base, TimestampMixin, enum_column
from epoint_sandbox.models.enums import (
    B2BStatus,
    CallbackStatus,
    CardStatus,
    InvoiceStatus,
    TransactionStatus,
)


class Merchant(Base, TimestampMixin):
    __tablename__ = "merchants"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    public_key: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    private_key: Mapped[str] = mapped_column(String(128))
    name: Mapped[str] = mapped_column(String(255))
    tin: Mapped[str | None] = mapped_column(String(16), default=None)
    contact_phone: Mapped[str | None] = mapped_column(String(32), default=None)

    site_url: Mapped[str | None] = mapped_column(String(512), default=None)
    result_url: Mapped[str | None] = mapped_column(String(512), default=None)
    success_url: Mapped[str | None] = mapped_column(String(512), default=None)
    error_url: Mapped[str | None] = mapped_column(String(512), default=None)

    # Granted per merchant by epoint. Off by default.
    amex_enabled: Mapped[bool] = mapped_column(default=False)
    token_payments_enabled: Mapped[bool] = mapped_column(default=False)
    installments_enabled: Mapped[bool] = mapped_column(default=False)
    wallets_enabled: Mapped[bool] = mapped_column(default=False)
    b2b_enabled: Mapped[bool] = mapped_column(default=False)

    transactions: Mapped[list["Transaction"]] = relationship(
        back_populates="merchant", foreign_keys="Transaction.merchant_id"
    )
    cards: Mapped[list["Card"]] = relationship(back_populates="merchant")


class Transaction(Base, TimestampMixin):
    __tablename__ = "transactions"
    __table_args__ = (Index("ix_transactions_merchant_order", "merchant_id", "order_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    transaction_id: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    merchant_id: Mapped[int] = mapped_column(ForeignKey("merchants.id"), index=True)
    order_id: Mapped[str] = mapped_column(String(255), index=True)

    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    currency: Mapped[str] = mapped_column(String(3), default="AZN")
    description: Mapped[str | None] = mapped_column(Text, default=None)
    language: Mapped[str] = mapped_column(String(2), default="az")

    status: Mapped[TransactionStatus] = mapped_column(
        enum_column(TransactionStatus), default=TransactionStatus.NEW
    )
    bank_code: Mapped[str | None] = mapped_column(String(8), default=None)
    message: Mapped[str | None] = mapped_column(String(255), default=None)
    operation_code: Mapped[str | None] = mapped_column(String(8), default=None)

    bank_transaction: Mapped[str | None] = mapped_column(String(32), default=None)
    rrn: Mapped[str | None] = mapped_column(String(16), default=None)
    card_mask: Mapped[str | None] = mapped_column(String(24), default=None)
    card_name: Mapped[str | None] = mapped_column(String(255), default=None)

    endpoint: Mapped[str] = mapped_column(String(64))
    checkout_token: Mapped[str | None] = mapped_column(String(64), unique=True, default=None)
    success_redirect_url: Mapped[str | None] = mapped_column(String(512), default=None)
    error_redirect_url: Mapped[str | None] = mapped_column(String(512), default=None)
    other_attr: Mapped[dict[str, Any] | None] = mapped_column(JSON, default=None)

    card_id: Mapped[int | None] = mapped_column(ForeignKey("cards.id"), default=None)
    split_merchant_id: Mapped[int | None] = mapped_column(ForeignKey("merchants.id"), default=None)
    split_amount: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), default=None)

    trace_id: Mapped[str] = mapped_column(String(32), index=True)
    paid_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=None)

    merchant: Mapped[Merchant] = relationship(
        back_populates="transactions", foreign_keys=[merchant_id]
    )
    callbacks: Mapped[list["Callback"]] = relationship(back_populates="transaction")


class Card(Base, TimestampMixin):
    __tablename__ = "cards"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    card_id: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    merchant_id: Mapped[int] = mapped_column(ForeignKey("merchants.id"), index=True)

    mask: Mapped[str] = mapped_column(String(24))
    holder_name: Mapped[str | None] = mapped_column(String(255), default=None)
    expiry: Mapped[str | None] = mapped_column(String(5), default=None)
    status: Mapped[CardStatus] = mapped_column(enum_column(CardStatus), default=CardStatus.NEW)
    is_payout_card: Mapped[bool] = mapped_column(default=False)
    # The mask cannot be reversed, so the outcome is stored.
    bank_code: Mapped[str | None] = mapped_column(String(8), default=None)
    description: Mapped[str | None] = mapped_column(Text, default=None)

    merchant: Mapped[Merchant] = relationship(back_populates="cards")


class Invoice(Base, TimestampMixin):
    __tablename__ = "invoices"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    merchant_id: Mapped[int] = mapped_column(ForeignKey("merchants.id"), index=True)

    total: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    status: Mapped[InvoiceStatus] = mapped_column(
        enum_column(InvoiceStatus), default=InvoiceStatus.WAITING
    )
    display: Mapped[bool] = mapped_column(default=True)
    save_as_template: Mapped[bool] = mapped_column(default=False)
    allow_installment: Mapped[bool] = mapped_column(default=False)

    recipient_name: Mapped[str | None] = mapped_column(String(255), default=None)
    description: Mapped[str | None] = mapped_column(Text, default=None)
    phone: Mapped[str | None] = mapped_column(String(32), default=None)
    email: Mapped[str | None] = mapped_column(String(255), default=None)
    tin: Mapped[str | None] = mapped_column(String(16), default=None)
    contract_number: Mapped[str | None] = mapped_column(String(64), default=None)
    merchant_order_id: Mapped[str | None] = mapped_column(String(255), default=None)
    period_from: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=None)
    period_to: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=None)


class Callback(Base, TimestampMixin):
    __tablename__ = "callbacks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    transaction_id: Mapped[int] = mapped_column(ForeignKey("transactions.id"), index=True)

    target_url: Mapped[str] = mapped_column(String(512))
    attempt: Mapped[int] = mapped_column(Integer, default=1)
    status: Mapped[CallbackStatus] = mapped_column(
        enum_column(CallbackStatus), default=CallbackStatus.PENDING
    )

    payload_data: Mapped[str] = mapped_column(Text)
    payload_signature: Mapped[str] = mapped_column(String(64))
    decoded_payload: Mapped[dict[str, Any]] = mapped_column(JSON)

    response_status: Mapped[int | None] = mapped_column(Integer, default=None)
    response_body: Mapped[str | None] = mapped_column(Text, default=None)
    error: Mapped[str | None] = mapped_column(Text, default=None)
    duration_ms: Mapped[int | None] = mapped_column(Integer, default=None)
    delivered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=None)

    transaction: Mapped[Transaction] = relationship(back_populates="callbacks")


class BalanceEntry(Base, TimestampMixin):
    __tablename__ = "balance_entries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    merchant_id: Mapped[int] = mapped_column(ForeignKey("merchants.id"), index=True)
    transaction_id: Mapped[int | None] = mapped_column(
        ForeignKey("transactions.id"), default=None, index=True
    )

    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    balance_after: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    kind: Mapped[str] = mapped_column(String(32))
    description: Mapped[str | None] = mapped_column(Text, default=None)


class RequestLog(Base, TimestampMixin):
    __tablename__ = "request_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    trace_id: Mapped[str] = mapped_column(String(32), index=True)
    merchant_id: Mapped[int | None] = mapped_column(
        ForeignKey("merchants.id"), default=None, index=True
    )

    method: Mapped[str] = mapped_column(String(8))
    path: Mapped[str] = mapped_column(String(255), index=True)
    status_code: Mapped[int] = mapped_column(Integer)
    duration_ms: Mapped[int] = mapped_column(Integer)

    raw_data: Mapped[str | None] = mapped_column(Text, default=None)
    raw_signature: Mapped[str | None] = mapped_column(String(64), default=None)
    signature_valid: Mapped[bool | None] = mapped_column(default=None)
    request_payload: Mapped[dict[str, Any] | None] = mapped_column(JSON, default=None)
    response_payload: Mapped[dict[str, Any] | None] = mapped_column(JSON, default=None)


class Notification(Base, TimestampMixin):
    """A captured invoice send. Nothing is delivered."""

    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    invoice_id: Mapped[int] = mapped_column(ForeignKey("invoices.id"), index=True)

    channel: Mapped[str] = mapped_column(String(16))
    recipient: Mapped[str] = mapped_column(String(255))
    subject: Mapped[str | None] = mapped_column(String(255), default=None)
    body: Mapped[str] = mapped_column(Text)
    trace_id: Mapped[str] = mapped_column(String(32), index=True)


class B2BPayment(Base, TimestampMixin):
    """Bank transfers. Separate lifecycle and webhook shape from Transaction."""

    __tablename__ = "b2b_payments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    merchant_id: Mapped[int] = mapped_column(ForeignKey("merchants.id"), index=True)
    order_id: Mapped[str] = mapped_column(String(255), index=True)

    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    description: Mapped[str] = mapped_column(String(255))
    status: Mapped[B2BStatus] = mapped_column(enum_column(B2BStatus), default=B2BStatus.PENDING)
    bulk_id: Mapped[str | None] = mapped_column(String(32), default=None)

    payee_iban: Mapped[str] = mapped_column(String(34))
    payee_name: Mapped[str] = mapped_column(String(255))
    payee_tin: Mapped[str] = mapped_column(String(16))
    bank_code: Mapped[str] = mapped_column(String(16))
    bank_name: Mapped[str | None] = mapped_column(String(255), default=None)

    email: Mapped[str | None] = mapped_column(String(255), default=None)
    address: Mapped[str | None] = mapped_column(String(512), default=None)
    additional_info: Mapped[str | None] = mapped_column(Text, default=None)
    bulk_description: Mapped[str | None] = mapped_column(Text, default=None)

    webhook_url: Mapped[str | None] = mapped_column(String(512), default=None)
    webhook_sent: Mapped[bool] = mapped_column(default=False)
    error_message: Mapped[str | None] = mapped_column(Text, default=None)
    trace_id: Mapped[str] = mapped_column(String(32), index=True)
