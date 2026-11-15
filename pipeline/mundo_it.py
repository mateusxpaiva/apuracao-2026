"""Itália (Camera dei Deputati, eleição de 25/09/2022, voto proporcional por região) -> data/mundo/it.json

Uso: python pipeline/mundo_it.py ItaliaVotiListeCIRC.csv OUT_DIR
Fonte: documenti.camera.it/leg19/risultatiElettorali2022/UGE/VotiListe/ItaliaVotiListeCIRC.csv (resultados oficiais
da circunscrição, publicados pela Câmara). Usa a "cifra elettorale" de cada lista; as colunas de coalizão são ignoradas.
Vale d'Aosta (só distrito uninominal) e voto no exterior (listas próprias) ficam de fora, como no total proporcional oficial.
"""
import csv, json, os, re, sys
from collections import defaultdict

SRC, OUT = sys.argv[1], sys.argv[2]
OUTRO = "#5B6478"
PART = [("FDI", "Irmãos da Itália (FdI)", "Giorgia Meloni", "#3B78EA"), ("PD-IDP", "Partido Democrático", "Enrico Letta", "#E0353D"),
        ("M5S", "Movimento 5 Estrelas", "Giuseppe Conte", "#E2B84B"), ("LEGA", "Liga", "Matteo Salvini", "#3FAE5A"),
        ("FI", "Forza Italia", "Silvio Berlusconi", "#38B2C9"), ("AZ-IV", "Ação-Itália Viva", "Carlo Calenda", "#7C5CE0"),
        ("ALL-VER-SIN", "Verdes e Esquerda", "", "#B5179E")]
IDS = [p[0] for p in PART]
REG = {"PIEMONTE": "Piemonte", "LOMBARDIA": "Lombardia", "TRENTINO-ALTO ADIGE/SÜDTIROL": "Trentino-Alto Ádige", "VENETO": "Vêneto",
       "FRIULI-VENEZIA GIULIA": "Friuli-Veneza Júlia", "LIGURIA": "Ligúria", "EMILIA-ROMAGNA": "Emília-Romanha", "TOSCANA": "Toscana",
       "UMBRIA": "Úmbria", "MARCHE": "Marcas", "LAZIO": "Lácio", "ABRUZZO": "Abruzos", "MOLISE": "Molise", "CAMPANIA": "Campânia",
       "PUGLIA": "Apúlia", "BASILICATA": "Basilicata", "CALABRIA": "Calábria", "SICILIA": "Sicília", "SARDEGNA": "Sardenha"}
norm = lambda s: re.sub(r"\s+", " ", s).strip()
rows = list(csv.reader(open(SRC, encoding="utf-8-sig"), delimiter=";"))
h = [norm(c) for c in rows[0]]
ix = {c: i for i, c in enumerate(h)}
listas = [c[:-len(" (CIFRA ELETTORALE CIRCOSCRIZIONALE)")] for c in h if c.endswith("(CIFRA ELETTORALE CIRCOSCRIZIONALE)") and not c.startswith("COALIZIONE")]
n = lambda x: int(x) if x.strip().lstrip("-").isdigit() else 0
reg = defaultdict(lambda: {"eleitores": 0, "votantes": 0, "brancos": 0, "nulos": 0, "validos": 0, "v": defaultdict(int)})
tot = None
for r in rows[1:]:
    if not r or not r[0].strip():
        continue
    if r[0].strip() == "TOTALE":
        tot = r; continue
    if not r[0].strip().isdigit():
        continue
    nome = re.sub(r"\s+\d+$", "", r[ix["CIRCOSCRIZIONE"]].strip())
    g = reg[nome]
    g["eleitores"] += n(r[ix["ELETTORI TOTALI"]]); g["votantes"] += n(r[ix["VOTANTI"]])
    g["brancos"] += n(r[ix["SCHEDE BIANCHE"]]); g["nulos"] += n(r[ix["SCHEDE E VOTI NULLI"]])
    for l in listas:
        g["v"][l if l in IDS else "O"] += n(r[ix[l + " (CIFRA ELETTORALE CIRCOSCRIZIONALE)"]])
out = []
for k in REG:
    if k not in reg:
        continue
    g = reg[k]; g["validos"] = sum(g["v"].values())
    out.append({"id": k, "n": REG[k], **{x: g[x] for x in ("eleitores", "votantes", "brancos", "nulos", "validos")}, "v": dict(g["v"])})
assert len(out) == len(reg), set(reg) - set(REG)
nac = {x: sum(r[x] for r in out) for x in ("eleitores", "votantes", "brancos", "nulos", "validos")}
nac["v"] = {k: sum(r["v"].get(k, 0) for r in out) for k in IDS + ["O"]}
tv = {l: n(tot[ix[l + " (CIFRA ELETTORALE CIRCOSCRIZIONALE)"]]) for l in listas}
assert all(nac["v"][k] == tv[k] for k in IDS), "não bate com a linha TOTALE"
assert nac["votantes"] == n(tot[ix["VOTANTI"]])
print("eleitores", nac["eleitores"], "votantes", nac["votantes"], f'({nac["votantes"]/nac["eleitores"]*100:.2f}%)', "válidos", nac["validos"], "(oficial", n(tot[ix["VOTI VALIDI"]]), ")")
for k in IDS + ["O"]:
    print("   ", k, nac["v"][k], f'{nac["v"][k]/nac["validos"]*100:.2f}%')
cands = [{"id": k, "nome": nome, "grupo": lid, "cor": cor} for k, nome, lid, cor in PART] + [{"id": "O", "nome": "Outros", "grupo": "", "cor": OUTRO}]
P = {"pais": "IT", "nome": "Itália", "nivel": "Região", "sistema": "Parlamentar", "parlamentar": True,
     "fonte": "Camera dei Deputati, resultados oficiais do voto proporcional por circunscrição (25/09/2022)", "fonte_url": "https://www.camera.it/deputati/elezioni/risultati-19-relazioni-csv-excel",
     "nota": "Eleição parlamentar mista: 37% das cadeiras em distritos uninominais e o resto proporcional. Aqui, o voto proporcional por lista pela cifra eleitoral oficial, que reparte entre as listas os votos dados só à coalizão (por isso o FdI aparece com 26,1%, e não os 26,0% das manchetes), somando as circunscrições de cada região. Ficam de fora o Vale de Aosta (só uninominal) e o voto no exterior, como no total proporcional oficial. A coalizão de direita (FdI, Liga, FI e Noi Moderati) venceu e Giorgia Meloni virou primeira-ministra.",
     "eleicoes": [{"ano": 2022, "turnos": {"1": {"cand": cands, "nac": nac, "reg": out}}}]}
os.makedirs(OUT, exist_ok=True)
json.dump(P, open(os.path.join(OUT, "it.json"), "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
