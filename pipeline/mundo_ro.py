"""Romênia (Autoritatea Electorală Permanentă, presidenciais de 4 e 18/05/2025, por distrito) -> data/mundo/ro.json

Uso: python pipeline/mundo_ro.py ro.txt OUT_DIR
ro.txt é a soma por distrito (județ) das atas de cada seção publicadas em prezenta.roaep.ro
(data/csv/sicpv/pv_part_cnty_prsd_*.csv; Bucareste somando os 6 setores; exterior com voto por correio).
Colunas: distrito; a (inscritos na lista permanente); b (votantes); c (válidos); d (nulos); votos por candidato.
"""
import json, os, sys

SRC, OUT = sys.argv[1], sys.argv[2]
OUTRO = "#5B6478"
C1 = [("SIM", "George Simion", "AUR", "#3B78EA"), ("DAN", "Nicușor Dan", "independente", "#E2B84B"), ("ANT", "Crin Antonescu", "PSD · PNL · UDMR", "#E0353D"),
      ("PON", "Victor Ponta", "independente", "#F28C28"), ("LAS", "Elena Lasconi", "USR", "#38B2C9"), ("SAN", "Lavinia Șandru", "PUSL", OUTRO),
      ("FUN", "Daniel Funeriu", "independente", OUTRO), ("TER", "Cristian Terheș", "PNCR", OUTRO), ("POP", "Sebastian Popescu", "PNR", OUTRO),
      ("BAN", "John Banu", "PNS", OUTRO), ("PRE", "Silviu Predoiu", "PLAN", OUTRO)]
FIX = str.maketrans({"Ş": "Ș", "ş": "ș", "Ţ": "Ț", "ţ": "ț"})


def turno(linhas, ids):
    reg = []
    for l in linhas:
        p = l.split(";")
        v = dict(zip(ids, map(int, p[5:])))
        val = sum(v.values())
        reg.append({"id": p[0], "n": p[0], "eleitores": int(p[1]) or None, "votantes": int(p[2]), "brancos": None, "nulos": int(p[4]), "validos": val, "v": v})
    return reg


t = open(SRC, encoding="utf-8").read().split("T2\n")
r1 = turno(t[0].split("T1\n")[1].strip().split("\n"), [c[0] for c in C1])
r2 = turno(t[1].strip().split("\n"), ["SIM", "DAN"])
NOMES = {}
for r in r1 + r2:
    k = r["id"]
    if k not in NOMES:
        s = k.translate(FIX)
        NOMES[k] = {"Străinătate": "Exterior", "București": "Bucareste"}.get(k, " ".join(w.capitalize() for w in s.lower().split()).replace("-năsăud", "-Năsăud").replace("-severin", "-Severin"))
    r["n"] = NOMES[k]
eleicoes = {}
for k, reg, cands in (("1", r1, C1), ("2", r2, [c for c in C1 if c[0] in ("SIM", "DAN")])):
    nac = {"eleitores": sum(r["eleitores"] or 0 for r in reg), "votantes": sum(r["votantes"] for r in reg), "brancos": None,
           "nulos": sum(r["nulos"] for r in reg), "validos": sum(r["validos"] for r in reg)}
    nac["v"] = {c[0]: sum(r["v"][c[0]] for r in reg) for c in cands}
    ordem = sorted(cands, key=lambda c: -nac["v"][c[0]])
    print(k, "inscritos", nac["eleitores"], "votantes", nac["votantes"], f'({nac["votantes"]/nac["eleitores"]*100:.2f}%)', "válidos", nac["validos"])
    for c in ordem[:5]:
        print("   ", c[1], nac["v"][c[0]], f'{nac["v"][c[0]]/nac["validos"]*100:.2f}%')
    eleicoes[k] = {"cand": [{"id": c[0], "nome": c[1], "grupo": c[2], "cor": c[3]} for c in ordem], "nac": nac, "reg": reg}
P = {"pais": "RO", "nome": "Romênia", "nivel": "Distrito", "sistema": "2 turnos",
     "fonte": "Autoritatea Electorală Permanentă, atas de todas as seções (prezenta.roaep.ro)", "fonte_url": "https://prezenta.roaep.ro/prezidentiale18052025/",
     "nota": "Percentual sobre votos válidos. Eleição refeita em 2025 depois que a Corte Constitucional anulou a de novembro de 2024. Eleitores = inscritos na lista permanente; quem vota em lista suplementar ou no exterior (sem lista) entra só nos votantes, por isso o comparecimento segue o cálculo oficial.",
     "eleicoes": [{"ano": 2025, "turnos": eleicoes}]}
os.makedirs(OUT, exist_ok=True)
json.dump(P, open(os.path.join(OUT, "ro.json"), "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
