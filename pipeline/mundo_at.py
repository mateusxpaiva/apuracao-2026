"""Áustria (BMI, eleição presidencial de 09/10/2022, resultado final com voto por correio, por estado) -> data/mundo/at.json

Uso: python pipeline/mundo_at.py endgueltiges_gesamtergebnis_inkl_briefwahl_bpw22_20221028.xlsx OUT_DIR
Fonte: Bundesministerium für Inneres, Bundespräsidentenwahl 2022.
"""
import json, os, sys, openpyxl

SRC, OUT = sys.argv[1], sys.argv[2]
OUTRO = "#5B6478"
COR = {"Dr. Alexander Van der Bellen": ("VDB", "Alexander Van der Bellen", "independente (ex-Verdes)", "#3FAE5A"),
       "Dr. Walter Rosenkranz": ("ROS", "Walter Rosenkranz", "FPÖ", "#3B78EA"), "Dr. Dominik Wlazny": ("WLA", "Dominik Wlazny", "Bierpartei", "#E2B84B"),
       "Gerald Grosz": ("GRO", "Gerald Grosz", "independente", "#F28C28"), "Dr. Tassilo Wallentin": ("WAL", "Tassilo Wallentin", "independente", "#38B2C9"),
       "Dr. Michael Brunner": ("BRU", "Michael Brunner", "MFG", OUTRO), "Heinrich Staudinger": ("STA", "Heinrich Staudinger", "independente", OUTRO)}
EST = {"Burgenland": "Burgenland", "Kärnten": "Caríntia", "Niederösterreich": "Baixa Áustria", "Oberösterreich": "Alta Áustria", "Salzburg": "Salzburgo",
       "Steiermark": "Estíria", "Tirol": "Tirol", "Vorarlberg": "Vorarlberg", "Wien": "Viena"}
ws = openpyxl.load_workbook(SRC, read_only=True, data_only=True).worksheets[0]
rows = list(ws.iter_rows(values_only=True))
h = rows[0]
cols = [(i, COR[h[i]]) for i in range(6, len(h), 2) if h[i] in COR]
assert len(cols) == 7, h


def linha(r, nome):
    v = {c[0]: int(r[i]) for i, c in cols}
    return {"id": r[0], "n": nome, "eleitores": int(r[2]), "votantes": int(r[3]), "brancos": None, "nulos": int(r[4]), "validos": int(r[5]), "v": v}


tot = next(r for r in rows if r[0] == "G00000")
reg = [linha(r, EST[r[1]]) for r in rows[2:] if r[0] and r[0][-4:] == "0000" and r[0] != "G00000"]
for r in reg:
    assert sum(r["v"].values()) == r["validos"], r["n"]
nac = {x: sum(r[x] for r in reg) for x in ("eleitores", "votantes", "nulos", "validos")}; nac["brancos"] = None
nac["v"] = {c[0]: sum(r["v"][c[0]] for r in reg) for _, c in cols}
t = linha(tot, "Áustria")
assert nac["v"] == t["v"] and nac["validos"] == t["validos"] and nac["eleitores"] == t["eleitores"], "estados não somam o total"
ordem = sorted([c for _, c in cols], key=lambda c: -nac["v"][c[0]])
print("eleitores", nac["eleitores"], "votantes", nac["votantes"], f'({nac["votantes"]/nac["eleitores"]*100:.2f}%)', "válidos", nac["validos"])
for c in ordem:
    print("   ", c[1], nac["v"][c[0]], f'{nac["v"][c[0]]/nac["validos"]*100:.2f}%')
P = {"pais": "AT", "nome": "Áustria", "nivel": "Estado", "sistema": "2 turnos",
     "fonte": "Bundesministerium für Inneres, resultado final da eleição presidencial de 09/10/2022 com voto por correio", "fonte_url": "https://www.bmi.gv.at/412/bundespraesidentenwahlen/bundespraesidentenwahl_2022/start.aspx",
     "nota": "Percentual sobre votos válidos. Alexander Van der Bellen foi reeleito no 1º turno, com maioria absoluta, sem precisar de 2º turno. Os votos por correio (Wahlkarten) estão somados em cada estado.",
     "eleicoes": [{"ano": 2022, "turnos": {"1": {"cand": [{"id": c[0], "nome": c[1], "grupo": c[2], "cor": c[3]} for c in ordem], "nac": nac, "reg": reg}}}]}
os.makedirs(OUT, exist_ok=True)
json.dump(P, open(os.path.join(OUT, "at.json"), "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
