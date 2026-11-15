"""Painel (cockpit da página inicial): resume os dados já publicados no site por município e por UF.

Uso: python pipeline/painel_build.py            (lê data/ e grava data/painel/)
Entradas: data/mapa/{2018,2022,2026}.json (presidente por município, código IBGE),
          data/mun/{2020,2024}/{UF}.json e {UF}_v.json (prefeitos e vereadores, código TSE),
          data/congresso/{camara,senado,gastos}.json, data/pesquisas/{2026,acerto}.json, data/mun/resumo.json,
          data/mundo/*.json, calendario/index.html (lista EV),
          pipeline/ibge_municipios.csv (coordenadas das sedes municipais; github.com/kelvins/municipios-brasileiros, licença MIT, base IBGE).
Saídas:   data/painel/mun.json   [[ibge, nome, uf, lat, lon, eleitores 2026], ...] para busca e localização
          data/painel/{UF}.json  dados da UF e de cada município
          data/painel/brasil.json indicadores nacionais, calendário e mundo
"""
import csv, json, os, re
from collections import Counter, defaultdict

R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D = lambda *p: os.path.join(R, "data", *p)
OUT = D("painel"); os.makedirs(OUT, exist_ok=True)
load = lambda *p: json.load(open(D(*p), encoding="utf-8"))
UFC = {"11": "RO", "12": "AC", "13": "AM", "14": "RR", "15": "PA", "16": "AP", "17": "TO", "21": "MA", "22": "PI", "23": "CE", "24": "RN", "25": "PB",
       "26": "PE", "27": "AL", "28": "SE", "29": "BA", "31": "MG", "32": "ES", "33": "RJ", "35": "SP", "41": "PR", "42": "SC", "43": "RS", "50": "MS",
       "51": "MT", "52": "GO", "53": "DF"}
UFN = {"AC": "Acre", "AL": "Alagoas", "AP": "Amapá", "AM": "Amazonas", "BA": "Bahia", "CE": "Ceará", "DF": "Distrito Federal", "ES": "Espírito Santo",
       "GO": "Goiás", "MA": "Maranhão", "MT": "Mato Grosso", "MS": "Mato Grosso do Sul", "MG": "Minas Gerais", "PA": "Pará", "PB": "Paraíba", "PR": "Paraná",
       "PE": "Pernambuco", "PI": "Piauí", "RJ": "Rio de Janeiro", "RN": "Rio Grande do Norte", "RS": "Rio Grande do Sul", "RO": "Rondônia", "RR": "Roraima",
       "SC": "Santa Catarina", "SP": "São Paulo", "SE": "Sergipe", "TO": "Tocantins"}

# ---- municípios: nome, UF, coordenadas, código TSE
K = {r["codigo_ibge"]: r for r in csv.DictReader(open(os.path.join(R, "pipeline", "ibge_municipios.csv"), encoding="utf-8"))}
MAPA = {a: load("mapa", f"{a}.json") for a in (2018, 2022, 2026)}
TSE = {}
for a in (2018, 2022, 2026):
    TSE.update(MAPA[a]["tse"])
mun_idx, porUF = [], defaultdict(dict)
for ib, r in K.items():
    if ib not in MAPA[2026]["t"]["2"]:
        continue  # Boa Esperança do Norte (MT), criado em 2023, ainda sem resultado próprio
    uf = UFC[r["codigo_uf"]]
    mun_idx.append([ib, r["nome"], uf, round(float(r["latitude"]), 4), round(float(r["longitude"]), 4), MAPA[2026]["t"]["2"][ib][0]])
    porUF[uf][ib] = {"n": r["nome"], "cap": r["capital"] == "1", "tse": TSE.get(ib)}
mun_idx.sort(key=lambda x: (x[1], x[2]))

