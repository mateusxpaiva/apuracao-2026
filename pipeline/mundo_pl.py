"""Polônia (PKW, eleição presidencial 2025, por voivodia + exterior) -> data/mundo/pl.json

Uso: python pipeline/mundo_pl.py PASTA_CSV OUT_DIR
PASTA_CSV tem wyniki_gl_na_kandydatow_po_gminach_utf8.csv (1º turno) e ..._w_drugiej_turze_utf8.csv (2º turno),
da página "Dane w arkuszach" da PKW (prezydent2025.pkw.gov.pl). O arquivo por município inclui exterior e navios.
"""
import csv, json, os, sys
from collections import defaultdict

DIR, OUT = sys.argv[1], sys.argv[2]
OUTRO = "#5B6478"
COR = {"NAWROCKI": "#3B78EA", "TRZASKOWSKI": "#F28C28", "MENTZEN": "#1F9E8E", "BRAUN": "#7C5CE0", "HOŁOWNIA": "#E2B84B", "ZANDBERG": "#B5179E", "BIEJAT": "#E0353D"}
VOI = {"dolnośląskie": "Baixa Silésia", "kujawsko-pomorskie": "Cuiávia-Pomerânia", "lubelskie": "Lublin", "lubuskie": "Lubúsquia", "łódzkie": "Łódź",
       "małopolskie": "Pequena Polônia", "mazowieckie": "Mazóvia", "opolskie": "Opole", "podkarpackie": "Subcarpácia", "podlaskie": "Podláquia",
       "pomorskie": "Pomerânia", "śląskie": "Silésia", "świętokrzyskie": "Santa Cruz", "warmińsko-mazurskie": "Vármia-Masúria",
       "wielkopolskie": "Grande Polônia", "zachodniopomorskie": "Pomerânia Ocidental"}
VAL = "Liczba głosów ważnych oddanych łącznie na wszystkich kandydatów"


def n(s):
    s = (s or "").strip()
    return int(s) if s else 0


def nome(col):
    p = col.split()
    return " ".join(x.title() for x in p[1:2]) + " " + p[0].title()


def turno(arq):
    rows = list(csv.DictReader(open(os.path.join(DIR, arq), encoding="utf-8-sig"), delimiter=";"))
    cols = [c for c in rows[0] if c.isupper() or (c.split()[0].isupper() and len(c.split()) > 1 and c.split()[0] not in ("TERYT",))]
    cols = [c for c in cols if c.split()[0].upper() == c.split()[0] and c.split()[0] not in ("TERYT", "W")]
    reg = defaultdict(lambda: {"eleitores": 0, "votantes": 0, "brancos": None, "nulos": 0, "validos": 0, "v": defaultdict(int)})
    for r in rows:
        k = r["Województwo"] or "EXT"
        g = reg[k]
        g["eleitores"] += n(r["Liczba wyborców uprawnionych do głosowania"])
        vot = n(r["Liczba kart wyjętych z urny"]); val = n(r[VAL])
        g["votantes"] += vot; g["validos"] += val; g["nulos"] += vot - val
        for c in cols:
            g["v"][c.split()[0]] += n(r[c])
    out = []
    for k in list(VOI) + ["EXT"]:
        g = reg[k]
        assert sum(g["v"].values()) == g["validos"], k
        out.append({"id": k, "n": VOI.get(k, "Exterior e navios"), **{x: g[x] for x in ("eleitores", "votantes", "brancos", "nulos", "validos")}, "v": dict(g["v"])})
    nac = {x: sum(r[x] for r in out) for x in ("eleitores", "votantes", "nulos", "validos")}; nac["brancos"] = None
    nac["v"] = {c.split()[0]: sum(r["v"][c.split()[0]] for r in out) for c in cols}
    ordem = sorted(cols, key=lambda c: -nac["v"][c.split()[0]])
    cands = [{"id": c.split()[0], "nome": nome(c), "grupo": "", "cor": COR.get(c.split()[0], OUTRO)} for c in ordem]
    print(arq[:60], "eleitores", nac["eleitores"], "votantes", nac["votantes"], "válidos", nac["validos"])
    for c in cands[:6]:
        print("   ", c["nome"], nac["v"][c["id"]], f'{nac["v"][c["id"]] / nac["validos"] * 100:.2f}%')
    return {"cand": cands, "nac": nac, "reg": out}


P = {"pais": "PL", "nome": "Polônia", "nivel": "Voivodia", "sistema": "2 turnos",
     "fonte": "Państwowa Komisja Wyborcza (PKW), resultados por município em 18/05 e 01/06/2025, versão de 23/09/2025",
     "fonte_url": "https://prezydent2025.pkw.gov.pl/prezydent2025/pl/dane_w_arkuszach",
     "nota": "Percentual sobre votos válidos. Exterior e navios somados numa linha. Os arquivos da PKW (versão de 23/09/2025) diferem em menos de 300 votos por candidato do resultado anunciado em 2 de junho de 2025 (Nawrocki 10.606.877 × Trzaskowski 10.237.286).",
     "eleicoes": [{"ano": 2025, "turnos": {"1": turno("wyniki_gl_na_kandydatow_po_gminach_utf8.csv"), "2": turno("wyniki_gl_na_kandydatow_po_gminach_w_drugiej_turze_utf8.csv")}}]}
os.makedirs(OUT, exist_ok=True)
json.dump(P, open(os.path.join(OUT, "pl.json"), "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
