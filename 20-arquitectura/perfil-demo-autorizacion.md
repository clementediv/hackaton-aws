---
tipo: implementacion
fecha: 2026-10-16
---
# Perfil de demostración con autorización al ingresar

Solicitud del usuario: crear el acceso `123456789` con clave `demo2026` y pedir permiso de uso de datos al entrar a [[mi-gobierno]].

La cuenta se identifica como **Persona De Prueba**. Se aceptan `123456789`, `12345678-9` y `12.345.678-9` en el acceso ficticio. Ese identificador no tiene un dígito verificador válido: la excepción se limita a esta cuenta explícita en `ruta/demo_auth.authenticate`, siempre que exista en la lista permitida y con la clave correcta. `normalize_run` y la API conservan su validación ordinaria.

## Recorrido

1. Inicio → Revisar mis requisitos, o pestaña Mi Gobierno.
2. Ingresar `123456789` y `demo2026`.
3. Se muestra **Autoriza el uso de tus datos**, con fuentes a consultar y permiso revocable. La casilla inicia desmarcada y Activar Mi Gobierno está deshabilitado.
4. Solo después de marcar la autorización y activarla se muestran evaluación, documentos y pasos personalizados.
5. Para esta cuenta, cada nuevo ingreso correcto desactiva el permiso persistido anterior para volver a demostrar el consentimiento. Se conserva el historial y los documentos; las demás cuentas mantienen su comportamiento actual.

La nueva identidad es ficticia y nace sin registros RSH, residencia, previsión ni información laboral. Tras autorizar, el motor indica antecedentes faltantes; no se inventa elegibilidad ni se crean documentos validados.

## Implementación y alcance

- `ruta/demo_profiles.py` agrega la identidad únicamente al acceso ciudadano y al chat personal. Devuelve una copia nueva de sus datos en cada carga.
- `ui_government` incorpora el diagnóstico de esa cuenta para login/vistas y conserva la pantalla de consentimiento existente, con título explícito para la cuenta nueva.
- El chat público puede revisar esa identidad solo con sesión y autorización, usando el mismo cargador ciudadano.
- Dataset A conserva sus 500 perfiles, campañas y conteos de verificación. No se crea una identidad en ClaveÚnica ni un perfil en AWS.

## Verificación

Cinco regresiones cubren formatos, contraseña incorrecta, pertenencia a la lista permitida, validación estricta ordinaria, aislamiento del dataset, revisión PGU y flujo de interfaz ingreso → permiso → datos → salida → nuevo permiso. Suite completa: 310 pruebas pasan, ocho evals reales excluidas; verificador de 500 perfiles TODO OK. No se usan credenciales reales ni se envían correos.

Chrome sobre la aplicación de localhost:8501 confirma ingreso con las credenciales solicitadas, título de autorización visible, casilla desmarcada y botón de activación deshabilitado. La prueba visual termina sin conceder el permiso, dejando listo el primer ingreso del usuario.
