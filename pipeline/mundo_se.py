"""Suécia (SCB / Valmyndigheten, eleição do Riksdag de 11/09/2022, por condado) -> data/mundo/se.json

Uso: python pipeline/mundo_se.py t3_2022_mun.csv t3_2022.csv OUT_DIR
Fonte: Statistikdatabasen do SCB, tabela ME0104T3 (votos por partido e município), API PxWeb.
Os 290 municípios são somados por condado (län) pelos dois primeiros dígitos do código.
"""
import csv, io, json, os, sys
from collections import defaultdict

MUN, NAC, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
OUTRO = "#5B6478"
LAN = {"01": "Estocolmo", "03": "Uppsala", "04": "Södermanland", "05": "Östergötland", "06": "Jönköping", "07": "Kronoberg", "08": "Kalmar",
       "09": "Gotland", "10": "Blekinge", "12": "Escânia", "13": "Halland", "14": "Västra Götaland", "17": "Värmland", "18": "Örebro",
       "19": "Västmanland", "20": "Dalarna", "21": "Gävleborg", "22": "Västernorrland", "23": "Jämtland", "24": "Västerbotten", "25": "Norrbotten"}
PART = [("Socialdemokraterna", "SAP", "Social-Democratas", "Magdalena Andersson", "#E0353D"), ("Sverigedemokraterna", "SD", "Democratas Suecos", "Jimmie Åkesson", "#E2B84B"),
        ("Moderaterna", "M", "Moderados", "Ulf Kristersson", "#3B78EA"), ("Vänsterpartiet", "V", "Esquerda", "", "#8B1E2E"),
        ("Centerpartiet", "C", "Centro", "", "#3FAE5A"), ("Kristdemokraterna", "KD", "Democrata-Cristãos", "", "#38B2C9"),
        ("Miljöpartiet", "MP", "Verdes", "", "#7CB342"), ("Liberalerna", "L", "Liberais", "", "#F28C28")]
KEY = {p[0]: p[1] for p in PART}
ler = lambda f: list(csv.DictReader(io.StringIO(open(f, encoding="cp1252").read())))
reg = defaultdict(lambda: {"eleitores": 0, "votantes": 0, "brancos": None, "nulos": 0, "validos": 0, "v": defaultdict(int)})
for r in ler(MUN):
    cod = r["region"].split()[0]; x = int(r["Antal röster 2022"]) if r["Antal röster 2022"].strip().isdigit() else 0; p = r["parti mm"]
    g = reg[cod[:2]]
    if p == "ogiltiga valsedlar": g["nulos"] += x; g["eleitores"] += x; g["votantes"] += x
    elif p == "ej röstande": g["eleitores"] += x
    else:
        g["v"][KEY.get(p, "O")] += x; g["validos"] += x; g["eleitores"] += x; g["votantes"] += x
out = [{"id": k, "n": LAN[k], **{x: reg[k][x] for x in ("eleitores", "votantes", "brancos", "nulos", "validos")}, "v": dict(reg[k]["v"])} for k in LAN]
nac = {x: sum(r[x] for r in out) for x in ("eleitores", "votantes", "nulos", "validos")}; nac["brancos"] = None
ids = [p[1] for p in PART] + ["O"]
nac["v"] = {k: sum(r["v"].get(k, 0) for r in out) for k in ids}
naci = {r["parti mm"]: int(r["Antal röster 2022"]) for r in ler(NAC)}
dif = {p[1]: naci[p[0]] - nac["v"][p[1]] for p in PART}
print("nacional (SCB) - soma municípios:", dif, "| nulos", naci["ogiltiga valsedlar"] - nac["nulos"])
assert all(d == 0 for d in dif.values()), "municípios não somam o nacional"
print("eleitores", nac["eleitores"], "votantes", nac["votantes"], f'({nac["votantes"]/nac["eleitores"]*100:.2f}%)', "válidos", nac["validos"])
for _, k, nome, *_ in PART:
    print("   ", nome, nac["v"][k], f'{nac["v"][k]/nac["validos"]*100:.2f}%')
cands = [{"id": k, "nome": nome, "grupo": lid, "cor": cor} for _, k, nome, lid, cor in PART] + [{"id": "O", "nome": "Outros", "grupo": "", "cor": OUTRO}]
P = {"pais": "SE", "nome": "Suécia", "nivel": "Condado", "sistema": "Parlamentar", "parlamentar": True,
     "fonte": "SCB (Statistics Sweden), tabela ME0104T3 com os votos oficiais da eleição do Riksdag de 11/09/2022", "fonte_url": "https://www.statistikdatabasen.scb.se/pxweb/sv/ssd/START__ME__ME0104__ME0104C/ME0104T3/",
     "nota": "Eleição parlamentar proporcional (349 cadeiras). Percentual sobre votos válidos; nulos incluem votos em branco, como na estatística sueca. Os social-democratas foram os mais votados, mas o bloco de direita (M, SD, KD e L) fez maioria e Ulf Kristersson virou primeiro-ministro.",
     "eleicoes": [{"ano": 2022, "turnos": {"1": {"cand": cands, "nac": nac, "reg": out}}}]}
os.makedirs(OUT, exist_ok=True)
json.dump(P, open(os.path.join(OUT, "se.json"), "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
