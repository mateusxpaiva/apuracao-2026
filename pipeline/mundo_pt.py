"""Portugal (MAI / SGMAI, Presidenciais 2026, resultados por distrito) -> data/mundo/pt.json

Uso: python pipeline/mundo_pt.py RAW_PT_DIR OUT_DIR
RAW_PT_DIR tem ch_{eleição}.json (distritos), d_{eleição}_{território}.json (resultado por distrito),
r_{eleição}_{território}.json (total global e estrangeiro). Fonte: www.eleicoes.mai.gov.pt.
"""
import json, os, sys

RAW, OUT = sys.argv[1], sys.argv[2]
OUTRO = "#5B6478"
COR = {"António José Seguro": "#E8508F", "André Ventura": "#3B78EA", "João Cotrim de Figueiredo": "#38B2C9",
       "Henrique Gouveia e Melo": "#E2B84B", "Luís Marques Mendes": "#F28C28"}
EL = {"1": (51, 54667, 54668), "2": (61, 65608, 65609)}


def ld(n):
    return json.load(open(os.path.join(RAW, n), encoding="utf-8"))["data"]


def linha(tid, nome, cr):
    v = {p["acronym"]: p["votes"] for p in cr["resultsParty"]}
    return {"id": str(tid), "n": nome, "eleitores": cr["subscribedVoters"], "votantes": cr["totalVoters"],
            "brancos": cr["blankVotes"], "nulos": cr["nullVotes"], "validos": sum(v.values()), "v": v}


turnos = {}
for k, (el, glob, ext) in EL.items():
    reg = []
    for t in ld(f"ch_{el}.json"):
        d = ld(f"d_{el}_{t['id']}.json")
        reg.append(linha(t["id"], t["descriptionShort"].replace("Região Autónoma dos ", "").replace("Região Autónoma da ", ""), d["currentResults"]))
    reg.append(linha("EXT", "Estrangeiro", ld(f"r_{el}_{ext}.json")["currentResults"]))
    g = ld(f"r_{el}_{glob}.json")["currentResults"]
    tot = linha("G", "Total", g)
    nac = {x: sum(r[x] for r in reg) for x in ("eleitores", "votantes", "brancos", "nulos", "validos")}
    nac["v"] = {}
    for r in reg:
        for c, v in r["v"].items():
            nac["v"][c] = nac["v"].get(c, 0) + v
    print(k, "MAI global:", tot["validos"], tot["brancos"], tot["nulos"], tot["votantes"], tot["eleitores"], "| soma:", nac["validos"], nac["brancos"], nac["nulos"], nac["votantes"], nac["eleitores"])
    assert nac["v"] == tot["v"], "votos por candidato não batem com o total global do MAI"
    ordem = sorted(nac["v"], key=lambda c: -nac["v"][c])
    cands = [{"id": c, "nome": c, "grupo": "", "cor": COR.get(c, OUTRO)} for c in ordem]
    for c in ordem[:5]:
        print("   ", c, nac["v"][c], f'{nac["v"][c] / nac["validos"] * 100:.2f}%')
    turnos[k] = {"cand": cands, "nac": nac, "reg": reg}

P = {"pais": "PT", "nome": "Portugal", "nivel": "Distrito", "sistema": "2 turnos",
     "fonte": "Ministério da Administração Interna (SGMAI), resultados oficiais por distrito e região autónoma",
     "fonte_url": "https://www.eleicoes.mai.gov.pt/presidenciais2026_2S/",
     "nota": "Percentual sobre votos válidos (sem brancos e nulos), como no Brasil. Açores e Madeira são regiões autónomas; Estrangeiro = portugueses votando fora do país. Presidenciais de 18 de janeiro e 8 de fevereiro de 2026, a primeira com 2º turno desde 1986.",
     "eleicoes": [{"ano": 2026, "turnos": turnos}]}
os.makedirs(OUT, exist_ok=True)
json.dump(P, open(os.path.join(OUT, "pt.json"), "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
