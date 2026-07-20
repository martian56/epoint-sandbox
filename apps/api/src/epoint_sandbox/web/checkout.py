from datetime import UTC, datetime
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select

from epoint_sandbox.api.deps import SessionDep
from epoint_sandbox.models import Card, CardStatus, Transaction, TransactionStatus
from epoint_sandbox.models.enums import OperationCode
from epoint_sandbox.services import callbacks, ids, magic_cards, settlement

router = APIRouter(prefix="/checkout", tags=["checkout"])
templates = Jinja2Templates(directory=Path(__file__).parent / "templates")

STRINGS = {
    "az": {
        "title": "Ödəniş təfərrüatları",
        "amount": "Ödəniş məbləği",
        "merchant": "Satıcı",
        "tin": "VÖEN",
        "phone": "Əlaqə nömrəsi",
        "holder": "Ad, Soyad",
        "number": "Kartın nömrəsi",
        "month": "Ay",
        "year": "İl",
        "cvv": "CVV",
        "submit": "Təsdiq",
        "invalid": "Kart məlumatları yanlışdır",
        "testCards": "Test kartları",
    },
    "en": {
        "title": "Payment details",
        "amount": "Payment amount",
        "merchant": "Merchant",
        "tin": "TIN",
        "phone": "Contact number",
        "holder": "Cardholder name",
        "number": "Card number",
        "month": "MM",
        "year": "YY",
        "cvv": "CVV",
        "submit": "Confirm",
        "invalid": "Card details are invalid",
        "testCards": "Test cards",
    },
    "ru": {
        "title": "Детали платежа",
        "amount": "Сумма платежа",
        "merchant": "Продавец",
        "tin": "ИНН",
        "phone": "Контактный номер",
        "holder": "Имя, Фамилия",
        "number": "Номер карты",
        "month": "ММ",
        "year": "ГГ",
        "cvv": "CVV",
        "submit": "Подтвердить",
        "invalid": "Неверные данные карты",
        "testCards": "Тестовые карты",
    },
}


def _load(session: SessionDep, token: str) -> Transaction:
    transaction = session.scalar(select(Transaction).where(Transaction.checkout_token == token))
    if transaction is None:
        raise HTTPException(status_code=404, detail="Unknown or expired checkout session")
    return transaction


def _context(transaction: Transaction, error: str | None = None) -> dict[str, object]:
    language = transaction.language if transaction.language in STRINGS else "az"
    return {
        "t": STRINGS[language],
        "transaction": transaction,
        "merchant": transaction.merchant,
        "error": error,
        "cards": magic_cards.catalogue(),
    }


def _settle_card(
    session: SessionDep,
    transaction: Transaction,
    digits: str,
    holder: str,
    month: str,
    year: str,
    *,
    approved: bool,
) -> None:
    """Attach the card from a registration flow. Usable only once approved."""
    if transaction.card_id is None:
        return

    card = session.get(Card, transaction.card_id)
    if card is None:
        return

    card.mask = magic_cards.mask(digits)
    card.holder_name = holder or None
    card.expiry = f"{month}/{year}" if month and year else None
    card.bank_code = magic_cards.resolve(digits).bank_code or None
    card.status = CardStatus.ACTIVE if approved else CardStatus.REJECTED


@router.get("/{token}", response_class=HTMLResponse)
async def show(request: Request, session: SessionDep, token: str) -> HTMLResponse:
    transaction = _load(session, token)
    if transaction.status is not TransactionStatus.NEW:
        return templates.TemplateResponse(request, "result.html", _context(transaction))
    return templates.TemplateResponse(request, "checkout.html", _context(transaction))


@router.post("/{token}", response_model=None)
async def pay(
    request: Request,
    session: SessionDep,
    token: str,
    card_number: Annotated[str, Form()],
    card_holder: Annotated[str, Form()] = "",
    month: Annotated[str, Form()] = "",
    year: Annotated[str, Form()] = "",
) -> HTMLResponse | RedirectResponse:
    transaction = _load(session, token)
    if transaction.status is not TransactionStatus.NEW:
        return templates.TemplateResponse(request, "result.html", _context(transaction))

    digits = magic_cards.normalize(card_number)
    if len(digits) != 16:
        context = _context(transaction, error=str(STRINGS[transaction.language]["invalid"]))
        return templates.TemplateResponse(request, "checkout.html", context, status_code=400)

    outcome = magic_cards.resolve(digits)

    transaction.card_mask = magic_cards.mask(digits)
    transaction.card_name = card_holder or None
    transaction.bank_transaction = ids.bank_transaction_id()
    transaction.bank_code = outcome.bank_code or None
    transaction.message = outcome.message
    transaction.operation_code = OperationCode.PAYMENT.value
    transaction.paid_at = datetime.now(UTC)

    if outcome.timeout:
        transaction.status = TransactionStatus.SERVER_ERROR
    elif outcome.approved:
        transaction.status = TransactionStatus.SUCCESS
        transaction.rrn = ids.rrn()
    else:
        transaction.status = TransactionStatus.FAILED

    _settle_card(session, transaction, digits, card_holder, month, year, approved=outcome.approved)

    # A pre-auth reserves only. Money moves on capture.
    if outcome.approved and transaction.amount > 0 and transaction.endpoint != "pre-auth-request":
        settlement.settle_payment(session, transaction)

    session.flush()

    if not outcome.timeout:
        callbacks.deliver(session, transaction)

    session.commit()

    redirect = (
        transaction.success_redirect_url if outcome.approved else transaction.error_redirect_url
    )
    if redirect:
        return RedirectResponse(redirect, status_code=303)
    return templates.TemplateResponse(request, "result.html", _context(transaction))
