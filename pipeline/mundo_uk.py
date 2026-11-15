"""Reino Unido (House of Commons Library, eleições gerais 2019 e 2024, por nação/região) -> data/mundo/uk.json

Uso: python pipeline/mundo_uk.py psephology.db OUT_DIR
Fonte: banco oficial do Parlamento (github.com/ukparliament/psephology-datasette, electionresults.parliament.uk).
Soma os votos das 650 circunscrições por partido e por região (9 regiões inglesas + Escócia, Gales, Irlanda do Norte).
"""
import json, os, sqlite3, sys
from collections import defaultdict

DB, OUT = sys.argv[1], sys.argv[2]
OUTRO = "#5B6478"
PART = [("LAB", "Trabalhistas", "Labour", "#E0353D"), ("CON", "Conservadores", "Conservative", "#3B78EA"), ("REF", "Reform UK", "Reform UK", "#38B2C9"),
        ("LD", "Liberal-Democratas", "Liberal Democrat", "#F28C28"), ("GRN", "Verdes", "Green", "#3FAE5A"), ("SNP", "SNP", "Scottish National Party", "#E2B84B")]
LIDER = {6: {"LAB": "Keir Starmer", "CON": "Rishi Sunak", "REF": "Nigel Farage", "LD": "Ed Davey"}, 4: {"LAB": "Jeremy Corbyn", "CON": "Boris Johnson", "REF": "Nigel Farage", "LD": "Jo Swinson"}}
REG_PT = {"South East": "Sudeste", "West Midlands": "Midlands Ocidental", "North West": "Noroeste", "East Midlands": "Midlands Oriental", "London": "Londres",
          "Yorkshire and The Humber": "Yorkshire e Humber", "East of England": "Leste da Inglaterra", "South West": "Sudoeste", "North East": "Nordeste",
          "Scotland": "Escócia", "Wales": "País de Gales", "Northern Ireland": "Irlanda do Norte"}
c = sqlite3.connect(DB)
partido = {pid: nome for pid, nome in c.execute("select id, name from political_parties")}


def chave(nome):
    if not nome:
        return "O"
    if "Green" in nome:
        return "GRN"  # Inglaterra/Gales, Escócia e Irlanda do Norte
    if nome == "The Brexit Party":
        return "REF"  # o Brexit Party virou Reform UK em 2021
    for k, _, prefixo, _ in PART:
        if nome.startswith(prefixo):
            return k
    return "O"


eleicoes = []
for ge, ano in ((4, 2019), (6, 2024)):
    reg = defaultdict(lambda: {"eleitores": 0, "votantes": 0, "brancos": None, "nulos": 0, "validos": 0, "v": defaultdict(int), "assentos": defaultdict(int)})
    q = """select e.id, e.valid_vote_count, coalesce(e.invalid_vote_count,0), el.population_count,
                  coalesce(er.name, co.name) from elections e
           join constituency_groups g on g.id = e.constituency_group_id
           join constituency_areas a on a.id = g.constituency_area_id
           left join english_regions er on er.id = a.english_region_id
           join countries co on co.id = a.country_id
           left join electorates el on el.id = e.electorate_id
           where e.general_election_id = ?"""
    n_circ = 0
    for eid, val, inv, elec, rnome in c.execute(q, (ge,)).fetchall():
        n_circ += 1
        r = reg[rnome]
        r["eleitores"] += elec or 0; r["validos"] += val; r["nulos"] += inv; r["votantes"] += val + inv
        for votos, win, pid in c.execute("""select ca.vote_count, ca.is_winning_candidacy, ce.political_party_id from candidacies ca
                                            left join certifications ce on ce.candidacy_id = ca.id and ce.adjunct_to_certification_id is null
                                            where ca.election_id = ?""", (eid,)):
            k = chave(partido.get(pid))
            r["v"][k] += votos
            if win: r["assentos"][k] += 1
    out = []
    for nome in sorted(reg, key=lambda n: list(REG_PT).index(n)):
        r = reg[nome]
        out.append({"id": nome, "n": REG_PT[nome], **{x: r[x] for x in ("eleitores", "votantes", "brancos", "nulos", "validos")}, "v": dict(r["v"])})
    nac = {x: sum(r[x] for r in out) for x in ("eleitores", "votantes", "nulos", "validos")}; nac["brancos"] = None
    nac["v"] = {k: sum(r["v"].get(k, 0) for r in out) for k in [p[0] for p in PART] + ["O"]}
    assentos = defaultdict(int)
    for r in reg.values():
        for k, s in r["assentos"].items(): assentos[k] += s
    nac["assentos"] = dict(assentos)
    print(ano, n_circ, "circunscrições | eleitores", nac["eleitores"], "votantes", nac["votantes"], f'({nac["votantes"]/nac["eleitores"]*100:.1f}%)', "válidos", nac["validos"])
    assert sum(assentos.values()) == 650 and n_circ == 650
    for k, nome, _, _ in PART:
        print("   ", nome, nac["v"][k], f'{nac["v"][k]/nac["validos"]*100:.2f}%', assentos.get(k, 0), "cadeiras")
    cands = [{"id": k, "nome": ("Brexit Party" if (k == "REF" and ano == 2019) else nome), "grupo": (f"{assentos.get(k,0)} cadeiras" + (" · " + LIDER[ge][k] if k in LIDER[ge] else "")), "cor": cor} for k, nome, _, cor in PART]
    cands.append({"id": "O", "nome": "Outros", "grupo": f"{assentos.get('O',0)} cadeiras", "cor": OUTRO})
    eleicoes.append({"ano": ano, "turnos": {"1": {"cand": cands, "nac": nac, "reg": out}}})

P = {"pais": "UK", "nome": "Reino Unido", "nivel": "Região", "sistema": "Parlamentar", "parlamentar": True,
     "fonte": "House of Commons Library, resultados oficiais das 650 circunscrições (electionresults.parliament.uk)",
     "fonte_url": "https://electionresults.parliament.uk/",
     "nota": "Eleição parlamentar por voto distrital: em cada uma das 650 circunscrições vence quem tiver mais votos, por isso a fatia de cadeiras pode ser bem diferente da fatia de votos (em 2024 os trabalhistas tiveram 33,7% dos votos e 411 cadeiras). Percentual sobre votos válidos; o primeiro-ministro é o líder do partido que forma maioria.",
     "eleicoes": eleicoes}
os.makedirs(OUT, exist_ok=True)
json.dump(P, open(os.path.join(OUT, "uk.json"), "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
