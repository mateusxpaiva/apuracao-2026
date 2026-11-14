"""Coletor de eleições municipais (prefeito e vereador) do TSE.

Baixa os arquivos do Portal de Dados Abertos do TSE, soma zonas por município e
publica JSON compactos em data/mun/. Uso:

    python pipeline/municipais.py 2016 2020 2024

Saídas
  data/mun/{ano}/{UF}.json      prefeitos (por turno) e totais de vereador por município
  data/mun/{ano}/{UF}_v.json    candidatos a vereador por município e votos por partido
  data/mun/index.json           código TSE do município -> [nome, UF]
  data/mun/resumo.json          resumo nacional por ano (partidos, comparecimento, reeleição)
"""
import csv, io, json, os, sys, time, unicodedata, urllib.request, zipfile
from collections import defaultdict

BASE = os.environ.get("TSE_BASE", "https://cdn.tse.jus.br/estatistica/sead/odsele")
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "mun")
UFS = "AC AL AM AP BA CE ES GO MA MG MS MT PA PB PE PI PR RJ RN RO RR RS SC SE SP TO".split()
PREF, VER = "11", "13"


def baixar(url, destino, tentativas=5):
    if os.path.exists(destino) and os.path.getsize(destino) > 0:
        return destino
    for i in range(tentativas):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (apuracao-por-ia coletor)"})
            with urllib.request.urlopen(req, timeout=300) as r, open(destino + ".part", "wb") as f:
                while True:
                    b = r.read(1 << 20)
                    if not b:
                        break
                    f.write(b)
            os.replace(destino + ".part", destino)
            print(f"  baixado {os.path.basename(destino)} ({os.path.getsize(destino)/1e6:.1f} MB)", flush=True)
            return destino
        except Exception as e:  # rede instável: tenta de novo
            print(f"  falha ao baixar {url}: {e} (tentativa {i+1})", flush=True)
            time.sleep(10 * (i + 1))
    raise SystemExit(f"Não foi possível baixar {url}")


def linhas(zpath, sufixo):
    """Lê o CSV de uma UF dentro do zip do TSE como dicionários."""
    with zipfile.ZipFile(zpath) as z:
        nome = next((n for n in z.namelist() if n.upper().endswith(sufixo.upper())), None)
        if not nome:
            return
        with z.open(nome) as raw:
            txt = io.TextIOWrapper(raw, encoding="latin-1", newline="")
            for row in csv.DictReader(txt, delimiter=";", quotechar='"'):
                yield row


def n(v):
    try:
        return int(v)
    except (TypeError, ValueError):
        return 0


def sit(ds):
    ds = (ds or "").upper()
    if ds.startswith("ELEITO"):
        return "E"
    if "2º TURNO" in ds or "2O TURNO" in ds or ds.startswith("2"):
        return "T"
    if ds.startswith("SUPLENTE"):
        return "S"
    return "N"


def chave_nome(s):
    s = unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode().upper()
    return " ".join(s.split())


