"""Presidente por município (TSE): soma as zonas de cada cidade e grava data/pres/{ano}.json.

Uso: python pipeline/presidente_mun.py 2018 2022 2026

Saída por ano:
{"ano":2026,
 "cand":{"1":{"13":["LULA","PT"],...},"2":{...}},
 "ord":{"1":["13","22",...],"2":["13","22"]},          # ordem nacional dos candidatos
 "mun":{cd_tse:["NOME","UF"]},
 "t":{"1":{cd_tse:[aptos,comparecimento,brancos,nulos,v_ord0,v_ord1,...]},"2":{...}}}
"""
import json, os, sys, tempfile
from collections import defaultdict
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from municipais import BASE, baixar, n  # mesmas rotinas de download do coletor municipal
import csv, io, zipfile

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "pres")
UFS = "AC AL AM AP BA CE DF ES GO MA MG MS MT PA PB PE PI PR RJ RN RO RR RS SC SE SP TO ZZ".split()


def membros(zpath):
    with zipfile.ZipFile(zpath) as z:
        nomes = [m for m in z.namelist() if m.lower().endswith(".csv")]
    br = [m for m in nomes if m.upper().endswith("_BR.CSV")]
    if br:
        return br
    return [m for m in nomes if any(m.upper().endswith(f"_{u}.CSV") for u in UFS)]


def ler(zpath):
    with zipfile.ZipFile(zpath) as z:
        for m in membros(zpath):
            print("   lendo", m, flush=True)
            with z.open(m) as raw:
                for r in csv.DictReader(io.TextIOWrapper(raw, encoding="latin-1", newline=""), delimiter=";", quotechar='"'):
                    yield r


def processar(ano, tmp):
    zc = baixar(f"{BASE}/votacao_candidato_munzona/votacao_candidato_munzona_{ano}.zip", os.path.join(tmp, f"pc_{ano}.zip"))
    zd = baixar(f"{BASE}/detalhe_votacao_munzona/detalhe_votacao_munzona_{ano}.zip", os.path.join(tmp, f"pd_{ano}.zip"))
    votos = defaultdict(lambda: defaultdict(int))   # (turno, cd) -> nr -> votos
    cand, mun = defaultdict(dict), {}
    for r in ler(zc):
        if r.get("CD_CARGO") != "1" or r.get("CD_TIPO_ELEICAO", "2") != "2":
            continue
        t, cd, nr = r["NR_TURNO"], r["CD_MUNICIPIO"].lstrip("0"), r["NR_CANDIDATO"]
        votos[(t, cd)][nr] += n(r.get("QT_VOTOS_NOMINAIS_VALIDOS") or r.get("QT_VOTOS_NOMINAIS"))
        cand[t][nr] = [r["NM_URNA_CANDIDATO"], r["SG_PARTIDO"]]
        mun[cd] = [r["NM_MUNICIPIO"], r["SG_UF"]]
    det = defaultdict(lambda: [0, 0, 0, 0])
    for r in ler(zd):
        if r.get("CD_CARGO") != "1" or r.get("CD_TIPO_ELEICAO", "2") != "2":
            continue
        d = det[(r["NR_TURNO"], r["CD_MUNICIPIO"].lstrip("0"))]
        d[0] += n(r["QT_APTOS"]); d[1] += n(r["QT_COMPARECIMENTO"]); d[2] += n(r["QT_VOTOS_BRANCOS"])
        d[3] += n(r.get("QT_TOTAL_VOTOS_NULOS") or r.get("QT_VOTOS_NULOS"))
    out = {"ano": ano, "cand": cand, "ord": {}, "mun": mun, "t": {}}
    for t in sorted(cand):
        tot = defaultdict(int)
        for (tt, cd), v in votos.items():
            if tt == t:
                for nr, q in v.items(): tot[nr] += q
        ordem = sorted(tot, key=lambda x: -tot[x]); out["ord"][t] = ordem
        out["t"][t] = {cd: det[(t, cd)] + [votos[(t, cd)].get(nr, 0) for nr in ordem] for (tt, cd) in votos if tt == t}
        print(f"  {ano} turno {t}: {len(out['t'][t])} municípios; " + ", ".join(f"{cand[t][nr][0]} {tot[nr]:,}" for nr in ordem[:3]), flush=True)
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, f"{ano}.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, separators=(",", ":"))


if __name__ == "__main__":
    with tempfile.TemporaryDirectory() as tmp:
        for a in sys.argv[1:]:
            print("Ano", a, flush=True)
            processar(int(a), tmp)
