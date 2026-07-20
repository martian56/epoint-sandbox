from decimal import Decimal, InvalidOperation

from sqlalchemy import select
from sqlalchemy.orm import Session

from epoint_sandbox.api.deps import SignedRequest
from epoint_sandbox.api.errors import EpointError
from epoint_sandbox.config import get_settings
from epoint_sandbox.models import BalanceEntry, Merchant, Transaction, TransactionStatus
from epoint_sandbox.services import ids

SUPPORTED_CURRENCIES = {"AZN", "USD", "EUR", "RUB"}
AZN_ONLY = {"AZN"}


def parse_amount(raw: object, field: str = "amount") -> Decimal:
    try:
        amount = Decimal(str(raw))
    except (InvalidOperation, TypeError) as exc:
        raise EpointError(f"{field} is not a valid number") from exc
    if amount <= 0:
        raise EpointError(f"{field} must be greater than zero")
    return amount.quantize(Decimal("0.01"))


def validate_currency(currency: str, allowed: set[str] = SUPPORTED_CURRENCIES) -> str:
    upper = currency.upper()
    if upper not in allowed:
        raise EpointError(
            f"Unsupported currency: {currency}. Allowed: {', '.join(sorted(allowed))}"
        )
    return upper


def create_transaction(
    session: Session,
    request: SignedRequest,
    *,
    endpoint: str,
    trace_id: str,
    allowed_currencies: set[str] = SUPPORTED_CURRENCIES,
    default_currency: str | None = None,
    require_language: bool = True,
) -> Transaction:
    required = ["amount", "order_id"] if default_currency else ["amount", "currency", "order_id"]
    # Documented required everywhere except token/widget, so refuse rather than default it.
    if require_language:
        required.append("language")
    request.require(*required)

    amount = parse_amount(request.get("amount"))
    currency = validate_currency(str(request.get("currency", default_currency)), allowed_currencies)
    order_id = str(request.get("order_id"))

    if len(order_id) > 255:
        raise EpointError("order_id must be 255 characters or fewer")

    existing = session.scalar(
        select(Transaction).where(
            Transaction.merchant_id == request.merchant.id,
            Transaction.order_id == order_id,
        )
    )
    if existing is not None:
        raise EpointError(f"order_id {order_id} has already been used")

    transaction = Transaction(
        transaction_id=ids.placeholder(),
        merchant_id=request.merchant.id,
        order_id=order_id,
        amount=amount,
        currency=currency,
        description=request.get("description"),
        language=str(request.get("language", "az")),
        status=TransactionStatus.NEW,
        endpoint=endpoint,
        checkout_token=ids.checkout_token(),
        success_redirect_url=request.get("success_redirect_url"),
        error_redirect_url=request.get("error_redirect_url"),
        other_attr=request.get("other_attr"),
        trace_id=trace_id,
    )
    session.add(transaction)
    session.flush()
    transaction.transaction_id = ids.transaction_id(transaction.id)
    session.flush()
    return transaction


def checkout_url(transaction: Transaction) -> str:
    return f"{get_settings().public_base_url}/checkout/{transaction.checkout_token}"


def current_balance(session: Session, merchant_id: int) -> Decimal:
    latest = session.scalar(
        select(BalanceEntry)
        .where(BalanceEntry.merchant_id == merchant_id)
        .order_by(BalanceEntry.id.desc())
        .limit(1)
    )
    return latest.balance_after if latest else Decimal("0.00")


def post_balance(
    session: Session,
    merchant: Merchant,
    amount: Decimal,
    kind: str,
    *,
    transaction: Transaction | None = None,
    description: str | None = None,
) -> BalanceEntry:
    balance_after = current_balance(session, merchant.id) + amount
    entry = BalanceEntry(
        merchant_id=merchant.id,
        transaction_id=transaction.id if transaction else None,
        amount=amount,
        balance_after=balance_after,
        kind=kind,
        description=description,
    )
    session.add(entry)
    session.flush()
    return entry