def processar_ano(ano, tmp):
    zc = baixar(f"{BASE}/votacao_candidato_munzona/votacao_candidato_munzona_{ano}.zip", os.path.join(tmp, f"cand_{ano}.zip"))
    zd = baixar(f"{BASE}/detalhe_votacao_munzona/detalhe_votacao_munzona_{ano}.zip", os.path.join(tmp, f"det_{ano}.zip"))
    zp = baixar(f"{BASE}/votacao_partido_munzona/votacao_partido_munzona_{ano}.zip", os.path.join(tmp, f"part_{ano}.zip"))
    os.makedirs(os.path.join(OUT, str(ano)), exist_ok=True)
    indice, pref_por_mun = {}, {}
    for uf in UFS:
        mun = {}
        # candidatos: soma das zonas
        cand = defaultdict(lambda: {"v": 0})
        for r in linhas(zc, f"_{uf}.csv"):
            if r.get("CD_TIPO_ELEICAO") != "2" or r.get("CD_CARGO") not in (PREF, VER):
                continue
            k = (r["CD_MUNICIPIO"].lstrip("0") or "0", r["CD_CARGO"], r["NR_TURNO"], r["SQ_CANDIDATO"])
            c = cand[k]
            c["v"] += n(r.get("QT_VOTOS_NOMINAIS_VALIDOS", r.get("QT_VOTOS_NOMINAIS")))
            c["nr"], c["nm"], c["nc"], c["sg"] = r["NR_CANDIDATO"], r["NM_URNA_CANDIDATO"], r["NM_CANDIDATO"], r["SG_PARTIDO"]
            c["s"] = sit(r.get("DS_SIT_TOT_TURNO"))
            mun.setdefault(k[0], {"n": r["NM_MUNICIPIO"]})
        # detalhe: comparecimento, brancos, nulos etc.
        det = defaultdict(lambda: [0] * 7)
        for r in linhas(zd, f"_{uf}.csv"):
            if r.get("CD_TIPO_ELEICAO") != "2" or r.get("CD_CARGO") not in (PREF, VER):
                continue
            k = (r["CD_MUNICIPIO"].lstrip("0") or "0", r["CD_CARGO"], r["NR_TURNO"])
            d = det[k]
            d[0] += n(r["QT_APTOS"]); d[1] += n(r["QT_COMPARECIMENTO"]); d[2] += n(r["QT_ABSTENCOES"])
            d[3] += n(r["QT_TOTAL_VOTOS_VALIDOS"]); d[4] += n(r["QT_VOTOS_BRANCOS"])
            d[5] += n(r.get("QT_TOTAL_VOTOS_NULOS", r.get("QT_VOTOS_NULOS")))
            d[6] += n(r.get("QT_TOTAL_VOTOS_LEG_VALIDOS"))
            mun.setdefault(k[0], {"n": r["NM_MUNICIPIO"]})
        # votos por partido (vereador): nominais + legenda
        part = defaultdict(lambda: [0, 0])
        for r in linhas(zp, f"_{uf}.csv"):
            if r.get("CD_TIPO_ELEICAO") != "2" or r.get("CD_CARGO") != VER:
                continue
            p = part[(r["CD_MUNICIPIO"].lstrip("0") or "0", r["SG_PARTIDO"])]
            p[0] += n(r.get("QT_VOTOS_NOMINAIS_VALIDOS")); p[1] += n(r.get("QT_VOTOS_LEGENDA_VALIDOS"))

        por_mun = defaultdict(list)
        for (m, cg, tt, _), c in cand.items():
            por_mun[m].append((cg, tt, c))
        part_mun = defaultdict(dict)
        for (m, sg), v in part.items():
            part_mun[m][sg] = v
        prefs, vers = {}, {}
        for cd, info in mun.items():
            cl = por_mun.get(cd, [])
            indice[cd] = [info["n"], uf]
            pm = {"n": info["n"], "p": {}, "vt": None}
            for t in ("1", "2"):
                d = det.get((cd, PREF, t))
                cs = sorted(((c["nr"], c["nm"], c["sg"], c["v"], c["s"]) for cg, tt, c in cl if cg == PREF and tt == t), key=lambda x: -x[3])
                if d or cs:
                    pm["p"][t] = {"t": (d or [0] * 7)[:6], "c": [list(x) for x in cs]}
            dv = det.get((cd, VER, "1"))
            if dv:
                pm["vt"] = dv  # aptos, comparec., abst., válidos, brancos, nulos, legenda
            vc = sorted(((c["nr"], c["nm"], c["sg"], c["v"], c["s"]) for cg, tt, c in cl if cg == VER), key=lambda x: -x[3])
            vp = part_mun.get(cd, {})
            prefs[cd] = pm
            vers[cd] = {"c": [list(x) for x in vc], "p": vp}
            # para reeleição: nome completo do prefeito eleito
            for cg, tt, c in cl:
                if cg == PREF and c["s"] == "E":
                    pref_por_mun[cd] = {"nome": chave_nome(c["nc"]), "sg": c["sg"], "uf": uf}
        with open(os.path.join(OUT, str(ano), f"{uf}.json"), "w", encoding="utf-8") as f:
            json.dump({"ano": ano, "uf": uf, "mun": prefs}, f, ensure_ascii=False, separators=(",", ":"))
        with open(os.path.join(OUT, str(ano), f"{uf}_v.json"), "w", encoding="utf-8") as f:
            json.dump({"ano": ano, "uf": uf, "mun": vers}, f, ensure_ascii=False, separators=(",", ":"))
        print(f"  {ano} {uf}: {len(prefs)} municípios", flush=True)
    with open(os.path.join(OUT, str(ano), "eleitos.json"), "w", encoding="utf-8") as f:
        json.dump(pref_por_mun, f, ensure_ascii=False, separators=(",", ":"))
    return indice


