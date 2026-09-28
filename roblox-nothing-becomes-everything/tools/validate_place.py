#!/usr/bin/env python3
"""Validate NothingBecomesEverything.rbxlx.

    python3 tools/validate_place.py [--skip-lune] [--skip-types]

Checks, in order:
 1. The file is well-formed XML (Roblox place format version 4).
 2. Every class, property name, XML data type and enum value exists in rbx-dom's reflection
    database AND in Roblox's current API dump (nothing deprecated, nothing unloadable).
    Attributes and CollectionService tags decode.
 3. Compliance: no off-platform references anywhere in the game (no links, no social handles,
    no full names), and every script in the place is byte-identical to its file in src/.
 4. Every part is anchored; the part count stays under the budget.
 5. Jump gaps between consecutive platforms (PathGroup/PathOrder attributes) are makeable:
    <= 5 studs horizontal and <= 2 studs up.
 6. tools/check_place.luau loads the place in Lune (the Roblox DOM) and checks its structure.
 7. luau-lsp type-checks every script with Roblox types (--!strict files are strict).
Missing tools are downloaded into tools/.cache/ on first use.
"""
import base64
import io
import json
import math
import os
import subprocess
import sys
import urllib.request
import xml.etree.ElementTree as ET
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from placegen.rbx import decode_attributes  # noqa: E402

CACHE = os.path.join(HERE, '.cache')
PLACE = os.path.join(ROOT, 'NothingBecomesEverything.rbxlx')
PART_BUDGET = 4000
MAX_GAP, MAX_RISE = 5.0, 2.0

TOOLS = {
    'rbxdom_database.json': ('https://raw.githubusercontent.com/rojo-rbx/rbx-dom/master/rbx_dom_lua/src/database.json', None),
    'Full-API-Dump.json': ('https://raw.githubusercontent.com/MaximumADHD/Roblox-Client-Tracker/roblox/Full-API-Dump.json', None),
    'globalTypes.d.luau': ('https://raw.githubusercontent.com/JohnnyMorganz/luau-lsp/main/scripts/globalTypes.d.luau', None),
    'luau-lsp': ('https://github.com/JohnnyMorganz/luau-lsp/releases/download/1.70.1/luau-lsp-linux-x86_64.zip', 'luau-lsp'),
    'lune': ('https://github.com/lune-org/lune/releases/download/v0.10.5/lune-0.10.5-linux-x86_64.zip', 'lune'),
}

def tool(name):
    path = os.path.join(CACHE, name)
    if os.path.exists(path):
        return path
    url, member = TOOLS[name]
    os.makedirs(CACHE, exist_ok=True)
    print(f'  downloading {name} ...')
    data = urllib.request.urlopen(url, timeout=120).read()
    if member:
        with zipfile.ZipFile(io.BytesIO(data)) as zf:
            data = zf.read(member)
    with open(path, 'wb') as f:
        f.write(data)
    if member:
        os.chmod(path, 0o755)
    return path

# ----------------------------------------------------------------------------- 1-2 reflection
TAGS = {'String': {'string'}, 'Bool': {'bool'}, 'Int32': {'int'}, 'Int64': {'int64'}, 'Float32': {'float'},
        'Float64': {'double'}, 'Vector3': {'Vector3'}, 'Vector2': {'Vector2'}, 'CFrame': {'CoordinateFrame'},
        'Color3': {'Color3'}, 'Color3uint8': {'Color3uint8'}, 'UDim2': {'UDim2'}, 'UDim': {'UDim'},
        'NumberRange': {'NumberRange'}, 'NumberSequence': {'NumberSequence'}, 'ColorSequence': {'ColorSequence'},
        'ContentId': {'Content'}, 'Content': {'Content'}, 'Font': {'Font'}, 'Ref': {'Ref'}, 'BrickColor': {'int'},
        'Enum': {'token'}, 'BinaryString': {'BinaryString'}, 'Tags': {'BinaryString'}}

def load_reflection():
    db = json.load(open(tool('rbxdom_database.json')))['Classes']
    dump = json.load(open(tool('Full-API-Dump.json')))
    dcls = {c['Name']: c for c in dump['Classes']}
    enums = {e['Name']: {i['Value'] for i in e['Items']} for e in dump['Enums']}
    return db, dcls, enums

