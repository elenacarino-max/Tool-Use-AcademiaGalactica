"""Build a standalone HTML and shared catalog from the editable frontend sources."""
from pathlib import Path
import json
import shutil
import subprocess
import sys

def main() -> int:
    root = Path(__file__).resolve().parent
    src = root / 'frontend'
    node = shutil.which('node')
    if not node:
        print('Necesitas Node.js para reconstruir el catalogo. El index.html ya construido funciona sin Node.', file=sys.stderr)
        return 1
    html = (src / 'index.template.html').read_text(encoding='utf-8')
    parts = {
        '/*CSS*/': (src / 'style.css').read_text(encoding='utf-8'),
        '/*ENGINE*/': (src / 'engine.js').read_text(encoding='utf-8'),
        '/*APP*/': '\n'.join((src / name).read_text(encoding='utf-8') for name in ('app.js', 'handlers.js')) + '\nrender();\n',
    }
    for marker, contents in parts.items():
        if marker not in html:
            raise ValueError('No se encuentra el marcador ' + marker)
        html = html.replace(marker, contents)
    script = 'const e=require(' + json.dumps(str(src / 'engine.js')) + '); console.log(JSON.stringify(e.catalog,null,2));'
    result = subprocess.run([node, '-e', script], check=True, text=True, encoding='utf-8', capture_output=True)
    json.loads(result.stdout)
    (root / 'index.html').write_text(html, encoding='utf-8')
    (root / 'catalog.json').write_text(result.stdout, encoding='utf-8')
    print('Generados index.html y catalog.json. Ejecuta las pruebas antes de entregar los cambios.')
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
