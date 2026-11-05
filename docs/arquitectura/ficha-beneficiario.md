---
tipo: implementacion
fecha: 2026-10-15
autor: Clemente (Claude)
---
# Ficha del beneficiario y fuente única de contacto

## Problema
Mi Gobierno y el colador mostraban datos de contacto distintos para la misma persona. Mi Gobierno armaba el email a partir del nombre y usaba un teléfono fijo (`+56 9 0000 0000`). El colador usaba `persona.<RUN>@example.com` y `SIM-TEL-<RUN>`, vacíos en el 15% y el 10% de las personas. Por eso, alguien sin email, que el colador había pasado directo a la etapa de llamada, aparecía con email en Mi Gobierno.

## Solución: una sola fuente
- **Formato en la capa de contacto** (`src/app/ruta/contacto.py`): email legible `nombre.apellido@example.com`, sin tildes y en el dominio reservado, y teléfono `+56 9 0000 xxxx`, donde el bloque `0000` lo marca como ficticio. Se mantienen la misma semilla y las mismas personas sin email o sin teléfono.
- **`ruta.ficha.contact_for(run, perfil)`** es la única forma de leer el contacto de una persona:
  1. si la persona está en la campaña simulada, devuelve **el contacto que usó el colador**;
  2. si no, la capa sintética (Región Metropolitana), la misma que generaría el colador.
- **Mi Gobierno** usa `contact_for` y muestra «Sin información» cuando falta un canal.
- `data/synthetic/contacto.csv` se regeneró con el formato nuevo.

Las campañas que ya estaban guardadas en una base SQLite conservan el contacto con el que se crearon. Para ver el formato nuevo en el embudo, hay que iniciar una simulación nueva.

## Ficha del beneficiario
Vista **«Ficha del beneficiario»** dentro de **«Vista ejecutivo»** en la app (`src/app/ui_ficha.py`). Es para ejecutivos y trabajadores sociales: reúne en una página todo lo que se sabe de una persona, sin escribir nada.

Desde el 15-10, la navegación principal reúne todas las herramientas de gestión en «Vista ejecutivo»: Mapa de calor y campañas, Detectar e invitar, Ficha del beneficiario, Atención del caso y Medición. El selector interno ejecuta solo la herramienta elegida y conserva los flujos existentes. Las sesiones que estaban en una de las antiguas entradas se redirigen a su herramienta dentro de «Vista ejecutivo».

| Sección | Fuente |
|---|---|
| Alerta de beneficio (nivel máximo si no respondió a ningún canal) | Colador |
| Identidad | Registro Civil del dataset A |
| Contacto, con su origen | `contact_for` |
| Consentimiento: invitación y autorización | Casos (SQLite) |
| Evaluación PGU y jubilación, con requisitos y fuentes | Motor de reglas |
| Ruta del trámite y próximo paso | `rutas.py` |
| Documentos y declaración | Mi Gobierno, **solo con autorización** |
| Etapa, intentos y eventos del colador | Colador |
| Historial por canal | Casos |

La lógica está en `src/app/ruta/ficha.py` (`build`), separada de la vista, para poder probarla y reutilizarla, por ejemplo en la API.

## Verificación
- `uv run --group app pytest`: 145 pruebas (6 nuevas en `tests/test_ficha.py`). Cubren:
  - formato y canales vacíos;
  - la misma fuente de contacto en todas las vistas;
  - que el contacto del colador gane una vez que la persona entra en la campaña;
  - documentos ocultos sin autorización;
  - el nivel de alerta;
  - que la vista se dibuje.
- `src/app/verificar.py`: TODO OK.
