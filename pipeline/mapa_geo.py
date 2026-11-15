import json, math, sys
src, out, W = sys.argv[1], sys.argv[2], float(sys.argv[3])
G = json.load(open(src))
feats = G["features"]
lat0 = math.radians(-15)
def proj(lon, lat): return (lon * math.cos(lat0), -lat)
xs, ys = [], []
for f in feats:
    g = f["geometry"]; polys = g["coordinates"] if g["type"] == "MultiPolygon" else [g["coordinates"]]
    for p in polys:
        for r in p:
            for lon, lat in r:
                x, y = proj(lon, lat); xs.append(x); ys.append(y)
x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
s = W / (x1 - x0); H = (y1 - y0) * s
Q = float(sys.argv[4])  # tamanho da grade em px
def q(lon, lat):
    x, y = proj(lon, lat); return (round((x - x0) * s / Q), round((y - y0) * s / Q))
def ring(r):
    pts = []
    for lon, lat in r:
        p = q(lon, lat)
        if not pts or pts[-1] != p: pts.append(p)
    # remove colineares
    out = []
    for p in pts:
        while len(out) >= 2:
            a, b = out[-2], out[-1]
            if (b[0]-a[0])*(p[1]-a[1]) - (b[1]-a[1])*(p[0]-a[0]) == 0: out.pop()
            else: break
        out.append(p)
    if len(out) < 3: return ""
    d = "M%d %d" % out[0]
    px, py = out[0]
    for x, y in out[1:]:
        d += "l%d %d" % (x - px, y - py); px, py = x, y
    return d + "z"
res, npts = {}, 0
for f in feats:
    g = f["geometry"]; polys = g["coordinates"] if g["type"] == "MultiPolygon" else [g["coordinates"]]
    d = "".join(ring(r) for p in polys for r in p[:1])
    res[str(f["properties"]["id"])] = [f["properties"].get("nome") or f["properties"].get("name"), f["properties"].get("uf",""), d]
uf = {}
if len(sys.argv) > 5:
    for f in json.load(open(sys.argv[5]))["features"]:
        g = f["geometry"]; polys = g["coordinates"] if g["type"] == "MultiPolygon" else [g["coordinates"]]
        p = f["properties"]; uf[str(p.get("sigla") or p.get("uf") or p.get("id"))] = "".join(ring(r) for pp in polys for r in pp[:1])
json.dump({"uf": uf, "w": round(W / Q), "h": round(H / Q), "q": Q, "m": res}, open(out, "w"), ensure_ascii=False, separators=(",", ":"))
import os; print(len(res), "mun", os.path.getsize(out) // 1024, "KB", "viewBox", round(W/Q), round(H/Q))
