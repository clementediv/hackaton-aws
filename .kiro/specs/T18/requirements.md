# T18 · API HTTP v2

[[plan-chatbot-desplegado]]: POST /casos, /chat, /casos/{id}/invitacion,
/casos/{id}/autorizacion y GET /casos/{id}. Pydantic extra=forbid, DV válido,
fuentes obligatorias, aceptación antes de autorizar, revocar al declinar.
Errores genéricos 400/401/403/404/503 sin detalles internos.

La API key es de integración demo. x-run identifica el ámbito de la solicitud;
no constituye autenticación ciudadana y requiere gateway de identidad para uso real.
