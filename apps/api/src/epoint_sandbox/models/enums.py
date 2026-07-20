from enum import StrEnum


class TransactionStatus(StrEnum):
    NEW = "new"
    SUCCESS = "success"
    FAILED = "failed"
    ERROR = "error"
    RETURNED = "returned"
    SERVER_ERROR = "server_error"


class CardStatus(StrEnum):
    NEW = "new"
    ACTIVE = "active"
    PENDING = "pending"
    REJECTED = "rejected"
    EXPIRED = "expired"
    SESSION_EXPIRED = "session_expired"


class InvoiceStatus(StrEnum):
    WAITING = "waiting_for_payment"
    PAID = "paid"
    CANCELED = "canceled"


class CallbackStatus(StrEnum):
    PENDING = "pending"
    DELIVERED = "delivered"
    FAILED = "failed"
    DROPPED = "dropped"


class OperationCode(StrEnum):
    CARD_REGISTRATION = "001"
    PAYMENT = "100"
    REGISTRATION_WITH_PAYMENT = "200"


class B2BStatus(StrEnum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
