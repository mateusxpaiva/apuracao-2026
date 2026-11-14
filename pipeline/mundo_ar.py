"""Argentina: agrega resultados provisórios da DINE (mesa a mesa) por província, cargo Presidente."""
import csv, io, json, sys, zipfile, collections
ARQS = {("2015","1"):"2015_generales.zip",("2015","2"):"2015_ballotage.zip",("2019","1"):"2019_generales.zip",
        ("2023","1"):"2023_generales.zip",("2023","2"):"2023_segundavuelta.zip"}
def proc(path):
    z = zipfile.ZipFile(path)
    m = [n for n in z.namelist() if "esultado" in n and n.endswith(".csv")][0]
    f = io.TextIOWrapper(z.open(m), encoding="utf-8", newline="")
    r = csv.reader(f); h = next(r); ix = {k:i for i,k in enumerate(h)}
    cargos = collections.Counter()
    D = {}
    mesas = set()
    for row in r:
        cn = row[ix["cargo_nombre"]]
        if row[ix["cargo_id"]] != "1":
            continue
        cargos[cn] += 1
        did = int(row[ix["distrito_id"]]); dn = row[ix["distrito_nombre"]]
        d = D.setdefault(did, {"n":dn, "electores":0, "tipos":collections.Counter(), "ag":collections.Counter(), "agn":{}})
        key = (did, row[ix["seccion_id"]], row[ix["circuito_id"]], row[ix["mesa_id"]], row[ix.get("mesa_tipo", ix["mesa_id"])])
        if key not in mesas:
            mesas.add(key)
            try: d["electores"] += int(row[ix["mesa_electores"]] or 0)
            except ValueError: pass
        vt = row[ix["votos_tipo"]]; v = int(row[ix["votos_cantidad"]] or 0)
        d["tipos"][vt] += v
        if vt == "POSITIVO":
            a = row[ix["agrupacion_id"]].lstrip("0"); d["ag"][a] += v; d["agn"][a] = row[ix["agrupacion_nombre"]].strip()
    return D, cargos
if __name__ == "__main__":
    base = sys.argv[1]; out = {}
    for (ano,t),fn in ARQS.items():
        D, cargos = proc(f"{base}/{fn}")
        print(ano, t, dict(cargos), file=sys.stderr)
        out.setdefault(ano, {})[t] = {str(k):{"n":v["n"],"electores":v["electores"],"tipos":dict(v["tipos"]),"ag":dict(v["ag"]),"agn":v["agn"]} for k,v in sorted(D.items())}
    json.dump(out, open(sys.argv[2],"w"), ensure_ascii=False)
