"""México (INE, Cómputos Distritales 2024, ata por ata) -> data/mundo/mx.json

Uso: python pipeline/mundo_mx.py PRES_2024.csv OUT_DIR
Fonte: https://computos2024.ine.mx/ (base de dados 20240608_2030_COMPUTOS.zip).
Cada candidata soma os votos do próprio partido e de todas as combinações da coalizão.
"""
import csv, io, json, os, sys
from collections import defaultdict

SRC, OUT = sys.argv[1], sys.argv[2]
CAND = [
    {"id": "CSP", "nome": "Claudia Sheinbaum", "grupo": "Morena · PT · PVEM", "cor": "#A6192E",
     "cols": ["PVEM", "PT", "MORENA", "PVEM_PT_MORENA", "PVEM_PT", "PVEM_MORENA", "PT_MORENA"]},
    {"id": "XG", "nome": "Xóchitl Gálvez", "grupo": "PAN · PRI · PRD", "cor": "#3B78EA",
     "cols": ["PAN", "PRI", "PRD", "PAN_PRI_PRD", "PAN_PRI", "PAN_PRD", "PRI_PRD"]},
    {"id": "JAM", "nome": "Jorge Álvarez Máynez", "grupo": "Movimiento Ciudadano", "cor": "#F28C28", "cols": ["MC"]},
]
NOMES = {"MEXICO": "Estado de México", "CIUDAD DE MEXICO": "Cidade do México", "MICHOACAN": "Michoacán", "NUEVO LEON": "Nuevo León",
         "QUERETARO": "Querétaro", "SAN LUIS POTOSI": "San Luis Potosí", "YUCATAN": "Yucatán", "COAHUILA": "Coahuila"}


def n(x):
    x = (x or "").strip().replace(",", "")
    return int(x) if x.isdigit() else 0


def nome_ent(s):
    import unicodedata
    k = "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn").upper().strip()
    return NOMES.get(k, s.title().replace(" De ", " de ").replace(" Del ", " del "))


raw = open(SRC, encoding="latin-1").read().splitlines()
cab = [i for i, l in enumerate(raw) if l.startswith("ACTAS_ESPERADAS")][0]
resumo = dict(zip(raw[cab].split("|"), raw[cab + 1].split("|")))
ini = [i for i, l in enumerate(raw) if l.startswith("CLAVE_CASILLA")][0]
reg = {}
for r in csv.DictReader(io.StringIO("\n".join(raw[ini:])), delimiter="|"):
    eid = r["ID_ENTIDAD"].strip('="')
    g = reg.setdefault(eid, {"id": eid, "n": nome_ent(r["ENTIDAD"]), "eleitores": 0, "votantes": 0, "brancos": None, "nulos": 0, "validos": 0, "v": defaultdict(int)})
    for c in CAND:
        v = sum(n(r[k]) for k in c["cols"])
        g["v"][c["id"]] += v
        g["validos"] += v
    g["nulos"] += n(r["VOTOS NULOS"]) + n(r["CANDIDATO/A NO REGISTRADO/A"])
    g["votantes"] += n(r["TOTAL_VOTOS_CALCULADOS"])
    g["eleitores"] += n(r["LISTA_NOMINAL"])
lista = sorted(reg.values(), key=lambda g: int(g["id"]))
for g in lista:
    g["v"] = dict(g["v"])
nac = {"eleitores": sum(g["eleitores"] for g in lista), "votantes": sum(g["votantes"] for g in lista), "brancos": None,
       "nulos": sum(g["nulos"] for g in lista), "validos": sum(g["validos"] for g in lista),
       "v": {c["id"]: sum(g["v"][c["id"]] for g in lista) for c in CAND}}
print("INE resumo:", resumo["TOTAL_VOTOS"], resumo["LISTA_NOMINAL_ACTAS_COMPUTADAS"], "| soma atas:", nac["votantes"], nac["eleitores"], len(lista), "entidades")
for c in CAND:
    print("  ", c["nome"], nac["v"][c["id"]], f'{nac["v"][c["id"]] / nac["votantes"] * 100:.2f}% do total', f'{nac["v"][c["id"]] / nac["validos"] * 100:.2f}% dos válidos')
assert nac["votantes"] == int(resumo["TOTAL_VOTOS"].replace(",", "")), "total não bate com o INE"
P = {"pais": "MX", "nome": "México", "nivel": "Estado", "sistema": "Turno único",
     "fonte": "Instituto Nacional Electoral (INE), Cómputos Distritales 2024, ata por ata",
     "fonte_url": "https://computos2024.ine.mx/",
     "nota": "Turno único: vence quem tiver mais votos. Percentual sobre votos dados a candidatas e candidatos (o INE divulga sobre o total, com nulos e não registrados, por isso os números oficiais são um pouco menores). Cada candidatura soma os votos do partido e das combinações da coalizão. Votos do exterior entram no estado de origem do eleitor.",
     "eleicoes": [{"ano": 2024, "turnos": {"1": {"cand": [{k: c[k] for k in ("id", "nome", "grupo", "cor")} for c in CAND], "nac": nac, "reg": lista}}}]}
os.makedirs(OUT, exist_ok=True)
json.dump(P, open(os.path.join(OUT, "mx.json"), "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
