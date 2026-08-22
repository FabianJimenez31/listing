"""Wompi-backed billing for virtual-tour creation.

Flow: panel asks for an intent (reference + integrity signature) -> Wompi widget
collects the payment -> backend verifies the transaction against Wompi's API
(never trusting the browser alone) and marks the payment approved -> creating a
tour consumes the approved payment.
"""
from __future__ import annotations

import hashlib
import os
import uuid
from datetime import datetime, timezone

import httpx
from fastapi import APIRouter, Header, HTTPException, Request, status

from src.api.deps import CurrentUser, DB
from src.db.models.project_models import ProjectORM
from src.db.models.property_models import PropertyORM
from src.db.models.tour_payment_models import TourPaymentORM

router = APIRouter(tags=["tour-billing"])

WOMPI_API = {
    "production": "https://production.wompi.co/v1",
    "test": "https://sandbox.wompi.co/v1",
}


def _env(name: str, default: str = "") -> str:
    return os.environ.get(name, default).strip()


def price_in_cents() -> int:
    try:
        return int(float(_env("TOUR_PRICE_COP", "50000")) * 100)
    except ValueError:
        return 5_000_000


def billing_enabled() -> bool:
    return bool(_env("WOMPI_PUBLIC_KEY")) and bool(_env("WOMPI_INTEGRITY_SECRET"))


def wompi_base() -> str:
    return WOMPI_API.get(_env("WOMPI_ENV", "production"), WOMPI_API["production"])


def integrity_signature(reference: str, amount_in_cents: int, currency: str) -> str:
    """Wompi checkout integrity: SHA256 of ref+cents+currency+secret."""
    secret = _env("WOMPI_INTEGRITY_SECRET")
    raw = f"{reference}{amount_in_cents}{currency}{secret}"
    return hashlib.sha256(raw.encode()).hexdigest()


def _guard_entity(entity_type: str, entity_id: str, current_user: CurrentUser, db) -> None:
    model = PropertyORM if entity_type == "properties" else ProjectORM
    owner_column = model.owner_id if hasattr(model, "owner_id") else model.agency_id
    obj = db.query(model).filter(model.id == entity_id).first()
    if not obj:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Entidad no encontrada")
    is_staff = getattr(current_user, "role", None) in ("admin", "staff")
    if not is_staff and getattr(obj, owner_column.key, None) != current_user.id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "No autorizado")


def _unconsumed_payment(db, entity_type: str, entity_id: str):
    return (
        db.query(TourPaymentORM)
        .filter(
            TourPaymentORM.entity_type == entity_type,
            TourPaymentORM.entity_id == entity_id,
            TourPaymentORM.status == "approved",
            TourPaymentORM.tour_id.is_(None),
        )
        .first()
    )


@router.get("/tour-billing/config")
def billing_config():
    cents = price_in_cents()
    return {
        "enabled": billing_enabled(),
        "public_key": _env("WOMPI_PUBLIC_KEY") or None,
        "amount_in_cents": cents,
        "currency": "COP",
    }


@router.post("/tour-billing/intent")
def create_intent(
    body: dict,
    current_user: CurrentUser,
    db: DB,
):
    if not billing_enabled():
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "Pagos no configurados")
    entity_type = body.get("entity_type")
    entity_id = body.get("entity_id")
    if entity_type not in ("properties", "projects") or not entity_id:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "entity_type/entity_id requeridos")
    _guard_entity(entity_type, entity_id, current_user, db)

    existing_approved = _unconsumed_payment(db, entity_type, entity_id)
    if existing_approved:
        return {"already_paid": True, "reference": existing_approved.reference}

    payment = (
        db.query(TourPaymentORM)
        .filter(
            TourPaymentORM.entity_type == entity_type,
            TourPaymentORM.entity_id == entity_id,
            TourPaymentORM.user_id == current_user.id,
            TourPaymentORM.status == "pending",
        )
        .order_by(TourPaymentORM.created_at.desc())
        .first()
    )
    if not payment:
        payment = TourPaymentORM(
            id=str(uuid.uuid4()),
            user_id=current_user.id,
            entity_type=entity_type,
            entity_id=entity_id,
            amount_in_cents=price_in_cents(),
            currency="COP",
            status="pending",
            reference=f"tour-{uuid.uuid4().hex[:20]}",
        )
        db.add(payment)
        db.commit()

    cents = payment.amount_in_cents
    return {
        "already_paid": False,
        "reference": payment.reference,
        "amount_in_cents": cents,
        "currency": payment.currency,
        "public_key": _env("WOMPI_PUBLIC_KEY"),
        "integrity": integrity_signature(payment.reference, cents, payment.currency),
        "widget_url": "https://checkout.wompi.co/widget/",
    }


