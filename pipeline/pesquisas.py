"""Pesquisas eleitorais registradas no TSE (PesqEle) -> data/pesquisas/{ano}.json

Uso: python pipeline/pesquisas.py 2022 2024 2026
O TSE publica o registro (quem fez, quando, quanto custou, quantas entrevistas, onde),
não o resultado das pesquisas.
"""
import csv, io, json, os, re, sys, tempfile, zipfile
from collections import Counter, defaultdict
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from municipais import BASE, baixar

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "pesquisas")


def num(s):
    s = (s or "").replace(".", "").replace(",", ".")
    try:
        return float(s)
    except ValueError:
        return 0.0


def data(s):
    return (s or "")[:10] if s and s[0].isdigit() and len(s) >= 10 and s[4] == "-" else ""


def nome_empresa(r):
    f = (r.get("NM_EMPRESA_FANTASIA") or "").strip()
    n = f if f and f != "#NULO#" else (r.get("NM_EMPRESA") or "").strip()
    n = re.sub(r"\s+(LTDA|EIRELI|ME|EPP|S/?A|S\.A\.?)\.?$", "", n, flags=re.I).strip(" -.")
    return n.title()


def linhas(zpath):
    with zipfile.ZipFile(zpath) as z:
        nomes = [m for m in z.namelist() if m.lower().endswith(".csv")]
        br = [m for m in nomes if m.upper().endswith(("_BRASIL.CSV", "_BR.CSV"))]
        for m in (br or nomes):
            with z.open(m) as raw:
                for r in csv.DictReader(io.TextIOWrapper(raw, encoding="latin-1", newline=""), delimiter=";"):
                    yield r


def processar(ano, tmp):
    z = baixar(f"{BASE}/pesquisa_eleitoral/pesquisa_eleitoral_{ano}.zip", os.path.join(tmp, f"p_{ano}.zip"))
    vistos, emp, uf, mes, cargo, cidades = set(), defaultdict(lambda: {"n": 0, "valor": 0.0, "entrev": 0, "propria": 0, "ufs": set()}), Counter(), Counter(), Counter(), Counter()
    nac = []
    total, valor, entrev = 0, 0.0, 0
    for r in linhas(z):
        p = r.get("NR_PROTOCOLO_REGISTRO")
        if not p or p in vistos:
            continue
        vistos.add(p)
        cnpj = re.sub(r"\D", "", r.get("NR_CNPJ_EMPRESA") or "")[:8] or nome_empresa(r)
        e = emp[cnpj]
        e.setdefault("nome", nome_empresa(r))
        v, q = num(r.get("VR_PESQUISA")), int(num(r.get("QT_ENTREVISTADO")))
        e["n"] += 1; e["valor"] += v; e["entrev"] += q; e["ufs"].add(r.get("SG_UF"))
        if r.get("ST_PESQUISA_PROPRIA") == "S":
            e["propria"] += 1
        total += 1; valor += v; entrev += q
        uf[r.get("SG_UF")] += 1
        dreg = data(r.get("DT_REGISTRO"))
        if dreg:
            mes[dreg[:7]] += 1
        for c in (r.get("DS_CARGO") or "").split(","):
            c = c.strip()
            if c and c != "#NULO#":
                cargo[c] += 1
        if r.get("SG_UF") not in ("BR", "ZZ") and r.get("NM_UE") and r.get("SG_UE") != r.get("SG_UF"):
            cidades[f'{r.get("NM_UE").title()} ({r.get("SG_UF")})'] += 1
        if r.get("SG_UF") == "BR":
            nac.append([data(r.get("DT_DIVULGACAO")), data(r.get("DT_INICIO_PESQUISA")), data(r.get("DT_FIM_PESQUISA")), e["nome"], q, round(v, 2), p, r.get("ST_PESQUISA_PROPRIA") == "S"])
    nac.sort(key=lambda x: x[0] or x[2], reverse=True)
    emps = sorted(({"nome": e["nome"], "n": e["n"], "valor": round(e["valor"], 2), "entrev": e["entrev"], "propria": e["propria"], "ufs": len(e["ufs"])} for e in emp.values()), key=lambda x: -x["n"])
    out = {"ano": ano, "total": total, "valor": round(valor, 2), "entrevistas": entrev, "institutos": len(emps),
           "empresas": emps[:60], "uf": dict(uf), "mes": dict(sorted(mes.items())), "cargo": dict(cargo.most_common(12)),
           "cidades": cidades.most_common(25), "nacionais": nac}
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, f"{ano}.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, separators=(",", ":"))
    print(f"{ano}: {total} pesquisas, R$ {valor:,.0f}, {len(emps)} institutos, {len(nac)} nacionais; top: " + ", ".join(f'{e["nome"]} ({e["n"]})' for e in emps[:5]), flush=True)


if __name__ == "__main__":
    with tempfile.TemporaryDirectory() as tmp:
        for a in sys.argv[1:]:
            processar(int(a), tmp)
