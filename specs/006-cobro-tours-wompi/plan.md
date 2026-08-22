# Implementation Plan: 006-cobro-tours-wompi

**Branch**: `feature/006-cobro-tours-wompi` | **Date**: 2026-08-22 | **Spec**: [spec.md](spec.md)

## Summary

Pasarela Wompi (Widget Checkout Web) para cobrar $50.000 COP por cada tour nuevo. Tabla
`tour_payments`, endpoints de billing con firma de integridad y verificacion server-side,
gate 402 en la creacion de tours, tope de 10 escenas, paywall en el panel.

## Technical Context

- Wompi Widget v2 (`https://cdn.wompi.co/widget/js/v2.js`) + API REST
  (`{WOMPI_API}/v1/transactions/{id}`); base configurable production/sandbox.
- Backend FastAPI + SQLAlchemy; migracion Alembic nueva; frontend React en el panel.

## Design

1. **Modelo** `tour_payments`: id, user_id, entity_type(property|project), entity_id,
   amount_in_cents, currency(COP), status(pending|approved|declined|voided), reference unico,
   wompi_transaction_id, tour_id (consumo), paid_at, created_at, updated_at.
2. **Endpoints** bajo `/api/v1/tour-billing`:
   - `GET  /config` → { enabled, public_key, amount_in_cents, currency }
   - `POST /intent` {entity_type, entity_id} → valida permisos (patron `_guard_parent`),
     reusa intent pending existente o crea uno nuevo; responde payload del widget incl.
     `integrity` = SHA256(ref+cents+currency+secret).
   - `POST /confirm` {reference, transaction_id?} → si falta id, se resuelve listando por
     referencia; verifica APPROVED/referencia/monto contra la API de Wompi y aprueba.
   - `POST /webhook` → valida `W-Signature`; actualizacion idempotente.
3. **Gate**: `create_tour` exige pago approved sin consumir para la entidad; lo consume.
   Sin llaves Wompi: 402 con mensaje "pagos no configurados" y widget oculto (FR-608).
4. **Tope escenas**: constante `MAX_SCENES_PER_TOUR=10` verificada en upload y generate.
5. **Frontend**: `TourEditor` sin tour muestra paywall (precio, beneficios, boton Pagar);
   carga perezosa del script Wompi; al `open()` exitoso confirma via `/confirm` y recarga.
6. **Variables**: `WOMPI_PUBLIC_KEY`, `WOMPI_INTEGRITY_SECRET`, `WOMPI_EVENTS_SECRET`,
   `WOMPI_ENV=production|test`, `TOUR_PRICE_COP=50000`.

## Verification

- Unit: vector determinista de firma de integridad; validacion de webhook valido/invalido.
- Integracion: crear tour sin pago → 402; con pago aprobado mockeado → 201 y consumo;
- 11a escena → 422. Suite completa verde + build de Vite.