def resumo():
    """Resumo nacional a partir dos arquivos já gerados."""
    anos = sorted(int(a) for a in os.listdir(OUT) if a.isdigit())
    res = {"anos": anos, "por_ano": {}}
    for ano in anos:
        pref_partido, pref_eleitorado, ver_partido = defaultdict(int), defaultdict(int), defaultdict(int)
        tot = [0] * 6; nmun = 0; seg_turno = 0
        for uf in UFS:
            p = os.path.join(OUT, str(ano), f"{uf}.json")
            if not os.path.exists(p):
                continue
            mun = json.load(open(p, encoding="utf-8"))["mun"]
            vmun = json.load(open(os.path.join(OUT, str(ano), f"{uf}_v.json"), encoding="utf-8"))["mun"]
            for cd, m in mun.items():
                nmun += 1
                if "2" in m["p"]:
                    seg_turno += 1
                t1 = m["p"].get("1")
                if t1:
                    for i in range(6):
                        tot[i] += t1["t"][i]
                for t in ("2", "1"):
                    if t in m["p"]:
                        el = [c for c in m["p"][t]["c"] if c[4] == "E"]
                        if el:
                            pref_partido[el[0][2]] += 1
                            pref_eleitorado[el[0][2]] += (m["p"]["1"]["t"][0] if "1" in m["p"] else 0)
                            break
                for c in vmun.get(cd, {}).get("c", []):
                    if c[4] == "E":
                        ver_partido[c[2]] += 1
        res["por_ano"][str(ano)] = {
            "municipios": nmun, "segundo_turno": seg_turno,
            "aptos": tot[0], "comparecimento": tot[1], "abstencao": tot[2], "validos": tot[3], "brancos": tot[4], "nulos": tot[5],
            "prefeitos_por_partido": dict(sorted(pref_partido.items(), key=lambda x: -x[1])),
            "eleitorado_governado_por_partido": dict(sorted(pref_eleitorado.items(), key=lambda x: -x[1])),
            "vereadores_por_partido": dict(sorted(ver_partido.items(), key=lambda x: -x[1])),
        }
    # reeleição e continuidade partidária entre eleições consecutivas
    res["reeleicao"] = {}
    for a, b in zip(anos, anos[1:]):
        ea = json.load(open(os.path.join(OUT, str(a), "eleitos.json"), encoding="utf-8"))
        eb = json.load(open(os.path.join(OUT, str(b), "eleitos.json"), encoding="utf-8"))
        comuns = [cd for cd in eb if cd in ea]
        reel = sum(1 for cd in comuns if ea[cd]["nome"] == eb[cd]["nome"])
        mesmo = sum(1 for cd in comuns if ea[cd]["sg"] == eb[cd]["sg"])
        res["reeleicao"][f"{a}-{b}"] = {"municipios": len(comuns), "mesmo_prefeito": reel, "mesmo_partido": mesmo}
    with open(os.path.join(OUT, "resumo.json"), "w", encoding="utf-8") as f:
        json.dump(res, f, ensure_ascii=False, separators=(",", ":"))
    print("resumo:", json.dumps({k: (v["municipios"], v["segundo_turno"]) for k, v in res["por_ano"].items()}), res["reeleicao"], flush=True)


def main():
    anos = [int(a) for a in sys.argv[1:]] or [2016, 2020, 2024]
    tmp = os.environ.get("TSE_TMP", "/tmp/tse")
    os.makedirs(tmp, exist_ok=True)
    idx_path = os.path.join(OUT, "index.json")
    os.makedirs(OUT, exist_ok=True)
    indice = json.load(open(idx_path, encoding="utf-8")) if os.path.exists(idx_path) else {}
    for ano in anos:
        print(f"== {ano}", flush=True)
        indice.update(processar_ano(ano, tmp))
    with open(idx_path, "w", encoding="utf-8") as f:
        json.dump(dict(sorted(indice.items(), key=lambda x: (x[1][1], x[1][0]))), f, ensure_ascii=False, separators=(",", ":"))
    resumo()


if __name__ == "__main__":
    main()
