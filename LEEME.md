# Academia Galáctica de IA · Versión 3

**Tool Use: tu droide propone; tu sistema decide.**

Proyecto educativo parael bootcamp de IA. Ambientación de aventura galáctica inspirada en Star Wars; material no oficial, sin afiliación. Todas las naves, balizas, rutas y operaciones de esta academia son datos ficticios. No hay rescates ni servicios externos reales.

## 1. Empieza por aquí: sin instalar nada

Abre `index.html` con Chrome o Edge. También puedes usar el archivo independiente `academia_tool_use_galactica_v3.html`: es la misma web.

La academia no carga fuentes, imágenes ni librerías de internet. Puedes recorrer las nueve estaciones, editar contratos y llamadas, ver trazas, completar el rescate y corregir la evaluación sin servidor, sin cuenta y sin clave de API. Los enlaces de documentación sí necesitan conexión si decides abrirlos.

La estación **07, Puente Python**, es opcional y requiere iniciar el backend. No impide superar los seis retos del recorrido principal.

### Recorrido

| Estación | Qué haces |
|---|---|
| 00. Centro de mando | Lees la misión y reconoces qué es real y qué se simula. |
| 01. Anatomía de una llamada | Recorres seis etapas: petición, propuesta, controles, ejecución, resultado y respuesta. |
| 02. Contratos | Reparas un JSON Schema y lo contrastas con diez pruebas positivas y negativas. |
| 03. Laboratorio | Editas argumentos, cambias el rol de entrenamiento, provocas errores e inspeccionas cada etapa. |
| 04. Orquestación | Comparas lecturas secuenciales y paralelas, límites de llamadas y reintentos acotados. |
| 05. Seguridad | Distingues una instrucción externa maliciosa de una orden autorizada. |
| 06. Rescate en Dagobah | Reúnes evidencia, eliges una ruta, confirmas la operación y compruebas que el reintento no duplica el despacho. |
| 07. Puente Python | Envías lecturas o cálculos a funciones Python a través de FastAPI. |
| 08. Evaluación | Resuelves doce casos, escribes tus conclusiones y exportas tu expediente. |

No se conceden los retos por visitar una pantalla. Se registran comprobaciones concretas; la evaluación requiere al menos diez aciertos de doce. Los botones de solución son una ayuda de estudio, no un examen vigilado.

## 2. Las tres capas: qué ejecuta realmente cada una

**Web autónoma:** el motor ejecuta JavaScript real sobre datos ficticios. Las propuestas del LLM y las respuestas narrativas son simuladas y deterministas. No hay un modelo descargado ni conectado. Los controles del navegador son didácticos, no una frontera de seguridad frente a su propio usuario.

**Backend local opcional:** ejecuta funciones Python reales. El navegador y FastAPI se comunican por HTTP cuando inicias el servidor en tu equipo. Sigue utilizando datos ficticios. La estación 07 cambia de motor; las otras estaciones continúan siendo simulaciones de navegador para que puedas experimentar libremente.

**Adaptador Ollama opcional:** `ollama_readonly.py` permite usar un modelo local compatible con tool calling desde la terminal. Solo expone consultas y cálculos, nunca despacho de naves ni ejecución de código arbitrario. No está integrado en el chat de la web. Se ha probado con respuestas simuladas del proveedor, no contra un modelo en funcionamiento.

Un JSON bien formado no es lo mismo que una llamada autorizada. El permiso procede del contexto del ejecutor, no de un argumento que escriba el modelo.

## 3. Python en Windows

Necesitas Python 3.11 o posterior. El entorno de comprobación utilizó Python 3.13. La instalación inicial de dependencias requiere internet.

Extrae el ZIP completo. No ejecutes archivos desde dentro de la vista comprimida.

La opción sencilla es abrir `iniciar_windows.bat`: crea un entorno `.venv`, instala las dependencias y arranca el servidor. El proceso queda visible en la terminal; se detiene con **Ctrl+C**. No instala ni descarga ningún modelo.

También puedes hacerlo manualmente en PowerShell desde la carpeta del proyecto:

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m uvicorn backend:app --host 127.0.0.1 --port 8000
```

Abre `http://127.0.0.1:8000`, entra en la estación 07 y pulsa **Conectar backend local**. Después pulsa **Ejecutar en Python**. La respuesta indicará `runtime: python-local`.

Si `py` no existe pero tienes Python instalado, utiliza `python` en el primer comando. No hace falta activar el entorno ni cambiar la política de ejecución de PowerShell.

### macOS / Linux

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m uvicorn backend:app --host 127.0.0.1 --port 8000
```

No cambies el host a `0.0.0.0`: este proyecto está pensado para entrenamiento local monousuario, no para exposición en internet.

## 4. LLM local opcional, desde la terminal

Primero debes tener Ollama funcionando en tu equipo y un modelo compatible con herramientas ya instalado. El proyecto no presupone un modelo concreto. Introduce su nombre real, no el texto del ejemplo:

```powershell
$env:OLLAMA_MODEL = "nombre-de-tu-modelo-compatible"
.\.venv\Scripts\python.exe ollama_readonly.py "Consulta la baliza de Dagobah y la nave ALBA-7"
```

En macOS/Linux:

```bash
OLLAMA_MODEL="nombre-de-tu-modelo-compatible" .venv/bin/python ollama_readonly.py "Consulta la baliza de Dagobah"
```

Por defecto se usa `http://127.0.0.1:11434`. `OLLAMA_BASE_URL` permite cambiar el puerto, pero el adaptador solo admite un servidor local. No envía los datos a un proveedor remoto.

