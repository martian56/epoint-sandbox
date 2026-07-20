"""Balance effects of a transaction.

Commission posts as its own negative row, matching epoint's payment history.
"""

from decimal import ROUND_HALF_UP, Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from epoint_sandbox.config import get_settings
from epoint_sandbox.models import BalanceEntry, Merchant, Transaction

CENTS = Decimal("0.01")


class Kind:
    PAYMENT = "payment"
    COMMISSION = "commission"
    SPLIT_OUT = "split_out"
    SPLIT_IN = "split_in"
    REFUND = "refund"
    PAYOUT = "payout"
    REVERSAL = "reversal"


def commission_for(amount: Decimal) -> Decimal:
    rate = Decimal(str(get_settings().commission_rate))
    return (amount * rate).quantize(CENTS, rounding=ROUND_HALF_UP)


def _post(
    session: Session,
    merchant_id: int,
    amount: Decimal,
    kind: str,
    transaction: Transaction | None,
    description: str | None = None,
) -> BalanceEntry:
    running = available_balance(session, merchant_id)

    entry = BalanceEntry(
        merchant_id=merchant_id,
        transaction_id=transaction.id if transaction else None,
        amount=amount,
        balance_after=running + amount,
        kind=kind,
        description=description,
    )
    session.add(entry)
    session.flush()
    return entry


def settle_payment(session: Session, transaction: Transaction) -> list[BalanceEntry]:
    """Credit the merchant, take commission, route any split share."""
    entries: list[BalanceEntry] = []
    merchant_share = transaction.amount

    if transaction.split_merchant_id and transaction.split_amount:
        merchant_share -= transaction.split_amount
        entries.append(
            _post(
                session,
                transaction.split_merchant_id,
                transaction.split_amount,
                Kind.SPLIT_IN,
                transaction,
                f"Split from {transaction.order_id}",
            )
        )
        entries.append(
            _post(
                session,
                transaction.merchant_id,
                -transaction.split_amount,
                Kind.SPLIT_OUT,
                transaction,
                f"Split to merchant {transaction.split_merchant_id}",
            )
        )

    entries.insert(
        0,
        _post(
            session,
            transaction.merchant_id,
            transaction.amount,
            Kind.PAYMENT,
            transaction,
            transaction.description,
        ),
    )

    commission = commission_for(merchant_share)
    if commission > 0:
        entries.append(
            _post(
                session,
                transaction.merchant_id,
                -commission,
                Kind.COMMISSION,
                transaction,
                f"Commission on {transaction.order_id}",
            )
        )

    return entries


def settle_debit(
    session: Session,
    merchant: Merchant,
    amount: Decimal,
    kind: str,
    transaction: Transaction | None = None,
    description: str | None = None,
) -> BalanceEntry:
    return _post(session, merchant.id, -amount, kind, transaction, description)


def available_balance(session: Session, merchant_id: int) -> Decimal:
    latest = session.scalar(
        select(BalanceEntry)
        .where(BalanceEntry.merchant_id == merchant_id)
        .order_by(BalanceEntry.id.desc())
        .limit(1)
    )
    return Decimal(str(latest.balance_after)) if latest else Decimal("0.00")
