"""Canadá (Elections Canada, 45ª eleição geral, 28/04/2025, resultados oficiais por província) -> data/mundo/ca.json

Uso: python pipeline/mundo_ca.py table_tableau03.csv table_tableau08.csv OUT_DIR
Fonte: https://www.elections.ca/res/rep/off/ovrGE45/ (tabelas 3 e 8 dos resultados oficiais).
"""
import csv, io, json, os, sys

T3, T8, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
OUTRO = "#5B6478"
PART = [("LPC", "Liberais", "Liberal Party", "Mark Carney", "#E0353D"), ("CPC", "Conservadores", "Conservative Party", "Pierre Poilievre", "#3B78EA"),
        ("BQ", "Bloco Quebequense", "Bloc Qu", "Yves-François Blanchet", "#38B2C9"), ("NDP", "Novo Partido Democrático", "New Democratic", "Jagmeet Singh", "#F28C28"),
        ("GPC", "Verdes", "Green Party", "", "#3FAE5A"), ("PPC", "Partido Popular", "People's Party", "Maxime Bernier", "#7C5CE0")]
PROV = ["Terra Nova e Labrador", "Ilha do Príncipe Eduardo", "Nova Escócia", "Nova Brunswick", "Quebec", "Ontário", "Manitoba", "Saskatchewan",
        "Alberta", "Colúmbia Britânica", "Yukon", "Territórios do Noroeste", "Nunavut"]


def ler(p):
    return list(csv.reader(io.StringIO(open(p, encoding="utf-8-sig", errors="replace").read())))


t3 = ler(T3)[1:]
t8 = ler(T8)
reg = []
for i, nome in enumerate(PROV):
    _, pop, ele, val, _, rej, _, tot, _ = t3[i]
    reg.append({"id": str(i), "n": nome, "eleitores": int(ele), "votantes": int(tot), "brancos": None, "nulos": int(rej), "validos": int(val),
                "v": {k: 0 for k, *_ in PART} | {"O": 0}})
for row in t8[1:]:
    k = next((k for k, _, pref, *_ in PART if row[0].startswith(pref)), "O")
    for i in range(len(PROV)):
        reg[i]["v"][k] += int(row[1 + i] or 0)
for r in reg:
    assert sum(r["v"].values()) == r["validos"], r["n"]
nac = {x: sum(r[x] for r in reg) for x in ("eleitores", "votantes", "nulos", "validos")}; nac["brancos"] = None
nac["v"] = {k: sum(r["v"][k] for r in reg) for k in reg[0]["v"]}
print("eleitores", nac["eleitores"], "votantes", nac["votantes"], f'({nac["votantes"]/nac["eleitores"]*100:.1f}%)', "válidos", nac["validos"])
for k, nome, *_ in PART:
    print("   ", nome, nac["v"][k], f'{nac["v"][k]/nac["validos"]*100:.2f}%')
cands = [{"id": k, "nome": nome, "grupo": lider, "cor": cor} for k, nome, _, lider, cor in PART] + [{"id": "O", "nome": "Outros", "grupo": "", "cor": OUTRO}]
P = {"pais": "CA", "nome": "Canadá", "nivel": "Província", "sistema": "Parlamentar", "parlamentar": True,
     "fonte": "Elections Canada, resultados oficiais da 45ª eleição geral (28/04/2025)", "fonte_url": "https://www.elections.ca/res/rep/off/ovrGE45/home.html",
     "nota": "Eleição parlamentar por voto distrital em 343 circunscrições; o primeiro-ministro é o líder do partido que comanda a maioria na Câmara dos Comuns. Percentual sobre votos válidos. O Bloco Quebequense só concorre no Quebec.",
     "eleicoes": [{"ano": 2025, "turnos": {"1": {"cand": cands, "nac": nac, "reg": reg}}}]}
os.makedirs(OUT, exist_ok=True)
json.dump(P, open(os.path.join(OUT, "ca.json"), "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
