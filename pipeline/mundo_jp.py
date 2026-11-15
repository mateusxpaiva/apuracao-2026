"""Japão (Ministério de Assuntos Internos, eleição da Câmara dos Representantes de 08/02/2026, voto proporcional por província) -> data/mundo/jp.json

Uso: python pipeline/mundo_jp.py PASTA OUT_DIR
PASTA tem os arquivos do MIC (soumu.go.jp/senkyo/senkyo_s/data/shugiin51/): 001061481 (votos por partido e província,
proporcional), 001061483 (votantes, válidos e inválidos) e 001061473 (eleitores).
"""
import json, os, sys, openpyxl
from collections import defaultdict

D, OUT = sys.argv[1], sys.argv[2]
OUTRO = "#5B6478"
PART = {"自由民主党": ("LDP", "Partido Liberal Democrata", "Sanae Takaichi", "#3FAE5A"), "中道改革連合": ("CRA", "Aliança Reformista de Centro", "", "#3B78EA"),
        "国民民主党": ("DPFP", "Partido Democrata para o Povo", "", "#F28C28"), "日本維新の会": ("ISHIN", "Partido da Inovação", "", "#38B2C9"),
        "参政党": ("SANSEI", "Sanseitō", "", "#E2B84B"), "チームみらい": ("MIRAI", "Team Mirai", "", "#B5179E"), "日本共産党": ("JCP", "Partido Comunista", "", "#E0353D")}
PREF = "北海道 青森県 岩手県 宮城県 秋田県 山形県 福島県 茨城県 栃木県 群馬県 埼玉県 千葉県 東京都 神奈川県 新潟県 富山県 石川県 福井県 山梨県 長野県 岐阜県 静岡県 愛知県 三重県 滋賀県 京都府 大阪府 兵庫県 奈良県 和歌山県 鳥取県 島根県 岡山県 広島県 山口県 徳島県 香川県 愛媛県 高知県 福岡県 佐賀県 長崎県 熊本県 大分県 宮崎県 鹿児島県 沖縄県".split()
ROM = "Hokkaido Aomori Iwate Miyagi Akita Yamagata Fukushima Ibaraki Tochigi Gunma Saitama Chiba Tóquio Kanagawa Niigata Toyama Ishikawa Fukui Yamanashi Nagano Gifu Shizuoka Aichi Mie Shiga Quioto Osaka Hyogo Nara Wakayama Tottori Shimane Okayama Hiroshima Yamaguchi Tokushima Kagawa Ehime Kochi Fukuoka Saga Nagasaki Kumamoto Oita Miyazaki Kagoshima Okinawa".split()
rows = lambda f, i=0: list(openpyxl.load_workbook(os.path.join(D, f), read_only=True, data_only=True).worksheets[i].iter_rows(values_only=True))
v = defaultdict(lambda: defaultdict(int)); total_part = defaultdict(int); cab = None
for r in rows("pr_pref_party.xlsx"):
    if r[1] == "都道府県":
        cab = r; continue
    if cab and r[1] in PREF:
        for i in range(2, len(r)):
            if cab[i] and cab[i] != "合計" and isinstance(r[i], (int, float)):
                v[r[1]][PART[cab[i]][0] if cab[i] in PART else "O"] += int(r[i])
    if cab and r[1] == "合計":
        for i in range(2, len(r)):
            if cab[i] and cab[i] != "合計" and isinstance(r[i], (int, float)):
                total_part[PART[cab[i]][0] if cab[i] in PART else "O"] += int(r[i])
tot = {r[1]: r for r in rows("pr_totais.xlsx") if r[1] in PREF}
ele = {r[1]: r for r in rows("pr_eleitores.xlsx") if r[1] in PREF}
reg = []
for p, nome in zip(PREF, ROM):
    val = sum(v[p].values())
    assert val == int(tot[p][3]), (p, val, tot[p][3])
    reg.append({"id": p, "n": nome, "eleitores": int(ele[p][4]), "votantes": int(tot[p][2]), "brancos": None, "nulos": int(tot[p][4]), "validos": val, "v": dict(v[p])})
ids = [x[0] for x in PART.values()] + ["O"]
nac = {x: sum(r[x] for r in reg) for x in ("eleitores", "votantes", "nulos", "validos")}; nac["brancos"] = None
nac["v"] = {k: sum(r["v"].get(k, 0) for r in reg) for k in ids}
assert all(nac["v"][k] == total_part[k] for k in ids), "províncias não somam o total"
print("eleitores", nac["eleitores"], "votantes", nac["votantes"], f'({nac["votantes"]/nac["eleitores"]*100:.2f}%)', "válidos", nac["validos"])
for k in ids:
    print("   ", k, nac["v"][k], f'{nac["v"][k]/nac["validos"]*100:.2f}%')
cands = [{"id": k, "nome": nome, "grupo": lid, "cor": cor} for k, nome, lid, cor in PART.values()] + [{"id": "O", "nome": "Outros", "grupo": "", "cor": OUTRO}]
P = {"pais": "JP", "nome": "Japão", "nivel": "Província", "sistema": "Parlamentar", "parlamentar": True,
     "fonte": "Ministério de Assuntos Internos e Comunicações (MIC), resultados da eleição geral de 08/02/2026", "fonte_url": "https://www.soumu.go.jp/senkyo/senkyo_s/data/shugiin51/index.html",
     "nota": "Eleição parlamentar mista: 289 cadeiras distritais e 176 proporcionais. Aqui, o voto proporcional por partido somado por província (as 11 regiões proporcionais agrupam várias províncias). Percentual sobre votos válidos. O MIC publica estes números como resultado de apuração (速報).",
     "eleicoes": [{"ano": 2026, "turnos": {"1": {"cand": cands, "nac": nac, "reg": reg}}}]}
os.makedirs(OUT, exist_ok=True)
json.dump(P, open(os.path.join(OUT, "jp.json"), "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
