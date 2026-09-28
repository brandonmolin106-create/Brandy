"""Tiny Roblox XML (.rbxlx, format version 4) writer.

Values are (xml_tag, payload) tuples so the serializer knows exactly which XML type to
write. CFrames are (x, y, z, R) where R is a 3x3 rotation matrix given as rows (the
columns are the part's Right, Up and Back vectors, exactly like Roblox's R00..R22).
Attributes and CollectionService tags are written in Roblox's binary formats
(see rbx-dom docs/attributes.md), and read back by tools/check_place.luau.
"""
import base64
import math
import struct
import uuid
from xml.sax.saxutils import escape

# ----------------------------------------------------------------------------- values
def S(v): return ('string', str(v))
def PS(v): return ('ProtectedString', v)
def B(v): return ('bool', bool(v))
def I(v): return ('int', int(v))
def I64(v): return ('int64', int(v))
def F(v): return ('float', float(v))
def D(v): return ('double', float(v))
def T(v): return ('token', int(v))
def V3(x, y, z): return ('Vector3', (float(x), float(y), float(z)))
def V2(x, y): return ('Vector2', (float(x), float(y)))
def C3(r, g, b): return ('Color3', (r / 255, g / 255, b / 255))
def C3u8(rgb): return ('Color3uint8', tuple(int(c) for c in rgb))
def U2(xs, xo, ys, yo): return ('UDim2', (float(xs), int(xo), float(ys), int(yo)))
def U(s, o): return ('UDim', (float(s), int(o)))
def NR(a, b): return ('NumberRange', (float(a), float(b)))
def NS(*kps): return ('NumberSequence', kps)          # (t, value, envelope)
def CS(*kps): return ('ColorSequence', kps)           # (t, (r, g, b))
def CT(url): return ('Content', url)                  # None -> null
def FONT(family, weight=400, style='Normal'):
    return ('Font', (family, weight, style))

FAMILY = {
    # Font.fromEnum mapping (checked with Lune's Roblox library)
    'Fantasy': 'rbxasset://fonts/families/Balthazar.json',
    'Antique': 'rbxasset://fonts/families/RomanAntique.json',
    'Garamond': 'rbxasset://fonts/families/Guru.json',
    'Merriweather': 'rbxasset://fonts/families/Merriweather.json',
    'BuilderSans': 'rbxasset://fonts/families/BuilderSans.json',
    'Gotham': 'rbxasset://fonts/families/GothamSSm.json',
    'Michroma': 'rbxasset://fonts/families/Michroma.json',
}

# ----------------------------------------------------------------------------- CFrame math
def _mm(A, Bm):
    return [[sum(A[i][k] * Bm[k][j] for k in range(3)) for j in range(3)] for i in range(3)]

def rot(rx=0.0, ry=0.0, rz=0.0):
    """CFrame.Angles(rx, ry, rz) in degrees -> 3x3 (Rx * Ry * Rz)."""
    a, b, c = (math.radians(v) for v in (rx, ry, rz))
    Rx = [[1, 0, 0], [0, math.cos(a), -math.sin(a)], [0, math.sin(a), math.cos(a)]]
    Ry = [[math.cos(b), 0, math.sin(b)], [0, 1, 0], [-math.sin(b), 0, math.cos(b)]]
    Rz = [[math.cos(c), -math.sin(c), 0], [math.sin(c), math.cos(c), 0], [0, 0, 1]]
    return _mm(_mm(Rx, Ry), Rz)

IDENT = [[1, 0, 0], [0, 1, 0], [0, 0, 1]]

class CFrame:
    __slots__ = ('p', 'R')
    def __init__(self, p=(0, 0, 0), R=None):
        self.p = tuple(float(v) for v in p)
        self.R = R if R is not None else IDENT
    @staticmethod
    def new(x, y, z, rx=0.0, ry=0.0, rz=0.0):
        return CFrame((x, y, z), rot(rx, ry, rz))
    def __mul__(self, o):
        if isinstance(o, CFrame):
            return CFrame(self.point(o.p), _mm(self.R, o.R))
        raise TypeError(o)
    def point(self, v):
        R, p = self.R, self.p
        return tuple(p[i] + R[i][0] * v[0] + R[i][1] * v[1] + R[i][2] * v[2] for i in range(3))
    def vector(self, v):
        R = self.R
        return tuple(R[i][0] * v[0] + R[i][1] * v[1] + R[i][2] * v[2] for i in range(3))
    @property
    def look(self):
        return tuple(-self.R[i][2] for i in range(3))
    def val(self):
        return ('CoordinateFrame', (self.p[0], self.p[1], self.p[2], self.R))

