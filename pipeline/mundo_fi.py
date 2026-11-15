"""Finlândia (Statistics Finland, eleições presidenciais 2012, 2018 e 2024, por distrito eleitoral) -> data/mundo/fi.json

Uso: python pipeline/mundo_fi.py 14db.csv OUT_DIR
Fonte: tabela StatFin 14db (Ehdokkaiden kannatus ja äänet vaalipiireittäin), API PxWeb pxdata.stat.fi.
A tabela traz votos por candidato; eleitores e nulos ficam de fora (estão em outra tabela).
"""
import csv, json, os, sys
from collections import defaultdict

SRC, OUT = sys.argv[1], sys.argv[2]
OUTRO = "#5B6478"
COR = {"Alexander Stubb": "#3B78EA", "Pekka Haavisto": "#3FAE5A", "Jussi Halla-aho": "#E2B84B", "Olli Rehn": "#38B2C9", "Li Andersson": "#B5179E",
       "Sauli Niinistö": "#3B78EA", "Paavo Väyrynen": "#7CB342", "Laura Huhtasaari": "#E2B84B", "Matti Vanhanen": "#38B2C9", "Tuula Haatainen": "#E0353D",
       "Timo Soini": "#E2B84B", "Paavo Lipponen": "#E0353D"}
VP = {"Helsingin": "Helsinque", "Uudenmaan": "Uusimaa", "Varsinais-Suomen": "Finlândia Própria", "Satakunnan": "Satakunta", "Ahvenanmaan maakunnan": "Åland",
      "Hämeen": "Häme", "Pirkanmaan": "Pirkanmaa", "Kaakkois-Suomen": "Sudeste", "Savo-Karjalan": "Savônia-Carélia", "Vaasan": "Vaasa",
      "Keski-Suomen": "Finlândia Central", "Oulun": "Oulu", "Lapin": "Lapônia"}
dados = defaultdict(lambda: defaultdict(lambda: defaultdict(dict)))  # ano -> turno -> vaalipiiri -> cand -> votos
for r in csv.DictReader(open(SRC, encoding="utf-8-sig")):
    ano = int(r["Vuosi"])
    if ano < 2012 or r["Äänet (lkm.)"] in ("", ".", "..", "..."):
        continue
    t = "1" if r["Kierros"].startswith("Ensimm") else "2"
    dados[ano][t][r["Vaalipiiri"]][r["Ehdokkaat"]] = int(r["Äänet (lkm.)"])
eleicoes = []
for ano in sorted(dados):
    turnos = {}
    for t, vp in sorted(dados[ano].items()):
        if not any(vp.get("Koko maa", {}).values()):
            continue
        META = ("Hyväksytyt äänet", "Hylätyt äänet")
        nacv = {c: v for c, v in vp["Koko maa"].items() if v and c not in META}
        cands = sorted(nacv, key=lambda c: -nacv[c])
        ids = {c: f"C{i}" for i, c in enumerate(cands)}
        reg = []
        for nome, vv in vp.items():
            if nome == "Koko maa":
                continue
            curto = nome.split(" ", 1)[1].replace(" vaalipiiri", "") if nome.startswith("VP") else nome
            v = {ids[c]: x for c, x in vv.items() if c in ids}
            val = sum(v.values())
            if val == 0:
                continue
            assert val == vv.get("Hyväksytyt äänet", val), (ano, t, nome)
            nul = vv.get("Hylätyt äänet")
            reg.append({"id": nome[:4], "n": VP.get(curto, curto), "eleitores": None, "votantes": val + (nul or 0), "brancos": None, "nulos": nul, "validos": val, "v": v})
        nac = {"eleitores": None, "votantes": sum(r["votantes"] for r in reg), "brancos": None, "nulos": sum(r["nulos"] or 0 for r in reg), "validos": sum(r["validos"] for r in reg)}
        assert nac["validos"] == vp["Koko maa"]["Hyväksytyt äänet"]
        nac["v"] = {ids[c]: sum(r["v"].get(ids[c], 0) for r in reg) for c in cands}
        assert all(nac["v"][ids[c]] == nacv[c] for c in cands), (ano, t, "distritos não somam o país")
        cl = [{"id": ids[c], "nome": c, "grupo": "", "cor": COR.get(c, OUTRO) if (cands.index(c) < 5 or t == "2") else OUTRO} for c in cands]
        turnos[t] = {"cand": cl, "nac": nac, "reg": reg}
        print(ano, t, len(reg), "distritos ·", " · ".join(f'{c} {nacv[c]} ({nacv[c]/nac["validos"]*100:.2f}%)' for c in cands[:3]))
    eleicoes.append({"ano": ano, "turnos": turnos})
P = {"pais": "FI", "nome": "Finlândia", "nivel": "Distrito eleitoral", "sistema": "2 turnos",
     "fonte": "Statistics Finland (Tilastokeskus), tabela StatFin 14db de votos por candidato e distrito eleitoral", "fonte_url": "https://pxdata.stat.fi/PxWeb/pxweb/fi/StatFin/StatFin__pvaa/",
     "nota": "Percentual sobre votos válidos. A tabela oficial usada não traz eleitores aptos, por isso o comparecimento não aparece. Em 2018 Sauli Niinistö venceu no 1º turno. Votos do exterior estão no distrito de Helsinque, como na contagem oficial.",
     "eleicoes": eleicoes}
os.makedirs(OUT, exist_ok=True)
json.dump(P, open(os.path.join(OUT, "fi.json"), "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
