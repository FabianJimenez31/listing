# Tasks: 006-cobro-tours-wompi

Convencion: `[x]` hecho · `[/]` en curso · `[ ]` pendiente.

- [x] T-101 Modelo TourPaymentORM + registro + migracion Alembic c4e8f2a6b9d3.
- [x] T-102 Router tour_billing: config/intent (firma SHA256)/confirm (verificacion API)/webhook.
- [x] T-103 Gate 402 en create_tour + consumo del pago; tope 10 escenas en upload/generate.
- [x] T-104 Tests unitarios e integracion de billing/gate/tope.
- [x] T-201 Frontend: api/tours.js billing; paywall + widget v2 en TourEditor.
- [/] T-202 .env.example listo; falta .env con llaves reales + .env con llaves de produccion (entregadas por el dueno).
- [x] T-105 FR-610: gates 402 en los 7 endpoints de mutacion + credit-status + candado en panel. Abuelados anulados por decision del dueno.
- [ ] T-301 Gates verdes, deploy backend+frontend, verificacion en produccion.
- [ ] T-302 Prueba de compra real con dataphone/nequi y conciliacion.
- [x] T-303 Corregir orden FK al consumir el pago y recuperar compra aprobada de inmueble 1000000070.
