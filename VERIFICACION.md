# Verificación de la entrega

Fecha: 23 de octubre de 2026.

## Resultado

| Capa | Resultado | Alcance |
|---|---:|---|
| Motor JavaScript | 35/35 | Contratos, errores, permisos, confirmaciones, reglas de negocio e idempotencia. |
| Python y API | 43/43 | Ejecutor, sesiones, endpoints mediante TestClient, concurrencia e integración Ollama con proveedor simulado. |
| Interfaz | 42/42 | Navegación, contratos editables, errores, controles, rescate completo, evaluación, exportación y vistas móviles. |

Son **120 comprobaciones automatizadas**, no 120 pruebas contra un LLM real. Se revisaron además capturas de escritorio y móvil. No se detectaron errores JavaScript de página durante el recorrido comprobado.

## Entorno y límites

Python 3.13; Node.js 22; Chromium en modo headless. La política del entorno impedía navegar a archivos o URLs de localhost. Por ello se cargó el mismo HTML mediante `set_content` de Playwright.

La persistencia se comprobó con una implementación de almacenamiento de prueba; también se verificó que la página funcionase sin almacenamiento. No se ha verificado la configuración concreta de almacenamiento de tu navegador.

El puente de la interfaz ejecutó el código Python mediante FastAPI TestClient y un transporte de prueba, no mediante una conexión de red real de Chromium. Las rutas y las respuestas HTTP se probaron en memoria. El servidor debe iniciarse y comprobarse en tu equipo siguiendo `LEEME.md`.

El adaptador Ollama se ensayó con `httpx.MockTransport`. No había un modelo local activo: no se afirma que un modelo real haya resuelto la misión ni que esta integración haya sido comprobada con todos los modelos.

Estas verificaciones no constituyen una auditoría completa de seguridad ni de accesibilidad. La aplicación es una herramienta educativa local.

## Reproducibilidad

Las pruebas de motor y backend se incluyen en el paquete. La lista de las 42 comprobaciones de interfaz está en `verification_results.json`; no es un expediente de la usuaria.

```text
python -m pytest -q
node --test frontend/engine.test.cjs
```
