import sys, os, io, struct

base = os.environ['TEMP'] + r'\591iq_scratch\hw4'
sys.path.insert(0, os.path.join(base, 'pylibs'))
import olefile

ole = olefile.OleFileIO(sys.argv[1])
doc = ole.openstream('WordDocument').read()
N = len(doc)
ccpText = struct.unpack_from('<I', doc, 0x4C)[0]
print('WordDocument=%d bytes  ccpText=%d' % (N, ccpText), file=sys.stderr)

found = None
for pos in range(0, min(N - 12, 0x4000)):
    if doc[pos] != 0x02:
        continue
    lcb = struct.unpack_from('<I', doc, pos + 1)[0]
    if lcb < 16 or lcb % 12 != 4 or lcb > 4096:
        continue
    if pos + 5 + lcb > N:
        continue
    nseg = (lcb - 4) // 12
    plc = doc[pos + 5: pos + 5 + lcb]
    cps = [struct.unpack_from('<I', plc, k * 4)[0] for k in range(nseg + 1)]
    if cps[0] != 0 or cps[-1] != ccpText:
        continue
    ok = True
    for k in range(nseg):
        fc = struct.unpack_from('<I', plc, (nseg + 1) * 4 + k * 8 + 2)[0]
        comp = bool(fc & 0x40000000)
        fo = (fc & 0x3FFFFFFF) // 2 if comp else (fc & 0x3FFFFFFF)
        if fo <= 0 or fo >= N:
            ok = False
            break
        if not comp and fo + (cps[k + 1] - cps[k]) * 2 > N:
            ok = False
            break
    if ok:
        found = (pos, lcb, nseg, plc)
        print('Pcdt @ 0x%X  lcb=%d  nseg=%d' % found[:3], file=sys.stderr)
        break

if not found:
    raise SystemExit('Pcdt not found')

pos, lcb, nseg, plc = found
cps = [struct.unpack_from('<I', plc, k * 4)[0] for k in range(nseg + 1)]
chunks = []
for k in range(nseg):
    fc = struct.unpack_from('<I', plc, (nseg + 1) * 4 + k * 8 + 2)[0]
    comp = bool(fc & 0x40000000)
    base_off = (fc & 0x3FFFFFFF) // 2 if comp else (fc & 0x3FFFFFFF)
    ncp = cps[k + 1] - cps[k]
    if comp:
        s = doc[base_off: base_off + ncp].decode('cp1252', 'replace')
    else:
        s = doc[base_off: base_off + ncp * 2].decode('utf-16-le', 'replace')
    chunks.append(s)

text = ''.join(chunks)
for ch in '\x07\x0c\x0b\x13\x14\x15\x01\x02\x1e\x1f':
    text = text.replace(ch, '\n')
text = text.replace('\r', '\n')
lines = [l.strip() for l in text.split('\n')]
lines = [l for l in lines if l]
io.open(sys.argv[2], 'w', encoding='utf-8').write('\n'.join(lines))
print('lines=%d' % len(lines), file=sys.stderr)