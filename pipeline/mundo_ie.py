"""Irlanda (eleições presidenciais de 2011, 2018 e 2025, 1ª contagem por distrito do Dáil) -> data/mundo/ie.json

Uso: python pipeline/mundo_ie.py OUT_DIR
Fonte: Department of Housing, Local Government and Heritage (Franchise Section), conjuntos
"2025/2018/2011 Presidential election results" em data.gov.ie / opendata.housing.gov.ie (CC BY-SA 4.0),
copiados em pipeline/ie/ie{ano}.csv.
"""
import csv, json, os, sys

OUT = sys.argv[1]
D = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ie")
OUTRO = "#5B6478"
CAND = {
    2025: [("Catherine Martina Ann Connolly", "CC", "Catherine Connolly", "Independente (apoio de Sinn Féin, Labour, Social Democrats)", "#2E9E5B"),
           ("Heather Humphreys", "HH", "Heather Humphreys", "Fine Gael", "#3B78EA"),
           ("Jim Gavin", "JG", "Jim Gavin", "Fianna Fáil (retirou a candidatura, seguiu na cédula)", "#F28C28")],
    2018: [("Michael D. Higgins", "MH", "Michael D. Higgins", "Independente (presidente em exercício)", "#2E9E5B"),
           ("Peter Joseph Casey", "PC", "Peter Casey", "Independente", "#7C5CE0"),
           ("Séan Gallagher", "SG", "Seán Gallagher", "Independente", "#F2C12E"),
           ("Liadh Ní Riada", "LR", "Liadh Ní Riada", "Sinn Féin", "#1FA37A"),
           ("Joan Freeman", "JF", "Joan Freeman", "Independente", "#38B2C9"),
           ("Gavin Duffy", "GD", "Gavin Duffy", "Independente", "#C9CED6")],
    2011: [("Michael D. Higgins", "MH", "Michael D. Higgins", "Labour", "#E0353D"),
           ("Sean Gallagher", "SG", "Seán Gallagher", "Independente", "#F2C12E"),
           ("Martin McGuinness", "MM", "Martin McGuinness", "Sinn Féin", "#1FA37A"),
           ("Gay Mitchell", "GM", "Gay Mitchell", "Fine Gael", "#3B78EA"),
           ("David Norris", "DN", "David Norris", "Independente", "#7C5CE0"),
           ("Dana Rosemary Scallon", "DS", "Dana Rosemary Scallon", "Independente", "#38B2C9"),
           ("Mary Davis", "MD", "Mary Davis", "Independente", "#C9CED6")],
}
OFICIAL = {2025: (3614450, 1656436, 213738, {"CC": 914143, "HH": 424987, "JG": 103568}),
           2018: (3401681, 1492338, 18438, {"MH": 822566, "PC": 342727}),
           2011: (3191157, 1790438, 18676, {"MH": 701101, "SG": 504964})}
num = lambda s: int(s.replace(",", "").strip())
eleicoes = []
for ano in (2011, 2018, 2025):
    raw = open(os.path.join(D, f"ie{ano}.csv"), encoding="latin-1").read().replace("Se\xe1n", "Séan").replace("N\xed", "Ní")
    rows = list(csv.reader(raw.splitlines()))
    hi = next(i for i, r in enumerate(rows) if r and r[0].strip() == "Constituency")
    head = [h.strip() for h in rows[hi]]
    col = {nome: head.index(nome) for nome, *_ in CAND[ano]}
    inv = next(i for i, h in enumerate(head) if h.startswith("Invalid"))
    reg, tot = [], None
    for r in rows[hi + 1:]:
        if not r or not r[0].strip(): continue
        nome = r[0].strip()
        el, poll, nul = num(r[1]), num(r[2]), num(r[inv])
        v = {cid: num(r[col[n]]) for n, cid, *_ in CAND[ano]}
        g = {"id": "C%02d" % (len(reg) + 1), "n": nome, "eleitores": el, "votantes": poll, "brancos": 0, "nulos": nul, "validos": sum(v.values()), "v": v}
        assert g["validos"] + nul == poll, (ano, nome)
        if nome.lower() == "total": tot = g
        else: reg.append(g)
    nac = {k: sum(x[k] for x in reg) for k in ("eleitores", "votantes", "brancos", "nulos", "validos")}
    nac["v"] = {cid: sum(x["v"][cid] for x in reg) for _, cid, *_ in CAND[ano]}
    assert nac["v"] == tot["v"] and nac["eleitores"] == tot["eleitores"] and nac["votantes"] == tot["votantes"], ano
    el, poll, nul, chk = OFICIAL[ano]
    assert (nac["eleitores"], nac["votantes"], nac["nulos"]) == (el, poll, nul) and all(nac["v"][k] == chk[k] for k in chk), ano
    print(ano, len(reg), "distritos", {k: f'{nac["v"][k]/nac["validos"]*100:.2f}%' for k in nac["v"]}, f'nulos {nul/poll*100:.1f}%')
    cands = [{"id": cid, "nome": nm, "grupo": gr, "cor": cor} for _, cid, nm, gr, cor in CAND[ano]]
    eleicoes.append({"ano": ano, "turnos": {"1": {"cand": cands, "nac": nac, "reg": reg}}})
P = {"pais": "IE", "nome": "Irlanda", "nivel": "Distrito eleitoral", "sistema": "Voto preferencial",
     "fonte": "Department of Housing, Local Government and Heritage, resultados das eleições presidenciais (data.gov.ie)",
     "fonte_url": "https://data.gov.ie/dataset/2025-presidential-election",
     "nota": "Eleição presidencial em turno único com voto preferencial (o eleitor ordena os candidatos; os votos dos eliminados são transferidos até alguém passar da metade). Aqui aparece a 1ª contagem. Em 2025 e 2018 a vencedora e o vencedor passaram da metade já na 1ª contagem; em 2011 Michael D. Higgins só venceu na 4ª contagem. Em 2025 os votos nulos chegaram a 12,9%, o maior índice já registrado, em parte como protesto contra as opções na cédula.",
     "eleicoes": eleicoes}
json.dump(P, open(os.path.join(OUT, "ie.json"), "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