def norm(v):
    m = math.sqrt(sum(c * c for c in v))
    return tuple(c / m for c in v)

def cross(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])

def look_at(pos, target, up=(0, 1, 0)):
    """Like CFrame.lookAt: the part's Front face (-Z) points at target."""
    look = norm(tuple(t - p for t, p in zip(target, pos)))
    right = norm(cross(look, up))
    upv = cross(right, look)
    back = tuple(-c for c in look)
    R = [[right[i], upv[i], back[i]] for i in range(3)]
    return CFrame(pos, R)

def CF(x, y, z, rx=0.0, ry=0.0, rz=0.0):
    return CFrame.new(x, y, z, rx, ry, rz).val()

def fmt(v):
    v = round(float(v), 5)
    if v == 0:
        v = 0.0
    if v.is_integer():
        return str(int(v))
    return repr(v)

# ----------------------------------------------------------------------------- attributes / tags
def attr_vec3(x, y, z): return ('Vector3', (float(x), float(y), float(z)))
def attr_color(rgb): return ('Color3', tuple(c / 255 for c in rgb))

def _astr(s):
    b = s.encode('utf-8')
    return struct.pack('<I', len(b)) + b

def encode_attributes(attrs):
    out = [struct.pack('<I', len(attrs))]
    for name, v in attrs.items():
        out.append(_astr(name))
        if isinstance(v, bool):
            out.append(b'\x03' + (b'\x01' if v else b'\x00'))
        elif isinstance(v, (int, float)):
            out.append(b'\x06' + struct.pack('<d', float(v)))
        elif isinstance(v, str):
            out.append(b'\x02' + _astr(v))
        elif isinstance(v, tuple) and v[0] == 'Vector3':
            out.append(b'\x11' + struct.pack('<3f', *v[1]))
        elif isinstance(v, tuple) and v[0] == 'Color3':
            out.append(b'\x0f' + struct.pack('<3f', *v[1]))
        else:
            raise ValueError(f'unsupported attribute {name}={v!r}')
    return b''.join(out)

def decode_attributes(blob):
    """Inverse of encode_attributes (used by the validator)."""
    pos, out = 0, {}
    def u32():
        nonlocal pos
        v = struct.unpack_from('<I', blob, pos)[0]; pos += 4; return v
    def rstr():
        nonlocal pos
        n = u32(); s = blob[pos:pos + n].decode('utf-8'); pos += n; return s
    count = u32()
    for _ in range(count):
        name = rstr()
        t = blob[pos]; pos += 1
        if t == 0x03:
            out[name] = blob[pos] != 0; pos += 1
        elif t == 0x06:
            out[name] = struct.unpack_from('<d', blob, pos)[0]; pos += 8
        elif t == 0x02:
            out[name] = rstr()
        elif t == 0x11:
            out[name] = ('Vector3', struct.unpack_from('<3f', blob, pos)); pos += 12
        elif t == 0x0F:
            out[name] = ('Color3', struct.unpack_from('<3f', blob, pos)); pos += 12
        else:
            raise ValueError(f'unknown attribute type {t:#x} for {name}')
    return out

# ----------------------------------------------------------------------------- instances
class Inst:
    _counter = 0
    def __init__(self, cls, name, **props):
        Inst._counter += 1
        self.cls = cls
        self.children = []
        self.props = {'Name': S(name)}
        self.props.update(props)
        self.attrs = {}
        self.tags = []
        self.source_file = None
        self.ref = 'RBX' + uuid.uuid5(uuid.NAMESPACE_URL, f'nbe/{Inst._counter}').hex.upper()
    def set(self, **props):
        self.props.update(props)
        return self
    def attr(self, **attrs):
        self.attrs.update(attrs)
        return self
    def tag(self, *tags):
        for t in tags:
            if t not in self.tags:
                self.tags.append(t)
        return self
    def add(self, *kids):
        for k in kids:
            if k is None:
                continue
            if isinstance(k, (list, tuple)):
                self.add(*k)
            else:
                self.children.append(k)
        return self
    @property
    def name(self):
        return self.props['Name'][1]
    def walk(self):
        yield self
        for c in self.children:
            yield from c.walk()
    def find(self, name):
        for c in self.children:
            if c.name == name:
                return c
        return None

