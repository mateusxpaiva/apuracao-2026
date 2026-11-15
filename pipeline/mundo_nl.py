"""Holanda (Kiesraad, eleição da Tweede Kamer de 29/10/2025, por província) -> data/mundo/nl.json

Uso: python pipeline/mundo_nl.py TK2025_uitslag.csv OUT_DIR
Fonte: conjunto "Verkiezingsuitslag Tweede Kamer 2025 (CSV Formaat)" da Kiesraad em data.overheid.nl,
o mesmo carregado em verkiezingsuitslagen.nl. Linhas de província (P..) e "Niet-provinciaal" (exterior e Caribe).
"""
import csv, json, os, sys
from collections import defaultdict

SRC, OUT = sys.argv[1], sys.argv[2]
OUTRO = "#5B6478"
PART = [("D66", "D66", "Rob Jetten", "#2E9E5B"), ("PVV (Partij voor de Vrijheid)", "PVV", "Geert Wilders", "#3B78EA"),
        ("VVD", "VVD", "Dilan Yeşilgöz", "#F28C28"), ("GROENLINKS / Partij van de Arbeid (PvdA)", "GroenLinks-PvdA", "Frans Timmermans", "#E0353D"),
        ("CDA", "CDA", "Henri Bontenbal", "#38B2C9"), ("JA21", "JA21", "", "#7C5CE0"), ("Forum voor Democratie", "Fórum pela Democracia", "", "#8B1E2E")]
KEY = {p[0]: p[1] for p in PART}
rows = list(csv.DictReader(open(SRC, encoding="utf-8-sig"), delimiter=";"))
reg = defaultdict(lambda: {"eleitores": 0, "votantes": 0, "brancos": 0, "nulos": 0, "validos": 0, "v": defaultdict(int)})
nomes = {}
nat = defaultdict(int); seats = defaultdict(int)
for r in rows:
    c, f, val = r["RegioCode"], r["VeldType"], r["Waarde"]
    if c.startswith("L"):
        if f == "LijstAantalStemmen": nat[KEY.get(r["LijstNaam"], "O")] += int(val)
        if f == "LijstAantalZetels": seats[KEY.get(r["LijstNaam"], "O")] += int(val)
        if f in ("Kiesgerechtigden", "Opkomst", "AantalBlancoStemmen", "AantalOngeldigeStemmen"): nat[f] = int(val)
        continue
    if not c.startswith("P"):
        continue
    nomes[c] = "Exterior e Caribe" if c == "P99" else r["Regio"]
    g = reg[c]
    if f == "LijstAantalStemmen": g["v"][KEY.get(r["LijstNaam"], "O")] += int(val)
    elif f == "Kiesgerechtigden": g["eleitores"] += int(val)
    elif f == "Opkomst": g["votantes"] += int(val)
    elif f == "AantalBlancoStemmen": g["brancos"] += int(val)
    elif f == "AantalOngeldigeStemmen": g["nulos"] += int(val)
out = []
for c in sorted(reg):
    g = reg[c]; g["validos"] = sum(g["v"].values())
    out.append({"id": c, "n": nomes[c], **{x: g[x] for x in ("eleitores", "votantes", "brancos", "nulos", "validos")}, "v": dict(g["v"])})
ids = [p[1] for p in PART] + ["O"]
nac = {x: sum(r[x] for r in out) for x in ("eleitores", "votantes", "brancos", "nulos", "validos")}
nac["v"] = {k: sum(r["v"].get(k, 0) for r in out) for k in ids}
assert all(nac["v"][k] == nat[k] for k in ids) and nac["eleitores"] == nat["Kiesgerechtigden"] and nac["votantes"] == nat["Opkomst"], "não bate com o total nacional"
print("eleitores", nac["eleitores"], "votantes", nac["votantes"], f'({nac["votantes"]/nac["eleitores"]*100:.2f}%)', "votos em listas", nac["validos"], "brancos", nac["brancos"])
for k in ids:
    print("   ", k, nac["v"][k], f'{nac["v"][k]/nac["validos"]*100:.2f}%', seats[k])
cands = [{"id": k, "nome": k, "grupo": f"{seats[k]} cadeiras" + (" · " + lid if lid else ""), "cor": cor} for _, k, lid, cor in PART]
cands.append({"id": "O", "nome": "Outros", "grupo": f"{seats['O']} cadeiras", "cor": OUTRO})
P = {"pais": "NL", "nome": "Holanda", "nivel": "Província", "sistema": "Parlamentar", "parlamentar": True,
     "fonte": "Kiesraad, resultado da eleição da Tweede Kamer de 29/10/2025 (data.overheid.nl)", "fonte_url": "https://data.overheid.nl/dataset/verkiezingsuitslag-tweede-kamer-2025",
     "nota": "Eleição parlamentar com proporcionalidade nacional pura (150 cadeiras, o país todo é um distrito). D66 e PVV empataram em 26 cadeiras; o D66 teve mais votos. Percentual sobre votos dados a listas. Exterior e Caribe = votos fora das 12 províncias.",
     "eleicoes": [{"ano": 2025, "turnos": {"1": {"cand": cands, "nac": nac, "reg": out}}}]}
os.makedirs(OUT, exist_ok=True)
json.dump(P, open(os.path.join(OUT, "nl.json"), "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
