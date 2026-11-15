"""Voto por local de votação (TSE) para uma lista de cidades.

Uso: python pipeline/secao.py SP 66397 [outros códigos TSE...]
Anos: 2020 e 2024 (prefeito e vereador), 2022 e 2026 (presidente).

Saída: data/secao/{cd}.json
{"cd","nome","uf",
 "locais":{"zona-local":[nome,endereço,bairro,lat,lon]},
 "el":{"2024":{"11-1":{"cand":{nr:nome},"loc":{"zona-local":[aptos,comparecimento,{nr:votos}]}}, "13-1":{...}}, ...}}
Chave "cargo-turno": 1 = presidente, 11 = prefeito, 13 = vereador. Brancos = 95, nulos = 96 (como no TSE).
"""
import csv, io, json, os, sys, tempfile, zipfile
from collections import defaultdict
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from municipais import BASE, baixar, n

RAIZ = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
OUT = os.path.join(RAIZ, "data", "secao")
TODOS = {2020: ("11", "13"), 2022: ("1",), 2024: ("11", "13"), 2026: ("1",)}
# Os arquivos de 2022 e 2026 trazem todos os cargos estaduais e federais e são muito grandes; por padrão só os municipais.
ANOS = {int(a): TODOS[int(a)] for a in os.environ.get("ANOS", "2020 2024").split()}


def col(r, *nomes):
    for k in nomes:
        if k in r and r[k] not in (None, ""):
            return r[k]
    return ""


def linhas(zpath, filtro_uf=None):
    with zipfile.ZipFile(zpath) as z:
        nomes = [m for m in z.namelist() if m.lower().endswith(".csv")]
        if filtro_uf:
            sel = [m for m in nomes if m.upper().endswith(f"_{filtro_uf}.CSV")]
            nomes = sel or nomes
        for m in nomes:
            print("   lendo", m, flush=True)
            with z.open(m) as raw:
                rd = csv.DictReader(io.TextIOWrapper(raw, encoding="latin-1", newline=""), delimiter=";", quotechar='"')
                print("   colunas:", ",".join(rd.fieldnames or [])[:400], flush=True)
                for r in rd:
                    yield r


def main(uf, cods):
    cods = set(c.lstrip("0") for c in cods)
    tmp = tempfile.mkdtemp()
    out = {c: {"cd": c, "nome": "", "uf": uf, "locais": {}, "el": {}} for c in cods}
    for ano, cargos in ANOS.items():
        url = f"{BASE}/votacao_secao/votacao_secao_{ano}_{uf}.zip"
        try:
            z = baixar(url, os.path.join(tmp, f"vs_{ano}.zip"))
        except Exception as e:
            print("  sem arquivo", url, e, flush=True); continue
        agg = defaultdict(lambda: {"cand": {}, "loc": defaultdict(lambda: [0, 0, defaultdict(int)]), "secoes": set()})
        for r in linhas(z):
            cd = r.get("CD_MUNICIPIO", "").lstrip("0")
            if cd not in cods or r.get("CD_CARGO") not in cargos: continue
            if r.get("CD_TIPO_ELEICAO", "2") != "2": continue
            o = out[cd]; o["nome"] = r.get("NM_MUNICIPIO", o["nome"])
            loc = f'{r["NR_ZONA"]}-{col(r, "NR_LOCAL_VOTACAO")}'
            if loc not in o["locais"]:
                o["locais"][loc] = [col(r, "NM_LOCAL_VOTACAO"), col(r, "DS_LOCAL_VOTACAO_ENDERECO", "DS_ENDERECO"), "", None, None]
            key = (cd, f'{r["CD_CARGO"]}-{r["NR_TURNO"]}')
            A = agg[key]; nr = r["NR_VOTAVEL"]
            A["cand"][nr] = col(r, "NM_VOTAVEL")
            L = A["loc"][loc]; L[2][nr] += n(r["QT_VOTOS"])
            sk = (loc, r["NR_SECAO"])
            if sk not in A["secoes"]:
                A["secoes"].add(sk)
                L[0] += n(col(r, "QT_APTOS")); L[1] += n(col(r, "QT_COMPARECIMENTO"))
        for (cd, k), A in agg.items():
            out[cd]["el"].setdefault(str(ano), {})[k] = {"cand": A["cand"], "loc": {l: [v[0], v[1], dict(v[2])] for l, v in A["loc"].items()}}
            tot = defaultdict(int)
            for v in A["loc"].values():
                for nr, q in v[2].items(): tot[nr] += q
            top = sorted(tot.items(), key=lambda x: -x[1])[:3]
            print(f"  {cd} {ano} {k}: {len(A['loc'])} locais; " + ", ".join(f"{A['cand'][nr]} {q:,}" for nr, q in top), flush=True)
        os.remove(z)
    # endereço, bairro e coordenadas dos locais de votação
    for ano in (2026, 2024, 2022):
        url = f"{BASE}/eleitorado_locais_votacao/eleitorado_local_votacao_{ano}.zip"
        try:
            z = baixar(url, os.path.join(tmp, f"lv_{ano}.zip"))
        except Exception as e:
            print("  sem arquivo", url, e, flush=True); continue
        achou = 0
        for r in linhas(z, uf):
            cd = r.get("CD_MUNICIPIO", "").lstrip("0")
            if cd not in cods: continue
            loc = f'{r.get("NR_ZONA")}-{r.get("NR_LOCAL_VOTACAO")}'
            L = out[cd]["locais"].get(loc)
            if not L or L[3] is not None: continue
            L[2] = col(r, "NM_BAIRRO")
            try:
                lat, lon = float(col(r, "NR_LATITUDE").replace(",", ".")), float(col(r, "NR_LONGITUDE").replace(",", "."))
                if lat != -1 and lon != -1 and -35 < lat < 6 and -75 < lon < -30: L[3], L[4] = round(lat, 5), round(lon, 5)
            except ValueError:
                pass
            if not L[1]: L[1] = col(r, "DS_ENDERECO")
            achou += 1
        os.remove(z)
        print(f"  locais com bairro/coordenada via {ano}: {achou}", flush=True)
        if all(all(l[3] is not None for l in o["locais"].values()) for o in out.values()): break
    os.makedirs(OUT, exist_ok=True)
    for cd, o in out.items():
        sem = sum(1 for l in o["locais"].values() if l[3] is None)
        print(f"{cd} {o['nome']}: {len(o['locais'])} locais, {sem} sem coordenada", flush=True)
        with open(os.path.join(OUT, f"{cd}.json"), "w", encoding="utf-8") as f:
            json.dump(o, f, ensure_ascii=False, separators=(",", ":"))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2:])
