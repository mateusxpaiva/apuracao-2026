"""Austrália (AEC, eleição federal de 03/05/2025, Câmara dos Representantes, por estado/território) -> data/mundo/au.json

Uso: python pipeline/mundo_au.py PASTA OUT_DIR
PASTA tem os CSVs da AEC (results.aec.gov.au/31496): HouseFirstPrefsByStateByPartyDownload, HouseTppByStateDownload,
HouseTurnoutByStateDownload e HouseMembersElectedDownload.
Etapa 1 = primeiras preferências por partido. Etapa 2 = preferência final entre os dois blocos (two-party preferred).
"""
import csv, json, os, sys
from collections import Counter, defaultdict

D, OUT = sys.argv[1], sys.argv[2]
OUTRO = "#5B6478"
EST = {"NSW": "Nova Gales do Sul", "VIC": "Vitória", "QLD": "Queensland", "WA": "Austrália Ocidental", "SA": "Austrália Meridional",
       "TAS": "Tasmânia", "ACT": "Território da Capital", "NT": "Território do Norte"}
COAL = {"LP", "LNP", "NP", "CLP", "LNQ"}
PART = [("ALP", "Trabalhistas", "Anthony Albanese", "#E0353D"), ("COAL", "Coalizão Liberal-Nacional", "Peter Dutton", "#3B78EA"),
        ("GRN", "Verdes", "", "#3FAE5A"), ("ON", "One Nation", "Pauline Hanson", "#F28C28"), ("IND", "Independentes", "", "#38B2C9")]
ler = lambda f: list(csv.reader(open(os.path.join(D, f), encoding="utf-8-sig")))[2:]
fp = ler("fp_state_party.csv"); tpp = ler("tpp_state.csv"); tur = {r[0]: r for r in ler("turnout_state.csv")}
eleitos = Counter()
for r in ler("elected.csv"):
    ab = r[7]; eleitos["COAL" if ab in COAL else ab if ab in ("ALP", "GRN", "ON", "IND") else "O"] += 1
reg1, reg2 = {}, {}
v = defaultdict(lambda: defaultdict(int))
for r in fp:
    ab = r[1]; k = "COAL" if ab in COAL else ab if ab in ("ALP", "GRN", "ON", "IND") else "O"
    v[r[0]][k] += int(r[17])
for e in EST:
    t = tur[e]; ele, vot = int(t[2]), int(t[3]); val = sum(v[e].values())
    reg1[e] = {"id": e, "n": EST[e], "eleitores": ele, "votantes": vot, "brancos": None, "nulos": vot - val, "validos": val, "v": dict(v[e])}
for r in tpp:
    e = r[0]; a, c = int(r[2]), int(r[4]); vot = int(tur[e][3])
    reg2[e] = {"id": e, "n": EST[e], "eleitores": int(tur[e][2]), "votantes": vot, "brancos": None, "nulos": vot - a - c, "validos": a + c, "v": {"ALP": a, "COAL": c}}


def nac(reg, ids):
    n = {x: sum(r[x] for r in reg) for x in ("eleitores", "votantes", "nulos", "validos")}; n["brancos"] = None
    n["v"] = {k: sum(r["v"].get(k, 0) for r in reg) for k in ids}
    return n


ids = [p[0] for p in PART] + ["O"]
n1 = nac(list(reg1.values()), ids); n2 = nac(list(reg2.values()), ["ALP", "COAL"])
print("eleitores", n1["eleitores"], "votantes", n1["votantes"], f'({n1["votantes"]/n1["eleitores"]*100:.2f}%)', "formais", n1["validos"])
for k in ids:
    print("   1ª pref", k, n1["v"][k], f'{n1["v"][k]/n1["validos"]*100:.2f}%', eleitos.get(k, 0), "cadeiras")
print("   TPP", n2["v"], {k: f'{x/n2["validos"]*100:.2f}%' for k, x in n2["v"].items()}, "total cadeiras", sum(eleitos.values()))
c1 = [{"id": k, "nome": nome, "grupo": f"{eleitos.get(k,0)} cadeiras" + (" · " + lid if lid else ""), "cor": cor} for k, nome, lid, cor in PART]
c1.append({"id": "O", "nome": "Outros", "grupo": f"{eleitos.get('O',0)} cadeiras", "cor": OUTRO})
c2 = [x for x in c1 if x["id"] in ("ALP", "COAL")]
P = {"pais": "AU", "nome": "Austrália", "nivel": "Estado", "sistema": "Parlamentar", "parlamentar": True,
     "etapas": {"1": "1ª preferência", "2": "Preferência final"},
     "fonte": "Australian Electoral Commission, resultados finais da Câmara dos Representantes (03/05/2025)", "fonte_url": "https://results.aec.gov.au/31496/Website/HouseDownloadsMenu-31496-Csv.htm",
     "nota": "Voto preferencial e obrigatório: o eleitor ordena todos os candidatos do distrito. A 1ª preferência mostra a força de cada partido; a preferência final (two-party preferred) redistribui os votos até sobrarem trabalhistas e coalizão. Nulos = votos informais. 150 cadeiras.",
     "eleicoes": [{"ano": 2025, "turnos": {"1": {"cand": c1, "nac": n1, "reg": list(reg1.values())}, "2": {"cand": c2, "nac": n2, "reg": list(reg2.values())}}}]}
os.makedirs(OUT, exist_ok=True)
json.dump(P, open(os.path.join(OUT, "au.json"), "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
