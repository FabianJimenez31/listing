# Feature Specification: 006-cobro-tours-wompi

**Feature Branch**: `feature/006-cobro-tours-wompi`

**Created**: 2026-08-22

**Status**: Draft

**Input**: User description: "Desde el admin vamos a cobrar 50 mil pesos por tour que se haga.
Maximo 10 fotos." Decisiones del dueño: cobra TODO tour nuevo (manual o IA); un pago habilita
un tour hasta 10 escenas; pasarela Wompi Colombia Widget Checkout Web en produccion.

## Resumen

Monetizacion de la creacion de tours virtuales. Ningun tour nuevo se crea sin un pago previo
aprobado de **$50.000 COP** procesado por **Wompi**. El pago queda asociado al inmueble o
proyecto y se consume al crear el tour. Tope duro de 10 escenas por tour. Los tours creados
antes del lanzamiento quedan como estan (abuelados).

## Requisitos funcionales

- **FR-601**: Crear un tour DEBE requerir un pago `approved` de $50.000 COP sin consumir para
  esa entidad; sin el pago la API responde **402 Payment Required**.
- **FR-602**: El pago se realiza con el Widget Checkout Web de Wompi (script v2) dentro del
  panel; el monto es `amountInCents = precio * 100`.
- **FR-603**: La integridad DEBE firmarse con SHA256(`reference + amountInCents + currency +
  secret`) usando el secreto de integridad del comercio.
- **FR-604**: La confirmacion NUNCA confia solo en el cliente: el backend consulta
  `GET /v1/transactions/{id}` de Wompi y exige `APPROVED`, referencia propia y monto exacto.
- **FR-605**: Webhook `POST /tour-billing/webhook` valida la firma `W-Signature`
  (SHA256 de valores de propiedades + timestamp + secreto de eventos) y actualiza estados de
  forma idempotente.
- **FR-606**: Un pago aprobado se CONSUME al crear el tour (queda ligado por `tour_id`); no
  reutilizable para otro tour ni entidad.
- **FR-607**: Todo tour tiene tope duro de **10 escenas** (subida manual y generacion IA);
  exceder responde 422.
- **FR-608**: Si Wompi no esta configurado (llaves ausentes), la creacion de tours queda
  deshabilitada con aviso claro y los pagos no se ofrecen (rollout seguro).
- **FR-609**: Pagos pendientes pueden pagarse despues (misma referencia); pagos rechazados
  permiten reintentar con nueva referencia.
- **FR-610** (decision del dueno, 2026-08-22): con facturacion activa, TODA mutacion de
  un tour (subir/editar/borrar/reordenar escenas, hotspots, publicar) exige credito
  aprobado vigente para la entidad — incluidos los tours pre-existentes al lanzamiento,
  que dejan de estar abuelados. Lectura permanece abierta. Un pago unico cubre creacion
  y las hasta 10 escenas del tour.

## Non-functional

- **NFR-601**: Secretos solo en `.env` (git-ignored); al frontend nunca sale mas que la
  public key y la firma de integridad del intento.
- **NFR-602**: La tabla de pagos guarda traza completa (referencia, id transaccion Wompi,
  timestamps) para conciliacion.

## Open Questions

- Ninguna abierta; llaves de produccion las entrega el dueno en `.env` cuando pase a cobros
  reales.