def props_of(db, cls):
    out, c = {}, cls
    while c:
        for n, p in db[c]['Properties'].items():
            out.setdefault(n, p)
        c = db[c].get('Superclass')
    return out

def dump_member(dcls, cls, name):
    c = cls
    while c:
        for m in dcls[c]['Members']:
            if m['MemberType'] == 'Property' and m['Name'] == name:
                return m
        c = dcls[c].get('Superclass')
    return None

def check_reflection(root, errors):
    db, dcls, enums = load_reflection()
    count, classes, refs = 0, {}, set()
    for item in root.iter('Item'):
        cls = item.get('class')
        count += 1
        classes[cls] = classes.get(cls, 0) + 1
        ref = item.get('referent')
        if ref in refs:
            errors.append(f'duplicate referent {ref}')
        refs.add(ref)
        if cls not in db or cls not in dcls:
            errors.append(f'unknown class {cls}')
            continue
        tags = dcls[cls].get('Tags', [])
        if 'NotCreatable' in tags and 'Service' not in tags and cls not in ('StarterPlayerScripts', 'StarterCharacterScripts'):
            errors.append(f'{cls} is NotCreatable')
        if 'Deprecated' in tags:
            errors.append(f'{cls} is deprecated')
        P = props_of(db, cls)
        name = None
        for el in item.find('Properties'):
            pname, tag = el.get('name'), el.tag
            if pname == 'Name':
                name = el.text
            p = P.get(pname)
            if p is None:
                errors.append(f'{cls}.{pname}: not a property')
                continue
            kind = p['Kind']
            canonical = p
            if 'Alias' in kind:
                canonical = P[kind['Alias']['AliasFor']]
                ser = canonical['Kind']['Canonical']['Serialization']
                if not (isinstance(ser, dict) and ser.get('SerializesAs') == pname):
                    errors.append(f'{cls}.{pname}: alias that is not the serialized name')
            else:
                ser = kind['Canonical']['Serialization']
                if ser == 'DoesNotSerialize':
                    errors.append(f'{cls}.{pname}: does not serialize')
                if isinstance(ser, dict) and 'SerializesAs' in ser and ser['SerializesAs'] != pname:
                    errors.append(f'{cls}.{pname}: should be written as "{ser["SerializesAs"]}"')
            dt = p['DataType']
            key = 'Enum' if 'Enum' in dt else dt['Value']
            if key not in TAGS:
                errors.append(f'{cls}.{pname}: unhandled datatype {key}')
            elif tag not in TAGS[key] and not (pname == 'Source' and tag == 'ProtectedString'):
                errors.append(f'{cls}.{pname}: xml tag {tag} but datatype {key}')
            if 'Enum' in dt:
                v = int(el.text)
                if v not in enums[dt['Enum']]:
                    errors.append(f'{cls}.{pname}: {v} not in Enum.{dt["Enum"]}')
            if pname == 'AttributesSerialize':
                try:
                    decode_attributes(base64.b64decode(el.text or ''))
                except Exception as e:  # noqa: BLE001
                    errors.append(f'{cls} {name}: attributes do not decode ({e})')
            if pname == 'Tags':
                try:
                    base64.b64decode(el.text or '').decode('utf-8')
                except Exception as e:  # noqa: BLE001
                    errors.append(f'{cls} {name}: tags do not decode ({e})')
            if pname in ('Tags', 'AttributesSerialize'):
                continue       # engine-internal names; not listed as scriptable members of the dump
            m = dump_member(dcls, cls, canonical['Name'])
            if m is None:
                errors.append(f'{cls}.{canonical["Name"]}: missing from current API dump')
            else:
                mtags = [t for t in m.get('Tags', []) if isinstance(t, str)]
                if 'Deprecated' in mtags:
                    errors.append(f'{cls}.{canonical["Name"]}: deprecated')
                if not m.get('Serialization', {}).get('CanLoad', True) and canonical is p:
                    errors.append(f'{cls}.{pname}: CanLoad false')
        if name is None:
            errors.append(f'{cls} without Name')
    return count, classes

# ----------------------------------------------------------------------------- helpers over the XML
PART_CLASSES = {'Part', 'WedgePart', 'CornerWedgePart', 'Seat', 'SpawnLocation', 'TrussPart', 'MeshPart',
                'VehicleSeat', 'UnionOperation'}

