"""Nova Zelândia (Electoral Commission, eleição geral de 14/10/2023, voto partidário por distrito eleitoral) -> data/mundo/nz.json

Uso: python pipeline/mundo_nz.py OUT_DIR
Fonte: tabelas oficiais de estatísticas da Electoral Commission (archive.electionresults.govt.nz/electionresults_2023):
"Party votes and turnout by electorate" e "Votes for registered parties by electorate", transcritas em
nz_turnout_2023.txt (válidos; informais; anulados ord.; anulados esp.; total; eleitores) e nz_partidos_2023.txt.
"""
import json, os, sys

OUT = sys.argv[1]
D = os.path.dirname(os.path.abspath(__file__))
OUTRO = "#5B6478"
PART = [("NAT", "National", "48 cadeiras · Christopher Luxon", "#2E6FD8"), ("LAB", "Labour", "34 cadeiras · Chris Hipkins", "#E0353D"),
        ("GRN", "Verdes", "15 cadeiras", "#2E9E5B"), ("ACT", "ACT", "11 cadeiras · David Seymour", "#F2C12E"),
        ("NZF", "NZ First", "8 cadeiras · Winston Peters", "#C9CED6"), ("TPM", "Te Pāti Māori", "6 cadeiras", "#8B1E2E"),
        ("TOP", "Opportunity", "0 cadeiras", "#38B2C9")]
ids = [p[0] for p in PART] + ["O"]
lt = lambda f: [l.split(";") for l in open(os.path.join(D, f), encoding="utf-8").read().strip().split("\n")]
T, Pv = lt("nz_turnout_2023.txt"), lt("nz_partidos_2023.txt")
tot_t, tot_p = T.pop(), Pv.pop()
tv = {x[0]: list(map(int, x[1:])) for x in T}
out = []
for i, x in enumerate(Pv):
    n = x[0]; v = dict(zip(ids, map(int, x[1:9])))
    val, inf, d1, d2, cast, el = tv[n]
    assert sum(v.values()) == val == int(x[9]), n
    out.append({"id": f"E{i+1:02d}", "n": n + (" (Māori)" if i >= 65 else ""), "eleitores": el, "votantes": cast, "brancos": 0,
                "nulos": inf + d1 + d2, "validos": val, "v": v})
nac = {k: sum(r[k] for r in out) for k in ("eleitores", "votantes", "brancos", "nulos", "validos")}
nac["v"] = {k: sum(r["v"][k] for r in out) for k in ids}
assert [nac["v"][k] for k in ids] == list(map(int, tot_p[1:9])) and nac["validos"] == int(tot_p[9]) == 2851211
assert nac["votantes"] == int(tot_t[5]) == 2884111 and nac["eleitores"] == int(tot_t[6]) == 3688292
print("eleitores", nac["eleitores"], "votantes", nac["votantes"], f'({nac["votantes"]/nac["eleitores"]*100:.2f}%)', "válidos", nac["validos"])
for k in ids: print("   ", k, nac["v"][k], f'{nac["v"][k]/nac["validos"]*100:.2f}%')
cands = [{"id": k, "nome": n, "grupo": g, "cor": c} for k, n, g, c in PART] + [{"id": "O", "nome": "Outros", "grupo": "0 cadeiras", "cor": OUTRO}]
P = {"pais": "NZ", "nome": "Nova Zelândia", "nivel": "Distrito eleitoral", "sistema": "Parlamentar", "parlamentar": True,
     "fonte": "Electoral Commission, resultado oficial da eleição geral de 14/10/2023 (voto partidário)", "fonte_url": "https://www.electionresults.govt.nz/electionresults_2023/",
     "nota": "Sistema misto (MMP): cada eleitor dá um voto no candidato do distrito e outro no partido; o voto partidário define o tamanho das bancadas e é o mostrado aqui. 72 distritos, 7 deles reservados ao eleitorado Māori. Cadeiras do resultado oficial (122, com uma cadeira extra de sobreposição); a eleição suplementar de Port Waikato deu mais uma ao National. Nulos incluem votos informais e anulados.",
     "eleicoes": [{"ano": 2023, "turnos": {"1": {"cand": cands, "nac": nac, "reg": out}}}]}
json.dump(P, open(os.path.join(OUT, "nz.json"), "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
