"""Junta presidente por município (data/pres/{ano}.json, códigos TSE) com a malha do IBGE.

Saídas em data/mapa/:
  geo.json        caminhos SVG por município (código IBGE) e contorno das UFs
  {ano}.json      {"t":{"1":{ibge:[aptos,comparecimento,validos,PT,BOL]},"2":{...}},"cand":{...},"tse":{ibge:tse}}
  resumo.json     totais, cidades vencidas, viradas, mudança por região
"""
import json, os, re, sys, unicodedata
from collections import defaultdict
RAIZ = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
GEO, OUT = sys.argv[1], os.path.join(RAIZ, "data", "mapa")
PT = "13"; BOL = {2018: "17", 2022: "22", 2026: "22"}
MANUAL = {("RN", "BOA SAUDE"): "2405306", ("RN", "ASSU"): "2400208", ("RN", "AREZ"): "2401206", ("GO", "BOM JESUS"): "5203500",
          ("SE", "AMPARO DE SAO FRANCISCO"): "2800100", ("MG", "SAO THOME DAS LETRAS"): "3165206", ("SP", "SAO LUIS DO PARAITINGA"): "3550001",
          ("PR", "MUNHOZ DE MELLO"): "4116307", ("SE", "GRACCHO CARDOSO"): "2802601", ("MG", "DONA EUSEBIA"): "3122900",
          ("RO", "ESPIGAO DO OESTE"): "1100098", ("PA", "ELDORADO DOS CARAJAS"): "1502954", ("RO", "ALVORADA DO OESTE"): "1100346",
          ("MT", "SANTO ANTONIO DO LEVERGER"): "5107800"}
REG = {"N": "RO AC AM RR PA AP TO", "NE": "MA PI CE RN PB PE AL SE BA", "SE": "MG ES RJ SP", "S": "PR SC RS", "CO": "MS MT GO DF"}
REGN = {"N": "Norte", "NE": "Nordeste", "SE": "Sudeste", "S": "Sul", "CO": "Centro-Oeste", "EX": "Exterior"}
UF2R = {u: r for r, us in REG.items() for u in us.split()}
def k(s):
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().upper()
    return " ".join(re.sub(r"[^A-Z ]", " ", s).split())

G = json.load(open(GEO))
ib = {(uf, k(n)): cd for cd, (n, uf, d) in G["m"].items()}
os.makedirs(OUT, exist_ok=True)
json.dump(G, open(os.path.join(OUT, "geo.json"), "w"), ensure_ascii=False, separators=(",", ":"))

res = {"anos": {}, "sem_mapa": []}
dados = {}
for ano in (2018, 2022, 2026):
    D = json.load(open(os.path.join(RAIZ, "data", "pres", f"{ano}.json")))
    tse = {}
    for cd, (n, uf) in D["mun"].items():
        if uf == "ZZ": continue
        i = ib.get((uf, k(n))) or MANUAL.get((uf, k(n)))
        if i: tse[cd] = i
        elif ano == 2026: res["sem_mapa"].append(f"{n.title()} ({uf})")
    out = {"ano": ano, "cand": {}, "t": {}, "tse": {v: c for c, v in tse.items()}}
    R = {}
    for t, M in D["t"].items():
        ordm = D["ord"][t]; ip, ib_ = ordm.index(PT) if PT in ordm else None, ordm.index(BOL[ano]) if BOL[ano] in ordm else None
        out["cand"][t] = {"pt": D["cand"][t][PT], "bol": D["cand"][t][BOL[ano]]}
        tt, reg = {}, defaultdict(lambda: [0, 0, 0, 0, 0])
        for cd, v in M.items():
            vs = v[4:]; row = [v[0], v[1], sum(vs), vs[ip] if ip is not None else 0, vs[ib_] if ib_ is not None else 0]
            uf = D["mun"][cd][1]; rg = UF2R.get(uf, "EX")
            for j in range(5): reg[rg][j] += row[j]
            if cd in tse: tt[tse[cd]] = row
        out["t"][t] = tt
        venc = {"pt": sum(1 for r in tt.values() if r[3] > r[4]), "bol": sum(1 for r in tt.values() if r[4] > r[3])}
        R[t] = {"reg": {REGN[r]: x for r, x in reg.items()}, "venceu": venc}
    dados[ano] = out
    res["anos"][ano] = {"cand": out["cand"], "t": R}
    json.dump(out, open(os.path.join(OUT, f"{ano}.json"), "w"), ensure_ascii=False, separators=(",", ":"))

# viradas no 2º turno 2022 -> 2026
a, b = dados[2022]["t"]["2"], dados[2026]["t"]["2"]
vir = {"pt": 0, "bol": 0}
for cd in b:
    if cd not in a: continue
    w0 = "pt" if a[cd][3] > a[cd][4] else "bol"; w1 = "pt" if b[cd][3] > b[cd][4] else "bol"
    if w0 != w1: vir[w1] += 1
res["viradas_2022_2026"] = vir
json.dump(res, open(os.path.join(OUT, "resumo.json"), "w"), ensure_ascii=False, separators=(",", ":"))
for ano in res["anos"]:
    for t, x in res["anos"][ano]["t"].items():
        print(ano, t, "cidades:", x["venceu"], "| margem PT por região:", {r: v[3] - v[4] for r, v in x["reg"].items()})
print("viradas 2022->2026:", vir, "| sem mapa:", res["sem_mapa"])
for f in sorted(os.listdir(OUT)): print(f, os.path.getsize(os.path.join(OUT, f)) // 1024, "KB")