def props(item):
    out = {}
    for el in item.find('Properties'):
        out[el.get('name')] = el
    return out

def get_attrs(item):
    el = props(item).get('AttributesSerialize')
    if el is None or not el.text:
        return {}
    return decode_attributes(base64.b64decode(el.text))

def vec(el):
    return tuple(float(el.find(k).text) for k in ('X', 'Y', 'Z'))

def cframe(el):
    p = tuple(float(el.find(k).text) for k in ('X', 'Y', 'Z'))
    R = [[float(el.find(f'R{i}{j}').text) for j in range(3)] for i in range(3)]
    return p, R

def item_path(item, parents):
    names = []
    cur = item
    while cur is not None:
        pr = cur.find('Properties')
        if pr is not None:
            for el in pr:
                if el.get('name') == 'Name':
                    names.append(el.text)
        cur = parents.get(cur)
    return '.'.join(reversed(names))

# ----------------------------------------------------------------------------- 3 compliance
# Nothing in the game may point players off Roblox or reveal more than the first name.
BANNED = [r'tik\s*tok', r'molina', r'https?://', r'www\.', r'\b[a-z0-9-]+\.(com|net|org|gg|tv|io|ly|co)(\b|/)',
          r'youtube', r'instagram', r'discord', r'twitter', r'snapchat', r'facebook', r'twitch', r'@\w']

def check_compliance(root, parents, errors):
    import re
    pats = [re.compile(b) for b in BANNED]
    for item in root.iter('Item'):
        for el in item.find('Properties'):
            if el.tag in ('string', 'ProtectedString') and el.text:
                low = el.text.lower()
                for pat in pats:
                    m = pat.search(low)
                    if m:
                        errors.append(f'{item_path(item, parents)}.{el.get("name")}: contains "{m.group(0)}"')

def check_sources(root, parents, errors):
    smap = json.load(open(os.path.join(CACHE, 'sourcemap.json')))
    files = {}
    def walk(node, path):
        p = path + [node['name']]
        for fp in node.get('filePaths', []):
            files['.'.join(p[1:])] = fp
        for c in node.get('children', []):
            walk(c, p)
    walk(smap, [])
    seen = 0
    for item in root.iter('Item'):
        if item.get('class') not in ('Script', 'LocalScript', 'ModuleScript'):
            continue
        path = item_path(item, parents)
        src_el = props(item).get('Source')
        fp = files.get(path)
        if fp is None:
            errors.append(f'{path}: script has no source file in src/')
            continue
        with open(os.path.join(ROOT, fp), encoding='utf-8') as f:
            disk = f.read()
        if (src_el.text or '') != disk:
            errors.append(f'{path}: Source differs from {fp} (rebuild the place)')
        seen += 1
    on_disk = set()
    for d, _, fs in os.walk(os.path.join(ROOT, 'src')):
        for fn in fs:
            if fn.endswith('.lua'):
                on_disk.add(os.path.relpath(os.path.join(d, fn), ROOT).replace(os.sep, '/'))
    missing = on_disk - set(files.values())
    for m in sorted(missing):
        errors.append(f'{m}: not in the place (rebuild the place)')
    return seen

# ----------------------------------------------------------------------------- 4 parts
def check_parts(root, parents, errors, warnings):
    n = 0
    shadows = 0
    for item in root.iter('Item'):
        if item.get('class') not in PART_CLASSES:
            continue
        n += 1
        pr = props(item)
        anchored = pr.get('Anchored')
        if anchored is None or anchored.text != 'true':
            errors.append(f'{item_path(item, parents)}: part is not anchored')
        collide = pr.get('CanCollide')
        shadow = pr.get('CastShadow')
        size = vec(pr['size']) if 'size' in pr else (4, 1, 2)
        if collide is not None and collide.text == 'false' and shadow is not None and shadow.text == 'true' \
                and max(size) < 4:
            shadows += 1
            warnings.append(f'{item_path(item, parents)} is small, non-colliding and casts a shadow')
    if n > PART_BUDGET:
        errors.append(f'{n} parts is over the budget of {PART_BUDGET}')
    return n

