#!/usr/bin/env python3
"""Gera os checksums do index.json. Rode após editar plugins, antes do git push."""
import hashlib
import json
from pathlib import Path

base = Path(__file__).resolve().parent
plugins = []
for folder in sorted((base / 'plugins').iterdir()):
    if not folder.is_dir():
        continue
    meta = json.loads((folder / 'plugin.json').read_text(encoding='utf-8'))
    records = []
    for file in sorted(folder.rglob('*')):
        if file.is_file() and file.suffix in ('.py', '.json', '.md', '.txt', '.png', '.svg'):
            records.append({'path': str(file.relative_to(base)), 'sha256': hashlib.sha256(file.read_bytes()).hexdigest()})
    record = {**{key: meta[key] for key in ('id', 'name', 'description', 'version')},
              'category': meta.get('category', 'Ferramentas'), 'files': records}
    if meta.get('image'):
        record['image'] = f'plugins/{meta["id"]}/{meta["image"]}'
    plugins.append(record)
(base / 'index.json').write_text(json.dumps({'schema': 1, 'plugins': plugins}, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print('index.json gerado com', len(plugins), 'plugins')
