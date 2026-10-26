#!/usr/bin/env python3
"""Check bundled assets, template references, CSS dependencies and Live2D models."""

import hashlib
import json
from pathlib import Path
import re
import sys
import xml.etree.ElementTree as ET
from urllib.parse import unquote, urlsplit


ROOT = Path(__file__).resolve().parents[1] / 'src/main/webapp'
ERRORS = []
CHECKED = set()
CSS_URL = re.compile(r'''url\(\s*(?:"([^"]*)"|'([^']*)'|([^)]*?))\s*\)''', re.S)
CDN = re.compile(r'''["'`](?:https?:)?//(?:ftp\.stackoverflow\.wiki|unpkg\.com|cdn\.jsdelivr\.net|file\.fishpi\.cn|fonts\.googleapis\.com|at\.alicdn\.com)/''')

patterns = {node.attrib['path'] for node in ET.parse(ROOT / 'WEB-INF/static-resources.xml').findall('include')}
if '/vendor/**' not in patterns:
    ERRORS.append('WEB-INF/static-resources.xml: vendor assets are not registered for static serving')


def local_file(source, reference, base=None):
    reference = reference.strip()
    if not reference or reference.startswith(('data:', '#')) or any(c in reference for c in ('$','{','}')):
        return
    if re.match(r'(https?:)?//', reference):
        ERRORS.append(f'{source.relative_to(ROOT)}: external asset {reference}')
        return
    name = unquote(urlsplit(reference).path)
    target = ROOT / name.lstrip('/') if name.startswith('/') else (base or source.parent) / name
    target = target.resolve()
    CHECKED.add(target)
    if not target.is_file():
        ERRORS.append(f'{source.relative_to(ROOT)}: missing {reference}')


def model_files(value, source):
    if isinstance(value, dict):
        for item in value.values():
            model_files(item, source)
    elif isinstance(value, list):
        for item in value:
            model_files(item, source)
    elif isinstance(value, str) and (value.startswith(('model/', '../')) or re.match(r'https?://', value)):
        base = ROOT / 'plugins/kanbanniang/assets' if value.startswith('model/') else source.parent
        local_file(source, value, base)


for source in sorted(ROOT.rglob('*')):
    if not source.is_file():
        continue
    if source.suffix in ('.css', '.scss'):
        content = re.sub(r'/\*.*?\*/', '', source.read_text(), flags=re.S)
        if source.suffix == '.scss':
            content = '\n'.join(line for line in content.splitlines() if not line.lstrip().startswith('//'))
        for match in CSS_URL.finditer(content):
            local_file(source, next(v for v in match.groups() if v is not None))
        for value in re.findall(r'''@import\s+["']([^"']+)["']''', content):
            if source.suffix == '.css' or value.endswith('.css'):
                local_file(source, value)
    elif source.suffix == '.ftl':
        content = source.read_text()
        for reference in re.findall(r'''(?:src|href|data-src|data-lazy-src)\s*=\s*["'](\$\{staticServePath\}/[^"']+)''', content):
            reference = reference.replace('${staticServePath}', '').split('?')[0]
            if '${skinDirName}' in reference:
                if 'skins' not in source.parts:
                    continue
                reference = reference.replace('${skinDirName}', source.relative_to(ROOT).parts[1])
            for postfix in ('', '.min') if '${miniPostfix}' in reference else ('',):
                local_file(source, reference.replace('${miniPostfix}', postfix))
        for reference in re.findall(r'''(?:src|data-src|data-lazy-src)\s*=\s*["']((?:https?:)?//[^"']+)''', content):
            local_file(source, reference)
    elif source.suffix == '.js':
        content = source.read_text()
        if CDN.search(content):
            ERRORS.append(f'{source.relative_to(ROOT)}: runtime CDN reference remains')
        for reference in re.findall(r'''["'](/vendor/[^"'\s]+)["']''', content):
            if not reference.endswith('/') and re.search(r'\.(js|css|json|png|gif|jpg|svg|woff2?)(?:[?#].*)?$', reference):
                local_file(source, reference)
    elif source.suffix == '.json' and ('kanbanniang/assets/model/' in source.as_posix() or 'vendor/sakura/live2d/' in source.as_posix()):
        model_files(json.loads(source.read_text()), source)

manifest = ROOT / 'vendor/sources.json'
for entry in json.loads(manifest.read_text()):
    target = ROOT / entry['path']
    if not target.is_file():
        ERRORS.append(f'sources.json: missing {entry["path"]}')
    elif hashlib.sha256(target.read_bytes()).hexdigest() != entry['sha256']:
        ERRORS.append(f'sources.json: checksum mismatch for {entry["path"]}')

if ERRORS:
    print('\n'.join(sorted(set(ERRORS))))
    sys.exit(1)
print(f'OK: {len(CHECKED)} referenced assets and all vendor checksums verified.')