El bucle conserva las propuestas del asistente, ejecuta las tools permitidas y devuelve sus resultados al modelo. Tiene un límite de seis rondas y diez llamadas a herramientas. Una respuesta del modelo puede seguir siendo incorrecta: compara lo que dice con `tool_events`.

## 5. Estructura y código editable

```text
academia_galactica_v3/
  index.html                 Web autónoma ya construida
  LEEME.md                   Esta guía
  VERIFICACION.md            Pruebas y límites de verificación
  iniciar_windows.bat        Arranque opcional
  requirements.txt           Versiones del entorno probado
  backend.py                 API FastAPI y sesiones locales
  tool_engine.py             Herramientas y reglas de negocio
  catalog.json               Contratos compartidos
  ollama_readonly.py          Adaptador de LLM local, solo lectura
  build_frontend.py          Reconstrucción de la web
  frontend/
    index.template.html
    style.css
    engine.js
    engine.test.cjs
    app.js
    handlers.js
  tests/                     Pruebas Python
  verification_results.json  Lista de comprobaciones de interfaz
```

Para editar contenido o diseño, cambia los archivos de `frontend/`. Para reconstruir el HTML y el catálogo necesitas Python y Node.js (probado con Node 22):

```powershell
py build_frontend.py
```

El catálogo se genera desde `frontend/engine.js`; no lo edites como fuente independiente. Si cambias contratos o reglas, actualiza también el motor Python y sus pruebas para mantener la equivalencia.

## 6. Ejecutar las pruebas

Con el entorno ya instalado, desde la carpeta principal:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
node --test frontend/engine.test.cjs
```

La entrega pasó **43 pruebas Python y 35 pruebas del motor JavaScript**, además de **42 comprobaciones de interfaz**. Consulta `VERIFICACION.md`: el entorno de comprobación no permitía navegación HTTP directa de Chromium, por lo que el puente se ensayó con el transporte en memoria de FastAPI. Eso no equivale a haber comprobado tu instalación de Windows o un modelo Ollama real.

## 7. Progreso, privacidad y exportaciones

El progreso se guarda localmente con una clave propia de la versión 3. No modifica el progreso de la versión 2. Si el navegador bloquea el almacenamiento, la web avisa y permite seguir trabajando en la sesión actual.

**Exportar bitácora** descarga un JSON con retos, notas y evidencia de aprendizaje. Puedes importarlo después en la misma versión. El archivo abierto como `file://` y la web servida en localhost pueden tener almacenes diferentes: utiliza exportar/importar para trasladar tu progreso.

**Informe de aprendizaje** descarga un HTML imprimible. Ábrelo y usa la impresión del navegador. No es un certificado oficial ni una auditoría inviolable.

La flota, las autorizaciones y las órdenes viven en memoria y se reinician al recargar o reiniciar el servidor. El historial de retos puede persistir, pero no restaura una operación real. No se exportan tokens de sesión ni aprobaciones.

## 8. Límites importantes

La sesión del backend asigna un rol de entrenamiento; **no sustituye autenticación real**. Los controles de origen, CSRF, registro permitido, validación y confirmación son defensas didácticas, no una garantía de seguridad de producción.

La idempotencia del ejemplo dura mientras exista su estado en memoria. En producción harían falta almacenamiento durable, transacciones, aislamiento entre usuarios, observabilidad, límites operativos y una revisión de seguridad. No hay ejecución de Python arbitrario, SQL libre, comandos de terminal generados por el modelo ni acceso a tus archivos personales.

El laboratorio de contratos del navegador implementa un subconjunto explícito de JSON Schema y rechaza palabras clave que no soporta. El backend usa `jsonschema` para validar los contratos compartidos. El formato interno de llamada no pretende ser idéntico al de todos los proveedores.

## 9. Referencias técnicas

- OpenAI, Function calling: https://developers.openai.com/api/docs/guides/function-calling
- JSON Schema, objetos: https://json-schema.org/understanding-json-schema/reference/object
- Ollama, Tool calling: https://docs.ollama.com/capabilities/tool-calling
- FastAPI, Testing: https://fastapi.tiangolo.com/tutorial/testing/
- OWASP, Prompt injection: https://genai.owasp.org/llmrisk/llm01-prompt-injection/
- MCP, introducción: https://modelcontextprotocol.io/docs/getting-started/intro

Documentación consultada durante la elaboración. El software y los formatos de los proveedores pueden evolucionar; las versiones instaladas en este proyecto quedan fijadas en `requirements.txt`.
