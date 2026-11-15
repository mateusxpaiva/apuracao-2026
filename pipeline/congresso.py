"""Congresso Nacional -> data/congresso/{camara,senado,gastos}.json (roda todo dia no GitHub Actions).

Fontes: Dados Abertos da Câmara (arquivos anuais de votações, votos, objetos e orientações;
API de deputados; cota parlamentar) e Dados Abertos do Senado (votações nominais).
"""
import csv, datetime as dt, io, json, os, re, sys, urllib.request, zipfile
from collections import Counter, defaultdict

RAIZ = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
OUT = os.path.join(RAIZ, "data", "congresso")
UA = {"User-Agent": "Mozilla/5.0 (apuracao-por-ia; dados abertos)", "Accept": "application/json"}
CAM = "https://dadosabertos.camara.leg.br"
PRINCIPAIS = ("PEC", "PLP", "PL", "MPV", "PDL", "PLV", "PRC")


def get(url, timeout=300, tent=4):
    for i in range(tent):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=timeout) as r:
                return r.read()
        except Exception as e:
            print("  tentativa", i + 1, "falhou:", url, e, flush=True)
    raise RuntimeError("não baixou " + url)


def gj(url):
    return json.loads(get(url))


def voto_cod(v):
    v = (v or "").strip().lower()
    return {"sim": "S", "não": "N", "nao": "N", "abstenção": "A", "abstencao": "A", "obstrução": "O", "obstrucao": "O", "artigo 17": "P"}.get(v, "O")


TIPOS = [("Proposta de Emenda à Constituição", "PEC"), ("Projeto de Lei Complementar", "PLP"), ("Projeto de Lei de Conversão", "PLV"),
         ("Projeto de Decreto Legislativo", "PDL"), ("Projeto de Resolução", "PRC"), ("Medida Provisória", "MPV"), ("Projeto de Lei", "PL")]


def titulo_desc(desc):
    for nome, sg in TIPOS:
        m = re.search(nome + r"\s+n[ºo°]\s*([\d.]+)\s*,?\s*(?:de\s*)?(\d{4})", desc or "")
        if m:
            return f"{sg} {m.group(1).replace('.', '')}/{m.group(2)}"
    return ""


def camara(ano):
    deps = gj(f"{CAM}/api/v2/deputados?itens=1000&ordem=ASC&ordenarPor=nome")["dados"]
    D = {str(d["id"]): [d["nome"], d["siglaPartido"], d["siglaUf"]] for d in deps}
    vot = gj(f"{CAM}/arquivos/votacoes/json/votacoes-{ano}.json")["dados"]
    votos = gj(f"{CAM}/arquivos/votacoesVotos/json/votacoesVotos-{ano}.json")["dados"]
    obj = gj(f"{CAM}/arquivos/votacoesObjetos/json/votacoesObjetos-{ano}.json")["dados"]
    ori = gj(f"{CAM}/arquivos/votacoesOrientacoes/json/votacoesOrientacoes-{ano}.json")["dados"]
    porV = defaultdict(dict)
    for v in votos:
        dp = v.get("deputado_") or {}
        did = str(dp.get("id"))
        porV[v["idVotacao"]][did] = voto_cod(v.get("voto"))
        if did not in D and dp.get("nome"):
            D[did] = [dp["nome"], dp.get("siglaPartido", ""), dp.get("siglaUf", "")]
    objs = defaultdict(list)
    for o in obj:
        p = o.get("proposicao_") or {}
        objs[o["idVotacao"]].append(p)
    orient = defaultdict(dict)
    for o in ori:
        if o.get("orientacao"):
            orient[o["idVotacao"]][o["siglaBancada"]] = o["orientacao"]
    lista, PROPS = [], {}
    for v in vot:
        if v.get("siglaOrgao") != "PLEN" or v["id"] not in porV:
            continue
        pid = v["id"].split("-")[0]
        if pid not in PROPS:
            try:
                q = gj(f"{CAM}/api/v2/proposicoes/{pid}")["dados"]
                PROPS[pid] = {"siglaTipo": q.get("siglaTipo"), "numero": q.get("numero"), "ano": q.get("ano"), "ementa": q.get("ementa"), "id": q.get("id")}
            except Exception:
                PROPS[pid] = next((p for p in objs.get(v["id"], []) if p.get("siglaTipo") in PRINCIPAIS), {})
        prin = PROPS[pid]
        vv = porV[v["id"]]
        cont = Counter(vv.values())
        og = orient[v["id"]]
        lista.append({
            "id": v["id"], "data": v.get("dataHoraRegistro") or v.get("data"),
            "desc": v.get("descricao", ""), "aprovada": v.get("aprovacao") == 1,
            "titulo": (f'{prin["siglaTipo"]} {prin.get("numero", "")}/{prin.get("ano", "")}' if prin.get("siglaTipo") else "") or titulo_desc(v.get("descricao")),
            "sobre": titulo_desc(v.get("descricao")),
            "ementa": (prin.get("ementa") or "")[:600], "idProp": prin.get("id"),
            "sim": cont["S"], "nao": cont["N"], "abst": cont["A"], "outros": cont["O"] + cont["P"],
            "gov": og.get("Governo", ""), "opo": og.get("Oposição", ""),
            "orient": {k: og[k] for k in og if not k.startswith("Bl ")},
            "votos": {c: [d for d, x in vv.items() if x == c] for c in "SNAO" if any(x == c for x in vv.values())},
        })
    lista.sort(key=lambda x: x["data"], reverse=True)
    # perfil de cada deputado: presença e alinhamento com o governo
    stat = defaultdict(lambda: [0, 0, 0])  # [votações em que votou, votos com orientação do governo, votos iguais ao governo]
    for v in lista:
        g = {"Sim": "S", "Não": "N"}.get(v["gov"])
        for c, ids in v["votos"].items():
            for d in ids:
                s = stat[d]; s[0] += 1
                if g and c in "SN":
                    s[1] += 1; s[2] += c == g
    perfil = {d: [stat[d][0], stat[d][1], stat[d][2]] for d in D}
    return {"ano": ano, "atualizado": dt.datetime.utcnow().strftime("%Y-%m-%dT%H:%MZ"), "total": len(lista),
            "deputados": D, "atuais": [str(d["id"]) for d in deps], "perfil": perfil, "votacoes": lista}


