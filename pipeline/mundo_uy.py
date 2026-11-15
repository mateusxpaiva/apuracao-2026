"""Uruguai (Corte Electoral, eleições nacionais e balotaje de 2024, escrutínio por departamento) -> data/mundo/uy.json

Uso: python pipeline/mundo_uy.py desglose-de-votos.csv totales-generales-...csv balotaje-2024.csv OUT_DIR
Fonte: catálogo de dados abertos do Uruguai (catalogodatos.gub.uy, conjuntos da Corte Electoral).
No 1º turno, o voto de cada partido soma as listas (HOJA_EN) e o voto só na legenda (VOTO_LEMA).
"""
import csv, json, os, sys
from collections import defaultdict

DESG, TOT, BAL, OUT = sys.argv[1:5]
OUTRO = "#5B6478"
DEP = {"MO": "Montevidéu", "CA": "Canelones", "MA": "Maldonado", "SA": "Salto", "PA": "Paysandú", "CO": "Colonia", "SJ": "San José", "RV": "Rivera",
       "TA": "Tacuarembó", "SO": "Soriano", "CL": "Cerro Largo", "AR": "Artigas", "RN": "Río Negro", "RO": "Rocha", "LA": "Lavalleja", "FD": "Florida",
       "DU": "Durazno", "TT": "Treinta y Tres", "FS": "Flores"}
PART = {"Partido Frente Amplio": ("FA", "Yamandú Orsi", "Frente Amplio", "#E0353D"), "Partido Nacional": ("PN", "Álvaro Delgado", "Partido Nacional", "#38B2C9"),
        "Partido Colorado": ("PC", "Andrés Ojeda", "Partido Colorado", "#F28C28"), "Partido Identidad Soberana": ("IS", "Gustavo Salle", "Identidad Soberana", "#7C5CE0"),
        "Partido Cabildo Abierto": ("CA", "Guido Manini Ríos", "Cabildo Abierto", "#E2B84B")}


def n(x):
    return int(x) if (x or "").strip() else 0


def montar(reg, cands):
    out = []
    for k in sorted(reg, key=lambda k: -reg[k]["eleitores"]):
        g = reg[k]
        g["validos"] = sum(g["v"].values())
        g["brancos"] = g["votantes"] - g["validos"] - g["nulos"]
        out.append({"id": k, "n": DEP[k], **{x: g[x] for x in ("eleitores", "votantes", "brancos", "nulos", "validos")}, "v": dict(g["v"])})
    nac = {x: sum(r[x] for r in out) for x in ("eleitores", "votantes", "brancos", "nulos", "validos")}
    nac["v"] = {c["id"]: sum(r["v"].get(c["id"], 0) for r in out) for c in cands}
    return {"cand": cands, "nac": nac, "reg": out}


# 1º turno
reg1 = defaultdict(lambda: {"eleitores": 0, "votantes": 0, "brancos": 0, "nulos": 0, "validos": 0, "v": defaultdict(int)})
for r in csv.DictReader(open(TOT, encoding="utf-8-sig")):
    g = reg1[r["Departamento"]]
    g["eleitores"] += n(r["TotalHabilitados"]); g["votantes"] += n(r["TotalVotosEmitidos"]); g["nulos"] += n(r["TotalAnulados"])
for r in csv.DictReader(open(DESG, encoding="utf-8-sig")):
    k = PART.get(r["Lema"], ("O",))[0]
    reg1[r["Departamento"]]["v"][k] += n(r["CantidadVotos"])
c1 = [{"id": k, "nome": nome, "grupo": grupo, "cor": cor} for k, nome, grupo, cor in PART.values()] + [{"id": "O", "nome": "Outros partidos", "grupo": "", "cor": OUTRO}]
t1 = montar(reg1, c1)
# balotaje
reg2 = defaultdict(lambda: {"eleitores": 0, "votantes": 0, "brancos": 0, "nulos": 0, "validos": 0, "v": defaultdict(int)})
for r in csv.DictReader(open(BAL, encoding="utf-8-sig")):
    g = reg2[r["Departamento"]]
    g["eleitores"] += n(r["TotalHabilitados"]); g["votantes"] += n(r["TotalVotosEmitidos"]); g["nulos"] += n(r["TotalAnulados"])
    g["v"]["FA"] += n(r["TotalOrsiCosse"]); g["v"]["PN"] += n(r["TotalDelgadoRipoll"])
c2 = [{"id": "FA", "nome": "Yamandú Orsi", "grupo": "Frente Amplio", "cor": "#E0353D"}, {"id": "PN", "nome": "Álvaro Delgado", "grupo": "Partido Nacional · apoio da Coalizão Republicana", "cor": "#38B2C9"}]
t2 = montar(reg2, c2)
for k, t in (("1", t1), ("2", t2)):
    nn = t["nac"]
    print(k, "habilitados", nn["eleitores"], "emitidos", nn["votantes"], "válidos", nn["validos"], "brancos/outros", nn["brancos"], "anulados", nn["nulos"])
    for c in t["cand"][:5]:
        print("   ", c["nome"], nn["v"][c["id"]], f'{nn["v"][c["id"]]/nn["validos"]*100:.2f}% válidos', f'{nn["v"][c["id"]]/nn["votantes"]*100:.2f}% emitidos')
P = {"pais": "UY", "nome": "Uruguai", "nivel": "Departamento", "sistema": "2 turnos",
     "fonte": "Corte Electoral, escrutínio de 27/10 e 24/11/2024 por circuito (catalogodatos.gub.uy)", "fonte_url": "https://catalogodatos.gub.uy/organization/corte-electoral",
     "nota": "Percentual sobre votos válidos, para comparar com os outros países; a Corte Electoral divulga sobre o total de votos emitidos (Orsi teve 49,8% dos emitidos no balotaje). No 1º turno o voto vai para o partido (lema); aparece o nome do candidato presidencial de cada um. Brancos inclui quem votou só no plebiscito.",
     "eleicoes": [{"ano": 2024, "turnos": {"1": t1, "2": t2}}]}
os.makedirs(OUT, exist_ok=True)
json.dump(P, open(os.path.join(OUT, "uy.json"), "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
