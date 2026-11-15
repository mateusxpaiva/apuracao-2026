"""Chile (SERVEL, resultados provisórios por mesa) -> data/mundo/cl.json

Uso: python pipeline/mundo_cl.py RAW_DIR OUT_DIR
RAW_DIR tem as pastas descompactadas: g_* (1º turno, provisorios-generales.servel.cl)
e p_* (2º turno, provisorios.servel.cl), mais g_total/p_total com total_votacion_4.json.
"""
import json, os, sys
from collections import defaultdict

RAW, OUT = sys.argv[1], sys.argv[2]
OUTRO = "#5B6478"
COR = {"KAST": "#3B78EA", "JARA": "#E0353D", "PARISI": "#E2B84B", "KAISER": "#7C5CE0", "MATTHEI": "#38B2C9"}
REG_NOME = {  # nomes curtos e com acento
    "DE ARICA Y PARINACOTA": "Arica y Parinacota", "DE TARAPACA": "Tarapacá", "DE ANTOFAGASTA": "Antofagasta", "DE ATACAMA": "Atacama",
    "DE COQUIMBO": "Coquimbo", "DE VALPARAISO": "Valparaíso", "METROPOLITANA DE SANTIAGO": "Metropolitana", "DEL LIBERTADOR GENERAL BERNARDO O'HIGGINS": "O'Higgins",
    "DEL MAULE": "Maule", "DE ÑUBLE": "Ñuble", "DEL BIOBIO": "Biobío", "DE LA ARAUCANIA": "La Araucanía", "DE LOS RIOS": "Los Ríos",
    "DE LOS LAGOS": "Los Lagos", "DE AYSEN DEL GENERAL CARLOS IBAÑEZ DEL CAMPO": "Aysén", "DE MAGALLANES Y DE LA ANTARTICA CHILENA": "Magallanes"}


def ld(*p):
    return json.load(open(os.path.join(RAW, *p), encoding="utf-8"))


CURTO = {"KAST": "José Antonio Kast", "JARA": "Jeannette Jara", "PARISI": "Franco Parisi", "KAISER": "Johannes Kaiser", "MATTHEI": "Evelyn Matthei",
         "MAYNE-NICHOLLS": "Harold Mayne-Nicholls", "ENRIQUEZ-OMINAMI": "Marco Enríquez-Ominami", "ARTES": "Eduardo Artés"}


def nome_bonito(n):
    for k, v in CURTO.items():
        if k in n.split():
            return v
    partes = n.title().split()
    # "Jose Antonio Kast Rist" -> "José Antonio Kast"
    fix = {"Jose": "José", "Fernandez": "Fernández", "Roman": "Román", "Enriquez-Ominami": "Enríquez-Ominami", "Marco": "Marco"}
    partes = [fix.get(x, x) for x in partes]
    return " ".join(partes[:-1]) if len(partes) > 2 else " ".join(partes)


def turno(pref):
    tot = ld(pref + "_total", "total_votacion_4.json")[0]
    cands = []
    for g in tot["detalles"]:
        for c in g["candidatos"]:
            sob = next((k for k in COR if k in c["candidato"]), None)
            cands.append({"id": str(c["id"]), "nome": nome_bonito(c["candidato"]), "grupo": c["sigla_partido"], "cor": COR.get(sob, OUTRO), "_v": c["totalVotosCandidatos"]})
    cands.sort(key=lambda c: -c["_v"])
    terr = ld(pref + "_territorios", "territorios.json")
    rn = {}
    for t in terr:
        rn[t["id_region"]] = (REG_NOME.get(t["region"], t["region"].title()), t["orden_region"])
    reg = defaultdict(lambda: {"eleitores": 0, "votantes": 0, "brancos": 0, "nulos": 0, "validos": 0, "v": defaultdict(int)})

    def soma(r, m):
        r["eleitores"] += m.get("electores") or 0
        r["votantes"] += m.get("total_general") or 0
        r["brancos"] += m.get("blancos") or 0
        r["nulos"] += m.get("nulos") or 0
        for c in m["candidatos"]:
            r["v"][str(c["id_candidato"])] += c["votos"] or 0
            r["validos"] += c["votos"] or 0

    for m in ld(pref + "_nomina4", "nomina_completa_4.json"):
        soma(reg[m["id_region"]], m)
    ext = {"eleitores": 0, "votantes": 0, "brancos": 0, "nulos": 0, "validos": 0, "v": defaultdict(int)}
    for m in ld(pref + "_nomina_ext4", "nomina_completa_ext_4.json"):
        soma(ext, m)
    out = []
    for k in sorted(reg, key=lambda k: rn[k][1]):
        r = reg[k]
        out.append({"id": str(k), "n": rn[k][0], **{x: r[x] for x in ("eleitores", "votantes", "brancos", "nulos", "validos")}, "v": dict(r["v"])})
    out.append({"id": "EXT", "n": "Exterior", **{x: ext[x] for x in ("eleitores", "votantes", "brancos", "nulos", "validos")}, "v": dict(ext["v"])})
    nac = {"eleitores": 0, "votantes": 0, "brancos": 0, "nulos": 0, "validos": 0, "v": {c["id"]: 0 for c in cands}}
    for r in out:
        for x in ("eleitores", "votantes", "brancos", "nulos", "validos"):
            nac[x] += r[x]
        for c, v in r["v"].items():
            nac["v"][c] = nac["v"].get(c, 0) + v
    # conferência: o "Total Votación Nacional" do SERVEL é só o território chileno (sem o exterior)
    dom = {x: nac[x] - out[-1][x] for x in ("validos", "brancos", "nulos", "votantes")}
    print(pref, "SERVEL:", tot["votosValidos"], tot["blancos"], tot["nulos"], tot["totalVotacion"], "| mesas no país:", dom["validos"], dom["brancos"], dom["nulos"], dom["votantes"])
    assert dom["validos"] == tot["votosValidos"], "soma das mesas não bate com o total do SERVEL"
    for c in cands:
        print("   ", c["nome"], c["_v"], nac["v"][c["id"]], f'{nac["v"][c["id"]] / nac["validos"] * 100:.2f}%')
        del c["_v"]
    return {"cand": cands, "nac": nac, "reg": out}


P = {"pais": "CL", "nome": "Chile", "nivel": "Região", "sistema": "2 turnos",
     "fonte": "Servicio Electoral de Chile (SERVEL), resultados provisórios mesa a mesa",
     "fonte_url": "https://provisorios.servel.cl/",
     "nota": "Percentual sobre votos válidos (sem brancos e nulos). Soma das atas de 99,99% das mesas; o resultado proclamado pelo Tribunal Calificador de Elecciones pode diferir por poucos votos. Exterior = chilenos votando fora do país. Voto obrigatório desde 2022.",
     "eleicoes": [{"ano": 2025, "turnos": {"1": turno("g"), "2": turno("p")}}]}
os.makedirs(OUT, exist_ok=True)
json.dump(P, open(os.path.join(OUT, "cl.json"), "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
