"""Coreia do Sul (Comissão Nacional de Eleições, 21ª eleição presidencial de 03/06/2025, por província/metrópole) -> data/mundo/kr.json

Uso: python pipeline/mundo_kr.py pres21.csv OUT_DIR
Fonte: data.go.kr, conjunto "중앙선거관리위원회_대통령선거 개표결과" (arquivo de 03/06/2025, por seção de votação).
Inclui voto antecipado, voto fora do distrito e voto no exterior, que aparecem como linhas próprias em cada município.
"""
import csv, json, os, sys
from collections import defaultdict

SRC, OUT = sys.argv[1], sys.argv[2]
OUTRO = "#5B6478"
CAND = {"더불어민주당 이재명": ("LJM", "Lee Jae-myung", "Partido Democrático", "#3B78EA"), "국민의힘 김문수": ("KMS", "Kim Moon-soo", "Partido do Poder Popular", "#E0353D"),
        "개혁신당 이준석": ("LJS", "Lee Jun-seok", "Partido da Reforma", "#F28C28"), "민주노동당 권영국": ("KYG", "Kwon Young-guk", "Partido Trabalhista Democrático", "#E2B84B"),
        "무소속 송진호": ("SJH", "Song Jin-ho", "independente", OUTRO)}
SIDO = {"서울특별시": "Seul", "부산광역시": "Busan", "대구광역시": "Daegu", "인천광역시": "Incheon", "광주광역시": "Gwangju", "대전광역시": "Daejeon",
        "울산광역시": "Ulsan", "세종특별자치시": "Sejong", "경기도": "Gyeonggi", "강원특별자치도": "Gangwon", "충청북도": "Chungcheong do Norte",
        "충청남도": "Chungcheong do Sul", "전북특별자치도": "Jeolla do Norte", "전라남도": "Jeolla do Sul", "경상북도": "Gyeongsang do Norte",
        "경상남도": "Gyeongsang do Sul", "제주특별자치도": "Jeju"}
g = defaultdict(lambda: defaultdict(int))
for r in csv.DictReader(open(SRC, encoding="utf-8-sig")):
    g[r["시도명"]][r["후보자"]] += int(r["득표수"] or 0)
reg = []
for k, nome in SIDO.items():
    x = g[k]
    v = {CAND[c][0]: x[c] for c in CAND}
    val = sum(v.values())
    assert val + x["무효 투표수"] == x["투표수"], k
    reg.append({"id": k, "n": nome, "eleitores": x["선거인수"], "votantes": x["투표수"], "brancos": None, "nulos": x["무효 투표수"], "validos": val, "v": v})
nac = {f: sum(r[f] for r in reg) for f in ("eleitores", "votantes", "nulos", "validos")}; nac["brancos"] = None
nac["v"] = {c[0]: sum(r["v"][c[0]] for r in reg) for c in CAND.values()}
print("eleitores", nac["eleitores"], "votantes", nac["votantes"], f'({nac["votantes"]/nac["eleitores"]*100:.2f}%)', "válidos", nac["validos"])
for c in CAND.values():
    print("   ", c[1], nac["v"][c[0]], f'{nac["v"][c[0]]/nac["validos"]*100:.2f}%', f'{nac["v"][c[0]]/nac["votantes"]*100:.2f}% dos votantes')
P = {"pais": "KR", "nome": "Coreia do Sul", "nivel": "Província", "sistema": "Turno único",
     "fonte": "Comissão Nacional de Eleições (NEC), resultado por seção da 21ª eleição presidencial (data.go.kr)", "fonte_url": "https://www.data.go.kr/data/15025528/fileData.do",
     "nota": "Turno único: vence quem tiver mais votos. Eleição antecipada depois do impeachment de Yoon Suk-yeol. Percentual sobre votos válidos, como a NEC divulga. Voto no exterior e antecipado entram na província de registro do eleitor.",
     "eleicoes": [{"ano": 2025, "turnos": {"1": {"cand": [{"id": a, "nome": b, "grupo": c, "cor": d} for a, b, c, d in CAND.values()], "nac": nac, "reg": reg}}}]}
os.makedirs(OUT, exist_ok=True)
json.dump(P, open(os.path.join(OUT, "kr.json"), "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
