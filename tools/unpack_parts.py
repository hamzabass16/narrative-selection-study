import json, base64, zlib, sys, os, collections
outdir = sys.argv[1]; srcs = sys.argv[2:]
parts = collections.defaultdict(dict); meta = {}
for src in srcs:
    t = json.load(open(src))[0]['text']
    for block in t.split('@@PART ')[1:]:
        head, _, body = block.partition('\n')
        name, method, usz, i, k = head.split()
        parts[name][int(i)] = body.strip(); meta[name] = (int(method), int(usz), int(k))
for name, (method, usz, k) in meta.items():
    assert sorted(parts[name]) == list(range(k)), (name, sorted(parts[name]))
    raw = base64.b64decode(''.join(parts[name][i] for i in range(k)))
    data = zlib.decompress(raw, -15) if method == 8 else raw
    assert len(data) == usz, (name, len(data), usz)
    open(os.path.join(outdir, name), 'wb').write(data); print(name, len(data))