def ser(name, val):
    tag, v = val
    n = f'name="{name}"'
    if tag == 'string':
        return f'<string {n}>{escape(v)}</string>'
    if tag == 'ProtectedString':
        return f'<ProtectedString {n}><![CDATA[{v.replace("]]>", "]]]]><![CDATA[>")}]]></ProtectedString>'
    if tag == 'bool':
        return f'<bool {n}>{"true" if v else "false"}</bool>'
    if tag in ('int', 'int64', 'token'):
        return f'<{tag} {n}>{int(v)}</{tag}>'
    if tag in ('float', 'double'):
        return f'<{tag} {n}>{fmt(v)}</{tag}>'
    if tag == 'Vector3':
        return f'<Vector3 {n}><X>{fmt(v[0])}</X><Y>{fmt(v[1])}</Y><Z>{fmt(v[2])}</Z></Vector3>'
    if tag == 'Vector2':
        return f'<Vector2 {n}><X>{fmt(v[0])}</X><Y>{fmt(v[1])}</Y></Vector2>'
    if tag == 'CoordinateFrame':
        x, y, z, R = v
        rs = ''.join(f'<R{i}{j}>{fmt(R[i][j])}</R{i}{j}>' for i in range(3) for j in range(3))
        return f'<CoordinateFrame {n}><X>{fmt(x)}</X><Y>{fmt(y)}</Y><Z>{fmt(z)}</Z>{rs}</CoordinateFrame>'
    if tag == 'Color3':
        return f'<Color3 {n}><R>{fmt(v[0])}</R><G>{fmt(v[1])}</G><B>{fmt(v[2])}</B></Color3>'
    if tag == 'Color3uint8':
        r, g, b = v
        return f'<Color3uint8 {n}>{0xFF000000 | (r << 16) | (g << 8) | b}</Color3uint8>'
    if tag == 'UDim2':
        return f'<UDim2 {n}><XS>{fmt(v[0])}</XS><XO>{v[1]}</XO><YS>{fmt(v[2])}</YS><YO>{v[3]}</YO></UDim2>'
    if tag == 'UDim':
        return f'<UDim {n}><S>{fmt(v[0])}</S><O>{v[1]}</O></UDim>'
    if tag == 'NumberRange':
        return f'<NumberRange {n}>{fmt(v[0])} {fmt(v[1])} </NumberRange>'
    if tag == 'NumberSequence':
        return f'<NumberSequence {n}>' + ''.join(f'{fmt(t)} {fmt(x)} {fmt(e)} ' for t, x, e in v) + '</NumberSequence>'
    if tag == 'ColorSequence':
        return (f'<ColorSequence {n}>'
                + ''.join(f'{fmt(t)} {fmt(c[0] / 255)} {fmt(c[1] / 255)} {fmt(c[2] / 255)} 0 ' for t, c in v)
                + '</ColorSequence>')
    if tag == 'Content':
        return f'<Content {n}>' + ('<null></null>' if v is None else f'<url>{escape(v)}</url>') + '</Content>'
    if tag == 'Font':
        fam, w, st = v
        return f'<Font {n}><Family><url>{fam}</url></Family><Weight>{w}</Weight><Style>{st}</Style></Font>'
    if tag == 'BinaryString':
        return f'<BinaryString {n}>{v}</BinaryString>'
    raise ValueError(tag)

def emit(inst, out, depth):
    ind = '\t' * depth
    out.append(f'{ind}<Item class="{inst.cls}" referent="{inst.ref}">')
    out.append(f'{ind}\t<Properties>')
    for k, v in inst.props.items():
        out.append(f'{ind}\t\t{ser(k, v)}')
    if inst.attrs:
        blob = base64.b64encode(encode_attributes(inst.attrs)).decode('ascii')
        out.append(f'{ind}\t\t{ser("AttributesSerialize", ("BinaryString", blob))}')
    if inst.tags:
        blob = base64.b64encode('\0'.join(inst.tags).encode('utf-8')).decode('ascii')
        out.append(f'{ind}\t\t{ser("Tags", ("BinaryString", blob))}')
    out.append(f'{ind}\t</Properties>')
    for c in inst.children:
        emit(c, out, depth + 1)
    out.append(f'{ind}</Item>')

def write_place(services, path):
    out = ['<roblox xmlns:xmime="http://www.w3.org/2005/05/xmlmime" '
           'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
           'xsi:noNamespaceSchemaLocation="http://www.roblox.com/roblox.xsd" version="4">',
           '\t<Meta name="ExplicitAutoJoints">true</Meta>',
           '\t<External>null</External>', '\t<External>nil</External>']
    for s in services:
        emit(s, out, 1)
    out.append('</roblox>')
    with open(path, 'w', encoding='utf-8', newline='\n') as f:
        f.write('\n'.join(out) + '\n')
