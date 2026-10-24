#!/usr/bin/env python3
"""Verify index integrity and Python syntax with only the stdlib."""
import ast
import hashlib
import json
from pathlib import Path

root = Path(__file__).resolve().parent
index = json.loads((root/'index.json').read_text(encoding='utf-8'))
assert index['schema'] == 1
assert len(index['plugins']) >= 31
seen = set()
for record in index['plugins']:
    plugin_id = record['id']
    assert plugin_id not in seen and record['name'] and record['version']
    seen.add(plugin_id)
    required = {f'plugins/{plugin_id}/plugin.py', f'plugins/{plugin_id}/plugin.json',
                f'plugins/{plugin_id}/cover.png'}
    paths = {item['path'] for item in record['files']}
    assert required <= paths, (plugin_id, required - paths)
    assert record.get('image') == f'plugins/{plugin_id}/cover.png'
    for f in record['files']:
        name = Path(f['path'])
        assert '..' not in name.parts and name.parts[:2] == ('plugins',plugin_id)
        contents = (root / name).read_bytes()
        assert hashlib.sha256(contents).hexdigest() == f['sha256'], str(name)
        if name.suffix == '.py':
            ast.parse(contents.decode('utf-8'), filename=str(name))
    meta = json.loads((root/f'plugins/{plugin_id}/plugin.json').read_text('utf-8'))
    assert meta['id'] == plugin_id and meta['version'] == record['version']
    assert (root/record['image']).read_bytes().startswith(b'\x89PNG\r\n\x1a\n')
print(f'OK: {len(seen)} plugins e SHA-256 de todos os arquivos verificados.')
