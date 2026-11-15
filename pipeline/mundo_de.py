"""Alemanha (Bundeswahlleiterin, eleição do Bundestag 2025, 2º voto por estado) -> data/mundo/de.json

Uso: python pipeline/mundo_de.py kerg2.csv OUT_DIR
Fonte: https://www.bundeswahlleiterin.de/bundestagswahlen/2025/ergebnisse/opendata/btw25/csv/kerg2.csv
O 2º voto (Zweitstimme, em lista partidária) define a proporção de cadeiras. CDU e CSU somadas como "União".
"""
import csv, io, json, os, sys

SRC, OUT = sys.argv[1], sys.argv[2]
OUTRO = "#5B6478"
PART = [("UNION", "União (CDU/CSU)", "Merz", "#E6E8EE", ("CDU", "CSU")), ("AfD", "AfD", "Weidel", "#3B78EA", ("AfD",)),
        ("SPD", "SPD", "Scholz", "#E0353D", ("SPD",)), ("GRUENE", "Verdes", "Habeck", "#3FAE5A", ("GRÜNE",)),
        ("LINKE", "Die Linke", "", "#B5179E", ("Die Linke",)), ("BSW", "BSW", "", "#7C5CE0", ("BSW",)), ("FDP", "FDP", "", "#E2B84B", ("FDP",))]
MAPA = {p: k for k, _, _, _, ps in PART for p in ps}
rows = list(csv.reader(io.StringIO(open(SRC, encoding="utf-8-sig").read()), delimiter=";"))
h = [i for i, r in enumerate(rows) if r and r[0] == "Wahlart"][0]
dados = [dict(zip(rows[h], r)) for r in rows[h + 1:] if len(r) > 10]


def n(x):
    return int(x) if x.strip().isdigit() else 0


def area(tipo, num):
    a = [r for r in dados if r["Gebietsart"] == tipo and r["Gebietsnummer"] == num]
    g = {r["Gruppenname"]: r for r in a}
    v = {k: 0 for k, *_ in PART}; v["O"] = 0
    for r in a:
        if r["Gruppenart"] == "Partei" and r["Stimme"] == "2":
            v[MAPA.get(r["Gruppenname"], "O")] += n(r["Anzahl"])
    val = next(n(r["Anzahl"]) for r in a if r["Gruppenname"] == "Gültige" and r["Stimme"] == "2")
    nul = next(n(r["Anzahl"]) for r in a if r["Gruppenname"] == "Ungültige" and r["Stimme"] == "2")
    return {"id": num, "n": a[0]["Gebietsname"], "eleitores": n(g["Wahlberechtigte"]["Anzahl"]), "votantes": n(g["Wählende"]["Anzahl"]),
            "brancos": None, "nulos": nul, "validos": val, "v": v}


NOME_PT = {"Bayern": "Baviera", "Baden-Württemberg": "Baden-Württemberg", "Nordrhein-Westfalen": "Renânia do Norte-Vestfália", "Niedersachsen": "Baixa Saxônia",
           "Hessen": "Hesse", "Sachsen": "Saxônia", "Rheinland-Pfalz": "Renânia-Palatinado", "Berlin": "Berlim", "Schleswig-Holstein": "Schleswig-Holstein",
           "Brandenburg": "Brandemburgo", "Sachsen-Anhalt": "Saxônia-Anhalt", "Thüringen": "Turíngia", "Hamburg": "Hamburgo", "Mecklenburg-Vorpommern": "Meclemburgo-Pomerânia",
           "Saarland": "Sarre", "Bremen": "Bremen"}
reg = []
for num in sorted({r["Gebietsnummer"] for r in dados if r["Gebietsart"] == "Land"}, key=int):
    x = area("Land", num); x["n"] = NOME_PT.get(x["n"], x["n"]); reg.append(x)
bund = area("Bund", "99")
nac = {k: sum(r[k] for r in reg) for k in ("eleitores", "votantes", "nulos", "validos")}; nac["brancos"] = None
nac["v"] = {k: sum(r["v"][k] for r in reg) for k in bund["v"]}
print("Bund:", bund["eleitores"], bund["votantes"], bund["validos"], "| soma estados:", nac["eleitores"], nac["votantes"], nac["validos"])
assert nac["v"] == bund["v"] and nac["validos"] == bund["validos"], "soma dos estados não bate com o total federal"
for k, nome, *_ in PART:
    print("  ", nome, nac["v"][k], f'{nac["v"][k] / nac["validos"] * 100:.2f}%')
cands = [{"id": k, "nome": nome, "grupo": ("candidato: " + cab) if cab else "", "cor": cor} for k, nome, cab, cor, _ in PART] + [{"id": "O", "nome": "Outros partidos", "grupo": "", "cor": OUTRO}]
P = {"pais": "DE", "nome": "Alemanha", "nivel": "Estado", "sistema": "Parlamentar", "parlamentar": True,
     "fonte": "Die Bundeswahlleiterin, resultado final da eleição do Bundestag de 23/02/2025", "fonte_url": "https://www.bundeswahlleiterin.de/bundestagswahlen/2025/ergebnisse.html",
     "nota": "Eleição parlamentar: o percentual é do 2º voto (lista partidária), que define as cadeiras; partidos abaixo de 5% ficam fora, salvo exceções. CDU e CSU (que só concorre na Baviera) aparecem somadas como União. O chanceler é escolhido depois pelo Bundestag.",
     "eleicoes": [{"ano": 2025, "turnos": {"1": {"cand": cands, "nac": nac, "reg": reg}}}]}
os.makedirs(OUT, exist_ok=True)
json.dump(P, open(os.path.join(OUT, "de.json"), "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