# ----------------------------------------------------------------------------- 5 jumps
def footprint(shape, pos, R, size, attrs):
    """(polygon in XZ, exit_top, entry_top) for a standable part."""
    sx, sy, sz = size
    def world(v):
        return tuple(pos[i] + R[i][0] * v[0] + R[i][1] * v[1] + R[i][2] * v[2] for i in range(3))
    if shape == 'disc':
        axis_len, radius = sx, sy / 2           # cylinder: axis = local X (turned vertical)
        top = pos[1] + axis_len / 2
        poly = [(pos[0] + radius * math.cos(2 * math.pi * k / 32), pos[2] + radius * math.sin(2 * math.pi * k / 32))
                for k in range(32)]
        return poly, top, top
    if shape == 'sweep':
        piv = attrs['SweepPivot'][1]
        r = attrs['SweepRadius']
        top = max(world((dx, sy / 2, dz))[1] for dx in (-sx / 2, sx / 2) for dz in (-sz / 2, sz / 2))
        poly = [(piv[0] + r * math.cos(2 * math.pi * k / 64), piv[2] + r * math.sin(2 * math.pi * k / 64))
                for k in range(64)]
        return poly, top, top
    corners = [world((dx, sy / 2, dz)) for dx in (-sx / 2, sx / 2) for dz in (-sz / 2, sz / 2)]
    poly = [(c[0], c[2]) for c in (corners[0], corners[1], corners[3], corners[2])]
    if shape == 'ramp':
        return poly, pos[1] + sy / 2, pos[1] - sy / 2
    top = max(c[1] for c in corners)
    return poly, top, top

def seg_dist(p, q, a, b):
    def pt_seg(pt, s0, s1):
        dx, dz = s1[0] - s0[0], s1[1] - s0[1]
        L = dx * dx + dz * dz
        t = 0 if L == 0 else max(0, min(1, ((pt[0] - s0[0]) * dx + (pt[1] - s0[1]) * dz) / L))
        return math.hypot(pt[0] - (s0[0] + t * dx), pt[1] - (s0[1] + t * dz))
    return min(pt_seg(p, a, b), pt_seg(q, a, b), pt_seg(a, p, q), pt_seg(b, p, q))

def inside(pt, poly):
    c = False
    for i in range(len(poly)):
        a, b = poly[i], poly[(i + 1) % len(poly)]
        if (a[1] > pt[1]) != (b[1] > pt[1]):
            x = a[0] + (pt[1] - a[1]) * (b[0] - a[0]) / (b[1] - a[1])
            if pt[0] < x:
                c = not c
    return c

def poly_dist(A, B_):
    if any(inside(p, B_) for p in A) or any(inside(p, A) for p in B_):
        return 0.0
    best = float('inf')
    for i in range(len(A)):
        for j in range(len(B_)):
            best = min(best, seg_dist(A[i], A[(i + 1) % len(A)], B_[j], B_[(j + 1) % len(B_)]))
    return best

def check_jumps(root, parents, errors):
    groups = {}
    for item in root.iter('Item'):
        if item.get('class') not in PART_CLASSES:
            continue
        attrs = get_attrs(item)
        if 'PathGroup' not in attrs:
            continue
        pr = props(item)
        pos, R = cframe(pr['CFrame'])
        size = vec(pr['size'])
        shape = attrs.get('PathShape', 'box')
        poly, exit_top, entry_top = footprint(shape, pos, R, size, attrs)
        groups.setdefault(attrs['PathGroup'], []).append(
            (attrs['PathOrder'], item_path(item, parents), shape, poly, exit_top, entry_top, attrs))
    report = []
    for g, nodes in sorted(groups.items()):
        nodes.sort(key=lambda n: n[0])
        worst_gap = worst_rise = 0.0
        for a, b in zip(nodes, nodes[1:]):
            if a[2] == 'sweep' or b[2] == 'sweep':
                sweep, other = (a, b) if a[2] == 'sweep' else (b, a)
                piv = sweep[6]['SweepPivot'][1]
                r = sweep[6]['SweepRadius']
                d = 0.0 if inside((piv[0], piv[2]), other[3]) else min(
                    seg_dist((piv[0], piv[2]), (piv[0], piv[2]), other[3][i], other[3][(i + 1) % len(other[3])])
                    for i in range(len(other[3])))
                gap = max(0.0, d - r)
            else:
                gap = poly_dist(a[3], b[3])
            rise = b[5] - a[4]
            worst_gap, worst_rise = max(worst_gap, gap), max(worst_rise, rise)
            if gap > MAX_GAP + 0.01 or rise > MAX_RISE + 0.01:
                errors.append(f'jump {g} #{a[0]:g} -> #{b[0]:g}: gap {gap:.2f} studs, rise {rise:.2f} studs '
                              f'({a[1]} -> {b[1]})')
        report.append(f'{g}: {len(nodes)} platforms, widest gap {worst_gap:.2f}, biggest step up {worst_rise:.2f}')
    return report