def gastos(ano):
    raw = get(f"https://www.camara.leg.br/cotas/Ano-{ano}.csv.zip", timeout=600)
    z = zipfile.ZipFile(io.BytesIO(raw))
    nome = [n for n in z.namelist() if n.endswith(".csv")][0]
    dep = defaultdict(lambda: {"t": 0.0, "cat": Counter(), "forn": Counter(), "n": 0})
    cat, mes = Counter(), Counter()
    info = {}
    with z.open(nome) as f:
        for r in csv.DictReader(io.TextIOWrapper(f, encoding="utf-8-sig", newline=""), delimiter=";"):
            did = (r.get("ideCadastro") or "").strip()
            if not did:
                continue  # lideranças de partido
            try:
                v = float((r.get("vlrLiquido") or "0").replace(",", "."))
            except ValueError:
                continue
            c = (r.get("txtDescricao") or "").strip().capitalize()
            d = dep[did]; d["t"] += v; d["cat"][c] += v; d["n"] += 1
            d["forn"][(r.get("txtFornecedor") or "").strip().title()[:60]] += v
            cat[c] += v; mes[int(r.get("numMes") or 0)] += v
            info[did] = [(r.get("txNomeParlamentar") or r.get("txtNomeParlamentar") or "").title(), r.get("sgPartido", ""), r.get("sgUF", "")]
    deps = sorted(({"id": k, "nome": info[k][0], "partido": info[k][1], "uf": info[k][2], "total": round(v["t"], 2), "docs": v["n"],
                    "cat": [[c, round(x, 2)] for c, x in v["cat"].most_common(4)],
                    "forn": [[c, round(x, 2)] for c, x in v["forn"].most_common(3)]} for k, v in dep.items()), key=lambda x: -x["total"])
    return {"ano": ano, "atualizado": dt.datetime.utcnow().strftime("%Y-%m-%dT%H:%MZ"), "total": round(sum(cat.values()), 2),
            "categorias": [[c, round(x, 2)] for c, x in cat.most_common()], "mes": {str(k): round(v, 2) for k, v in sorted(mes.items()) if k},
            "deputados": deps}


def senado(dias=120):
    fim = dt.date.today(); ini = fim - dt.timedelta(days=dias)
    L = gj(f"https://legis.senado.leg.br/dadosabertos/votacao?dataInicio={ini}&dataFim={fim}")
    S, lista = {}, []
    for v in L:
        votos = defaultdict(list)
        for p in v.get("votos") or []:
            cid = str(p.get("codigoParlamentar"))
            S[cid] = [p.get("nomeParlamentar"), p.get("siglaPartidoParlamentar"), p.get("siglaUFParlamentar")]
            votos[voto_cod(p.get("siglaVotoParlamentar"))].append(cid)
        lista.append({"id": str(v.get("codigoSessaoVotacao")), "data": v.get("dataSessao"), "titulo": v.get("identificacao") or "",
                      "desc": v.get("descricaoVotacao") or "", "ementa": (v.get("ementa") or "")[:600],
                      "aprovada": v.get("resultadoVotacao") == "A", "secreta": v.get("votacaoSecreta") == "S",
                      "sim": len(votos["S"]), "nao": len(votos["N"]), "abst": len(votos["A"]), "outros": len(votos["O"]) + len(votos["P"]),
                      "votos": {k: x for k, x in votos.items() if k in "SNAO"}})
    lista.sort(key=lambda x: x["data"] or "", reverse=True)
    return {"atualizado": dt.datetime.utcnow().strftime("%Y-%m-%dT%H:%MZ"), "senadores": S, "votacoes": lista}


if __name__ == "__main__":
    ano = int(sys.argv[1]) if len(sys.argv) > 1 else dt.date.today().year
    os.makedirs(OUT, exist_ok=True)
    for nome, fn in (("camara", lambda: camara(ano)), ("gastos", lambda: gastos(ano)), ("senado", senado)):
        try:
            d = fn()
            with open(os.path.join(OUT, f"{nome}.json"), "w", encoding="utf-8") as f:
                json.dump(d, f, ensure_ascii=False, separators=(",", ":"))
            print(nome, "ok", {k: (len(v) if isinstance(v, (list, dict)) else v) for k, v in d.items() if k in ("total", "votacoes", "deputados", "senadores")}, flush=True)
        except Exception as e:
            print(nome, "FALHOU:", e, flush=True)
