"""Noruega (Valgdirektoratet, eleição do Storting de 08/09/2025, por distrito eleitoral) -> data/mundo/no.json

Uso: python pipeline/mundo_no.py PASTA OUT_DIR
PASTA tem api.json (nacional) e k{nr}.json (19 distritos), da API pública valgresultat.no/api/2025/st.
"""
import json, os, sys

D, OUT = sys.argv[1], sys.argv[2]
OUTRO = "#5B6478"
PART = [("A", "Trabalhistas (Ap)", "Jonas Gahr Støre", "#E0353D"), ("FRP", "Partido do Progresso (FrP)", "Sylvi Listhaug", "#3B78EA"),
        ("H", "Conservadores (Høyre)", "Ine Eriksen Søreide", "#38B2C9"), ("SV", "Esquerda Socialista (SV)", "", "#B5179E"),
        ("SP", "Centro (Sp)", "", "#3FAE5A"), ("RØDT", "Vermelho (Rødt)", "", "#8B1E2E"), ("MDG", "Verdes (MDG)", "", "#7CB342"),
        ("KRF", "Democrata-Cristão (KrF)", "", "#E2B84B"), ("V", "Liberal (Venstre)", "", "#F28C28")]
IDS = [p[0] for p in PART]
nac_api = json.load(open(os.path.join(D, "api.json"), encoding="utf-8"))
reg = []
for r in nac_api["_links"]["related"]:
    d = json.load(open(os.path.join(D, f"k{r['nr']}.json"), encoding="utf-8"))
    v = {k: 0 for k in IDS + ["O"]}; seats = {k: 0 for k in IDS + ["O"]}
    blank = 0
    for p in d["partier"]:
        if p["id"]["partikategori"] == 0:
            continue  # "Andre": soma de outros partidos que já aparecem na lista
        if p["id"]["partikode"] == "BLANKE":
            blank += p["stemmer"]["resultat"]["antall"]["total"]; continue
        k = p["id"]["partikode"] if p["id"]["partikode"] in IDS else "O"
        v[k] += p["stemmer"]["resultat"]["antall"]["total"]; seats[k] += p["mandater"]["resultat"]["antall"] or 0
    val = sum(v.values()); nul = d["stemmer"]["totalForkastede"]
    assert val + blank == d["stemmer"]["total"], r["navn"]
    reg.append({"id": r["nr"], "n": r["navn"].split(" ")[0] if r["nr"] in ("55", "56") else r["navn"], "eleitores": d["antallsb"], "votantes": val + blank + nul,
                "brancos": blank, "nulos": nul, "validos": val, "v": v, "_s": seats})
nac = {x: sum(r[x] for r in reg) for x in ("eleitores", "votantes", "brancos", "nulos", "validos")}
nac["v"] = {k: sum(r["v"][k] for r in reg) for k in IDS + ["O"]}
seats = {k: sum(r["_s"][k] for r in reg) for k in IDS + ["O"]}
for r in reg: del r["_s"]
tot_api = {p["id"]["partikode"]: p["stemmer"]["resultat"]["antall"]["total"] for p in nac_api["partier"]}
assert all(nac["v"][k] == tot_api[k] for k in IDS), "soma dos distritos não bate com o total nacional da API"
assert sum(seats.values()) == nac_api["mandater"]["antall"]
pct_api = {p["id"]["partikode"]: p["stemmer"]["resultat"].get("prosent") for p in nac_api["partier"]}
assert all(abs(nac["v"][k] / nac["validos"] * 100 - pct_api[k]) < 0.001 for k in IDS), "percentuais diferentes dos oficiais"
print("eleitores", nac["eleitores"], "votantes", nac["votantes"], f'({nac["votantes"]/nac["eleitores"]*100:.1f}%)', "válidos", nac["validos"])
for k, nome, *_ in PART:
    print("   ", nome, nac["v"][k], f'{nac["v"][k]/nac["validos"]*100:.2f}%', seats[k])
cands = [{"id": k, "nome": nome, "grupo": f"{seats[k]} cadeiras" + (" · " + lid if lid else ""), "cor": cor} for k, nome, lid, cor in PART]
cands.append({"id": "O", "nome": "Outros", "grupo": f"{seats['O']} cadeiras", "cor": OUTRO})
P = {"pais": "NO", "nome": "Noruega", "nivel": "Distrito", "sistema": "Parlamentar", "parlamentar": True,
     "fonte": "Valgdirektoratet, resultado final da eleição do Storting de 08/09/2025 (valgresultat.no)", "fonte_url": "https://valgresultat.no/",
     "nota": "Eleição parlamentar proporcional: 169 cadeiras em 19 distritos (os antigos condados), com cadeiras de compensação nacional. Percentual sobre votos válidos (sem brancos), como o Valgdirektoratet divulga. Jonas Gahr Støre (Ap) seguiu como primeiro-ministro.",
     "eleicoes": [{"ano": 2025, "turnos": {"1": {"cand": cands, "nac": nac, "reg": reg}}}]}
os.makedirs(OUT, exist_ok=True)
json.dump(P, open(os.path.join(OUT, "no.json"), "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