# ----------------------------------------------------------------------------- 6-7 external checks
def run_lune(errors):
    lune = tool('lune')
    r = subprocess.run([lune, 'run', os.path.join(HERE, 'check_place.luau'), PLACE, ROOT], capture_output=True,
                       text=True)
    out = (r.stdout + r.stderr).strip()
    print('\n'.join('    ' + l for l in out.splitlines()))
    if r.returncode != 0:
        errors.append('Lune structural check failed')

def run_types(errors):
    lsp = tool('luau-lsp')
    defs = tool('globalTypes.d.luau')
    files = []
    for d, _, fs in os.walk(os.path.join(ROOT, 'src')):
        for fn in sorted(fs):
            if fn.endswith('.lua'):
                files.append(os.path.relpath(os.path.join(d, fn), ROOT))
    nonstrict = [f for f in files if not open(os.path.join(ROOT, f), encoding='utf-8').read().startswith('--!strict')]
    for solver in ('false', 'true'):      # the classic type solver and the new one
        r = subprocess.run([lsp, 'analyze', '--platform=roblox', f'--definitions={defs}',
                            f'--sourcemap={os.path.join(CACHE, "sourcemap.json")}', f'--flag:LuauSolverV2={solver}']
                           + files, capture_output=True, text=True, cwd=ROOT)
        lines = sorted(set(l for l in (r.stdout + r.stderr).splitlines()
                           if not l.startswith('[INFO]') and 'didChangeWatchedFiles' not in l))
        if lines:
            print('\n'.join('    ' + l.replace(ROOT + os.sep, '') for l in lines))
        if r.returncode != 0 or lines:
            errors.append(f'Luau type check reported problems (LuauSolverV2={solver})')
        name = 'new solver' if solver == 'true' else 'classic solver'
        print(f'    luau-lsp ({name}): {len(files)} scripts, {len(lines)} problems')
    print(f'    {len(files) - len(nonstrict)} of {len(files)} scripts are --!strict'
          + (f'; not strict: {", ".join(nonstrict)}' if nonstrict else ''))

def main():
    args = set(sys.argv[1:])
    errors, warnings = [], []
    tree = ET.parse(PLACE)
    root = tree.getroot()
    assert root.tag == 'roblox' and root.get('version') == '4', 'not a version 4 Roblox XML place'
    parents = {c: p for p in root.iter() for c in p}
    print('1-2. XML + reflection')
    count, classes = check_reflection(root, errors)
    print(f'    {count} instances, {len(classes)} classes: ' + ', '.join(f'{k} x{v}' for k, v in sorted(classes.items())))
    print('3. compliance + sources')
    check_compliance(root, parents, errors)
    seen = check_sources(root, parents, errors)
    print(f'    {seen} scripts match src/')
    print('4. parts')
    n = check_parts(root, parents, errors, warnings)
    print(f'    {n} parts (budget {PART_BUDGET}), all anchored' if not any('anchored' in e for e in errors)
          else f'    {n} parts')
    print('5. jump gaps')
    for line in check_jumps(root, parents, errors):
        print('    ' + line)
    if '--skip-lune' not in args:
        print('6. Lune (Roblox DOM) load + structure')
        run_lune(errors)
    if '--skip-types' not in args:
        print('7. Luau type check')
        run_types(errors)
    for w in warnings:
        print('  warning:', w)
    if errors:
        print(f'\n{len(errors)} ERRORS')
        for e in sorted(set(errors)):
            print('  ', e)
        sys.exit(1)
    print('\nOK: place is valid')

if __name__ == '__main__':
    main()
