"""Panamá (Tribunal Electoral, eleição presidencial de 5/5/2024, por província e comarca) -> data/mundo/pa.json

Uso: python pipeline/mundo_pa.py OUT_DIR
Fonte: Tribunal Electoral, Comisión de Estadísticas, Cuadros No. 1 e No. 2 da eleição para presidente de 2024,
publicados em datosabiertos.gob.pa e copiados em pipeline/pa/pa_c1.csv e pa_c2.csv (codificação cp850).
"""
import csv, json, os, sys

OUT = sys.argv[1]
D = os.path.join(os.path.dirname(os.path.abspath(__file__)), "pa")
OUTRO = "#5B6478"
# (coluna no Cuadro 2, id, nome, grupo, cor)
CAND = [(6, "JRM", "José Raúl Mulino", "Realizando Metas, Alianza", "#7C5CE0"),
        (14, "RL", "Ricardo Lombana", "Movimiento Otro Camino", "#38B2C9"),
        (16, "MT", "Martín Torrijos", "Partido Popular", "#2E9E5B"),
        (10, "RR", "Rómulo Roux", "Cambio Democrático, Panameñista", "#F28C28"),
        (2, "JGC", "José Gabriel Carrizo", "PRD, Molirena", "#E0353D")]
OUTROS = [18, 22, 24]  # Melitón Arrocha, Zulay Rodríguez, Maribel Gordón (livre postulação)
num = lambda s: int(s.replace(",", "").strip() or 0)
ler = lambda f: [r for r in csv.reader(open(os.path.join(D, f), encoding="cp850"), delimiter=";")]
c1 = {r[0].strip(): r for r in ler("pa_c1.csv") if r and r[0].strip() and not r[0].startswith(" ") or (r and r[0].strip() == "Total")}
c2 = [r for r in ler("pa_c2.csv") if r and r[0].strip() and not r[0].startswith(" ") and len(r) > 24 and r[1][:1].isdigit()]
reg, tot = [], None
for r in c2:
    n = r[0].strip()
    v = {cid: num(r[col]) for col, cid, *_ in CAND}
    v["O"] = sum(num(r[c]) for c in OUTROS)
    t = c1[n]
    g = {"id": "P%02d" % (len(reg) + 1), "n": n, "eleitores": num(t[5]), "votantes": num(t[6]), "brancos": num(t[13]), "nulos": num(t[15]), "validos": num(r[1]), "v": v}
    assert sum(v.values()) == g["validos"] == num(t[11]) and g["validos"] + g["brancos"] + g["nulos"] == g["votantes"], n
    if n == "Total": tot = g
    else: reg.append(g)
ids = [c[1] for c in CAND] + ["O"]
nac = {k: sum(x[k] for x in reg) for k in ("eleitores", "votantes", "brancos", "nulos", "validos")}
nac["v"] = {k: sum(x["v"][k] for x in reg) for k in ids}
assert all(nac[k] == tot[k] for k in ("eleitores", "votantes", "brancos", "nulos", "validos")) and nac["v"] == tot["v"]
assert (nac["eleitores"], nac["votantes"], nac["validos"], nac["v"]["JRM"]) == (3004083, 2332864, 2275179, 778763)
print(len(reg), "regiões", {k: f'{nac["v"][k]/nac["validos"]*100:.2f}%' for k in ids}, f'comparecimento {nac["votantes"]/nac["eleitores"]*100:.1f}%')
for x in reg:
    if x["n"] == "Voto Adelantado": x["n"] = "Voto antecipado"
cands = [{"id": cid, "nome": nm, "grupo": gr, "cor": cor} for _, cid, nm, gr, cor in CAND] + [{"id": "O", "nome": "Outros", "grupo": "3 candidaturas independentes", "cor": OUTRO}]
P = {"pais": "PA", "nome": "Panamá", "nivel": "Província e comarca", "sistema": "Turno único",
     "fonte": "Tribunal Electoral do Panamá, Cuadros 1 e 2 da eleição presidencial de 2024 (datosabiertos.gob.pa)",
     "fonte_url": "https://www.datosabiertos.gob.pa/dataset/te-elecciones-generales-presidente-2024",
     "nota": "Turno único: vence quem tiver mais votos, sem exigência de maioria. Mulino entrou na disputa como substituto de Ricardo Martinelli, impedido de concorrer, e venceu com cerca de um terço dos votos válidos. Comarcas são territórios indígenas com status de província. Voto antecipado reúne o voto no exterior e o voto antecipado.",
     "eleicoes": [{"ano": 2024, "turnos": {"1": {"cand": cands, "nac": nac, "reg": reg}}}]}
json.dump(P, open(os.path.join(OUT, "pa.json"), "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