def _fetch_transaction(transaction_id: str) -> dict:
    url = f"{wompi_base()}/transactions/{transaction_id}"
    response = httpx.get(url, timeout=15)
    if response.status_code != 200:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, "No se pudo verificar la transaccion")
    return response.json().get("data", {})


def apply_transaction(payment: TourPaymentORM, transaction: dict) -> TourPaymentORM:
    expected_ref = transaction.get("reference")
    if expected_ref != payment.reference:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "La transaccion no corresponde a esta referencia")
    if int(transaction.get("amount_in_cents", -1)) != payment.amount_in_cents:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "El monto de la transaccion no coincide")
    wompi_status = str(transaction.get("status", "")).upper()
    mapping = {"APPROVED": "approved", "DECLINED": "declined", "VOIDED": "voided", "ERROR": "declined"}
    new_status = mapping.get(wompi_status)
    if new_status is None:
        return payment  # PENDING u otros: no cambia nada todavia
    payment.status = new_status
    payment.wompi_transaction_id = transaction.get("id") or payment.wompi_transaction_id
    if new_status == "approved":
        payment.paid_at = datetime.now(timezone.utc)
    return payment


@router.post("/tour-billing/confirm")
def confirm_payment(body: dict, current_user: CurrentUser, db: DB):
    reference = body.get("reference")
    if not reference:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "reference requerida")
    payment = db.query(TourPaymentORM).filter(TourPaymentORM.reference == reference).first()
    if not payment:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Referencia no encontrada")
    _guard_entity(payment.entity_type, payment.entity_id, current_user, db)

    if payment.status != "approved":
        transaction_id = body.get("transaction_id")
        if not transaction_id:
            # Resolver la transaccion mas reciente por referencia en Wompi.
            listing = httpx.get(
                f"{wompi_base()}/transactions?reference={reference}", timeout=15
            )
            items = (listing.json().get("data") or []) if listing.status_code == 200 else []
            if not items:
                raise HTTPException(status.HTTP_402_PAYMENT_REQUIRED, "Pago aun no registrado en Wompi")
            transaction_id = items[-1]["id"]
        transaction = _fetch_transaction(str(transaction_id))
        apply_transaction(payment, transaction)
        db.commit()

    return {
        "status": payment.status,
        "already_paid": payment.status == "approved" and payment.tour_id is None,
        "entity_type": payment.entity_type,
        "entity_id": payment.entity_id,
    }


def _resolve_event_value(data: dict, path: str):
    value: object = data
    for part in path.split("."):
        if not isinstance(value, dict):
            return None
        value = value.get(part)
    return value


def event_signature_valid(payload: dict, signature_header: str, secret: str) -> bool:
    """Valida 'W-Signature': SHA256(valores concatenados + timestamp + secreto)."""
    import json as _json

    try:
        header = _json.loads(signature_header)
    except ValueError:
        return False
    properties = header.get("properties") or []
    timestamp = str(header.get("timestamp", ""))
    checksum = str(header.get("signature", ""))
    values = "".join(str(_resolve_event_value(payload.get("data", {}), prop)) for prop in properties)
    computed = hashlib.sha256(f"{values}{timestamp}{secret}".encode()).hexdigest()
    return computed == checksum


@router.post("/tour-billing/webhook")
async def wompi_webhook(request: Request, w_signature: str | None = Header(default=None), db: DB = None):
    secret = _env("WOMPI_EVENTS_SECRET")
    payload = await request.json()
    if not secret or not w_signature or not event_signature_valid(payload, w_signature, secret):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Firma invalida")

    event = payload.get("event")
    data = payload.get("data", {})
    if event != "transaction.updated":
        return {"received": True}
    reference = data.get("reference")
    payment = db.query(TourPaymentORM).filter(TourPaymentORM.reference == reference).first()
    if not payment:
        return {"received": True}
    apply_transaction(payment, data)
    db.commit()
    return {"received": True}