# ---- presidente (2º turno; 2026 também 1º turno) por município e UF
ufpres = defaultdict(lambda: defaultdict(lambda: [0] * 5))
for a, M in MAPA.items():
    for t in ("1", "2"):
        if t == "1" and a != 2026: continue
        for ib, row in M["t"][t].items():
            uf = UFC.get(ib[:2])
            if not uf or ib not in porUF[uf]: continue
            porUF[uf][ib].setdefault("p", {})[f"{a}" if t == "2" else f"{a}t1"] = row
            acc = ufpres[uf][f"{a}" if t == "2" else f"{a}t1"]
            for i, x in enumerate(row): acc[i] += x
CAND = {str(a): MAPA[a]["cand"]["2"] for a in MAPA}

# ---- prefeitos e vereadores (2024, e partido do prefeito em 2020)
def eleito(m):
    for t in ("2", "1"):
        if t in m["p"]:
            for c in m["p"][t]["c"]:
                if c[4] == "E":
                    tot = m["p"][t]["t"][3] or 1
                    return [c[1], c[2], round(c[3] / tot * 100, 1), int(t)]
    return None

tse2ib = {}
for uf, ms in porUF.items():
    for ib, x in ms.items():
        if x["tse"]: tse2ib[x["tse"]] = (uf, ib)
ufpref, ufver = defaultdict(Counter), defaultdict(Counter)
for uf in porUF:
    for ano in (2020, 2024):
        p = D("mun", str(ano), f"{uf}.json")
        if not os.path.exists(p): continue
        M = json.load(open(p, encoding="utf-8"))["mun"]
        for cd, m in M.items():
            if cd not in tse2ib: continue
            ib = tse2ib[cd][1]; e = eleito(m)
            if ano == 2024:
                porUF[uf][ib]["pf"] = e
                t = m["p"]["1"]["t"]; porUF[uf][ib]["m24"] = [t[0], t[1]]
                if e: ufpref[uf][e[1]] += 1
            else:
                porUF[uf][ib]["pf20"] = [e[0], e[1]] if e else None
    p = D("mun", "2024", f"{uf}_v.json")
    if os.path.exists(p):
        V = json.load(open(p, encoding="utf-8"))["mun"]
        for cd, m in V.items():
            if cd not in tse2ib: continue
            c = Counter(x[2] for x in m["c"] if x[4] == "E")
            porUF[uf][tse2ib[cd][1]]["vr"] = dict(c.most_common())
            ufver[uf].update(c)

# ---- Congresso por UF
CAM, SEN, GAS = load("congresso", "camara.json"), load("congresso", "senado.json"), load("congresso", "gastos.json")
nv = len(CAM["votacoes"]); gasto = {g["id"]: g["total"] for g in GAS["deputados"]}
deps = defaultdict(list)
for i in CAM["atuais"]:
    nome, part, uf = CAM["deputados"][i]
    p = CAM["perfil"].get(i, [0, 0, 0])
    deps[uf].append([nome, part, round(p[0] / nv * 100) if nv else None, round(p[2] / p[1] * 100) if p[1] else None, round(gasto.get(i, 0))])
sens = defaultdict(list)
for i, (nome, part, uf) in SEN["senadores"].items():
    sens[uf].append([nome, part])

