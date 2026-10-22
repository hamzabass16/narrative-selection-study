import json, base64, zlib, sys, os
src, outdir = sys.argv[1], sys.argv[2]
t = json.load(open(src))[0]['text']
t = t[t.index('@@FILE'):]
for block in t.split('@@FILE ')[1:]:
    head, _, body = block.partition('\n')
    parts = head.split()
    name, method, usz = parts[0], int(parts[1]), int(parts[2])
    raw = base64.b64decode(body.strip())
    data = zlib.decompress(raw, -15) if method == 8 else raw
    assert len(data) == usz, (name, len(data), usz)
    open(os.path.join(outdir, name), 'wb').write(data)
    print(name, len(data))
