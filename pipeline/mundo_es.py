"""Espanha (Ministerio del Interior / Infoelectoral, Congreso 23/07/2023, por comunidade autônoma) -> data/mundo/es.json

Uso: python pipeline/mundo_es.py es_provincias_2023.txt OUT_DIR
es_provincias_2023.txt foi extraído da planilha oficial PROV_02_202307_1.xlsx (Área de descargas do Infoelectoral):
comunidade; província; censo; votantes; válidos; votos em candidaturas; brancos; nulos; votos de 11 partidos; outros; cadeiras dos 11; outros.
"""
import json, os, sys
from collections import defaultdict

SRC, OUT = sys.argv[1], sys.argv[2]
OUTRO = "#5B6478"
PART = [("PP", "Partido Popular", "Alberto Núñez Feijóo", "#3B78EA"), ("PSOE", "PSOE", "Pedro Sánchez", "#E0353D"), ("VOX", "Vox", "Santiago Abascal", "#3FAE5A"),
        ("SUMAR", "Sumar", "Yolanda Díaz", "#B5179E"), ("ERC", "ERC", "", "#E2B84B"), ("JUNTS", "Junts", "", "#38B2C9"), ("BILDU", "EH Bildu", "", "#7CB342"),
        ("PNV", "PNV", "", "#2E7D32"), ("BNG", "BNG", "", "#81D4FA"), ("CC", "Coalición Canaria", "", "#FFD54F"), ("UPN", "UPN", "", "#90A4AE")]
COM = {"Andalucía": "Andaluzia", "Aragón": "Aragão", "Principado de Asturias": "Astúrias", "Illes Balears": "Ilhas Baleares", "Canarias": "Canárias",
       "Cantabria": "Cantábria", "Castilla - La Mancha": "Castela-La Mancha", "Castilla y León": "Castela e Leão", "Cataluña": "Catalunha",
       "Extremadura": "Estremadura", "Galicia": "Galiza", "Comunidad de Madrid": "Madri", "Comunidad Foral de Navarra": "Navarra", "País Vasco": "País Basco",
       "Región de Murcia": "Múrcia", "La Rioja": "La Rioja", "Comunitat Valenciana": "Comunidade Valenciana", "Ciudad de Ceuta": "Ceuta", "Ciudad de Melilla": "Melilla"}
L = [l.split(";") for l in open(SRC, encoding="utf-8").read().strip().split("\n")]
esp = L[-1]; prov = L[:-1]
reg = defaultdict(lambda: {"eleitores": 0, "votantes": 0, "brancos": 0, "nulos": 0, "validos": 0, "v": defaultdict(int)})
for x in prov:
    g = reg[x[0]]; n = list(map(int, x[2:]))
    g["eleitores"] += n[0]; g["votantes"] += n[1]; g["validos"] += n[3]; g["brancos"] += n[4]; g["nulos"] += n[5]
    for i, (k, *_) in enumerate(PART):
        g["v"][k] += n[6 + i]
    g["v"]["O"] += n[17]
out = [{"id": c, "n": COM[c], **{x: reg[c][x] for x in ("eleitores", "votantes", "brancos", "nulos", "validos")}, "v": dict(reg[c]["v"])} for c in COM]
nac = {x: sum(r[x] for r in out) for x in ("eleitores", "votantes", "brancos", "nulos", "validos")}
nac["v"] = {k: sum(r["v"][k] for r in out) for k in [p[0] for p in PART] + ["O"]}
e = list(map(int, esp[2:]))
assert nac["eleitores"] == e[0] and nac["votantes"] == e[1] and nac["validos"] == e[3] and nac["v"]["PP"] == e[6], "não bate com a linha España"
seats = dict(zip([p[0] for p in PART] + ["O"], e[18:30]))
print("censo", nac["eleitores"], "votantes", nac["votantes"], f'({nac["votantes"]/nac["eleitores"]*100:.2f}%)', "válidos (com brancos)", e[2])
for k, nome, *_ in PART[:6]:
    print("   ", nome, nac["v"][k], f'{nac["v"][k]/e[2]*100:.2f}% oficial', f'{nac["v"][k]/nac["validos"]*100:.2f}% sem brancos', seats[k], "cadeiras")
cands = [{"id": k, "nome": nome, "grupo": f"{seats[k]} cadeiras" + (" · " + lider if lider else ""), "cor": cor} for k, nome, lider, cor in PART]
cands.append({"id": "O", "nome": "Outros", "grupo": f"{seats['O']} cadeiras", "cor": OUTRO})
P = {"pais": "ES", "nome": "Espanha", "nivel": "Comunidade autônoma", "sistema": "Parlamentar", "parlamentar": True,
     "fonte": "Ministerio del Interior (Infoelectoral), resultados do Congreso de 23/07/2023 por província", "fonte_url": "https://infoelectoral.interior.gob.es/es/elecciones-celebradas/area-de-descargas/",
     "nota": "Eleição parlamentar (350 cadeiras distribuídas por província). Aqui o percentual é sobre votos dados a partidos, sem brancos; o Ministério conta o voto em branco como válido, por isso divulga números um pouco menores (PP 33,1%, PSOE 31,7%). O primeiro-ministro precisa do voto de maioria do Congresso: em 2023 o PP foi o mais votado, mas Pedro Sánchez (PSOE) foi reconduzido.",
     "eleicoes": [{"ano": 2023, "turnos": {"1": {"cand": cands, "nac": nac, "reg": out}}}]}
os.makedirs(OUT, exist_ok=True)
json.dump(P, open(os.path.join(OUT, "es.json"), "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