PESQ = load("pesquisas", "2026.json")
for uf, ms in porUF.items():
    out = {"uf": uf, "nome": UFN[uf], "pres": ufpres[uf], "prefeitos": dict(ufpref[uf].most_common()), "vereadores": dict(ufver[uf].most_common()),
           "deputados": sorted(deps[uf], key=lambda d: d[0]), "senadores": sorted(sens[uf]), "pesquisas": PESQ["uf"].get(uf, 0), "mun": ms}
    json.dump(out, open(os.path.join(OUT, f"{uf}.json"), "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
json.dump(mun_idx, open(os.path.join(OUT, "mun.json"), "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))

# ---- Brasil
RES = load("mapa", "resumo.json"); MR = load("mun", "resumo.json"); AC = load("pesquisas", "acerto.json")
def soma(a, t):
    s = [0] * 5
    for v in RES["anos"][str(a)]["t"][t]["reg"].values():
        for i, x in enumerate(v): s[i] += x
    return s
pres = {str(a): {"t2": soma(a, "2"), "venceu": RES["anos"][str(a)]["t"]["2"]["venceu"], "cand": CAND[str(a)]} for a in (2018, 2022, 2026)}
pres["2026"]["t1"] = soma(2026, "1")
e26 = AC["eleicoes"][0]
acerto = sorted([[p[0], round(abs(p[1] - e26["oficial"][0]), 1)] for p in e26["pesquisas"]], key=lambda x: x[1])
gov = [v for v in CAM["votacoes"] if v.get("gov")]
# calendário: lê a lista EV da página do calendário
cal = []
src = open(os.path.join(R, "calendario", "index.html"), encoding="utf-8").read()
for blk in src[src.index("var EV = ["):src.index("];", src.index("var EV = ["))].split("{d:")[1:]:
    f = dict(re.findall(r'\b(d|d2|pais|f|o|link):"([^"]*)"', "d:" + blk))
    cal.append([f["d"], f.get("d2"), f["pais"], f["f"], f["o"], f.get("link", "").replace("../", "")])
# mundo: comparecimento e margem do turno decisivo da eleição mais recente
mundo = []
for f in sorted(os.listdir(D("mundo"))):
    P = load("mundo", f); e = P["eleicoes"][-1]; T = e["turnos"][max(e["turnos"])]; n = T["nac"]
    vs = sorted(n["v"].items(), key=lambda kv: -kv[1]); vs = [kv for kv in vs if kv[0] != "O"] or vs
    marg = (vs[0][1] - vs[1][1]) / n["validos"] * 100 if len(vs) > 1 and n["validos"] else None
    win = next((c["nome"] for c in T["cand"] if c["id"] == vs[0][0]), vs[0][0])
    mundo.append([f[:2], P["nome"], e["ano"], round(n["votantes"] / n["eleitores"] * 100, 1) if n.get("eleitores") else None,
                  round(marg, 1) if marg is not None else None, win, bool(P.get("parlamentar"))])
BR = {"atualizado": CAM["atualizado"], "pres": pres, "viradas": RES["viradas_2022_2026"],
      "municipais": {"2024": {k: MR["por_ano"]["2024"][k] for k in ("municipios", "aptos", "comparecimento", "segundo_turno")},
                     "prefeitos": MR["por_ano"]["2024"]["prefeitos_por_partido"], "reeleicao": MR["reeleicao"]["2020-2024"]},
      "congresso": {"votacoes_camara": nv, "votacoes_senado": len(SEN["votacoes"]), "deputados": len(CAM["atuais"]), "gastos": round(GAS["total"]),
                    "ultima": (lambda v: [v["data"][:10], v.get("titulo") or "", v["aprovada"]])(max(CAM["votacoes"], key=lambda v: v["data"]))},
      "pesquisas": {"total": PESQ["total"], "institutos": PESQ["institutos"], "valor": round(PESQ["valor"]), "entrevistas": PESQ["entrevistas"],
                    "presidente": PESQ["cargo"].get("Presidente", 0), "acerto": acerto, "oficial": e26["oficial"]},
      "calendario": cal, "mundo": mundo, "ufs": {u: [UFN[u], ufpres[u]["2026"]] for u in sorted(ufpres)}}
json.dump(BR, open(os.path.join(OUT, "brasil.json"), "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))

# ---- conferências
n26 = BR["pres"]["2026"]["t2"]
assert round(n26[3] / n26[2] * 100, 2) == 51.79, n26
assert sum(len(v["mun"]) for v in [json.load(open(os.path.join(OUT, f"{u}.json"))) for u in porUF]) == len(mun_idx) == 5570
print("municípios", len(mun_idx), "| Lula 2026", round(n26[3] / n26[2] * 100, 2), "| sem prefeito:", sum(1 for u in porUF for m in porUF[u].values() if not m.get("pf")),
      "| calendário", len(cal), "| mundo", len(mundo))
for f in sorted(os.listdir(OUT)): print(f, os.path.getsize(os.path.join(OUT, f)))
