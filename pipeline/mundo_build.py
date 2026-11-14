"""Monta data/mundo/{pais}.json num formato único a partir das fontes oficiais baixadas.

Formato de cada país:
{ "pais","nome","nivel","fonte","nota",
  "eleicoes":[{"ano":2023,"turnos":{"1":T,"2":T}}] }
T = {"cand":[{"id","nome","grupo","cor"}],
     "nac":{"eleitores","votantes","brancos","nulos","validos","v":{id:votos}},
     "reg":[{"id","n","eleitores","votantes","brancos","nulos","validos","v":{id:votos}}]}
"validos" é a base oficial do percentual em cada país.
"""
import csv, io, json, os, re, sys, openpyxl

RAW, OUT = sys.argv[1], sys.argv[2]
os.makedirs(OUT, exist_ok=True)
OUTRO = "#5B6478"

def soma_nac(reg, cands):
    nac = {"eleitores": 0, "votantes": 0, "brancos": 0, "nulos": 0, "validos": 0, "v": {c["id"]: 0 for c in cands}}
    for r in reg:
        for k in ("eleitores", "votantes", "brancos", "nulos", "validos"):
            if r.get(k) is None: nac[k] = None
            elif nac[k] is not None: nac[k] += r[k]
        for c, v in r["v"].items(): nac["v"][c] = nac["v"].get(c, 0) + v
    return nac

def turno(cands, reg):
    return {"cand": cands, "nac": soma_nac(reg, cands), "reg": reg}

# ---------------- Argentina (DINE, provisórios) ----------------
AR_PROV = {"1":"Ciudad de Buenos Aires","2":"Buenos Aires","3":"Catamarca","4":"Córdoba","5":"Corrientes","6":"Chaco","7":"Chubut","8":"Entre Ríos","9":"Formosa","10":"Jujuy","11":"La Pampa","12":"La Rioja","13":"Mendoza","14":"Misiones","15":"Neuquén","16":"Río Negro","17":"Salta","18":"San Juan","19":"San Luis","20":"Santa Cruz","21":"Santa Fe","22":"Santiago del Estero","23":"Tucumán","24":"Tierra del Fuego"}
AR_CAND = {  # agrupação -> (candidato, cor)
 "FRENTE PARA LA VICTORIA": ("Daniel Scioli", "#2FA3E0"), "CAMBIEMOS": ("Mauricio Macri", "#F2C230"),
 "UNIDOS POR UNA NUEVA ALTERNATIVA": ("Sergio Massa", "#7FB069"), "FRENTE DE IZQUIERDA": ("Nicolás del Caño", OUTRO),
 "PROGRESISTAS": ("Margarita Stolbizer", OUTRO), "COMPROMISO FEDERAL": ("Adolfo Rodríguez Saá", OUTRO),
 "FRENTE DE TODOS": ("Alberto Fernández", "#2FA3E0"), "JUNTOS POR EL CAMBIO": None,
 "CONSENSO FEDERAL": ("Roberto Lavagna", OUTRO), "FRENTE NOS": ("Juan José Gómez Centurión", OUTRO),
 "UNITE POR LA LIBERTAD": ("José Luis Espert", OUTRO),
 "UNION POR LA PATRIA": ("Sergio Massa", "#2FA3E0"), "LA LIBERTAD AVANZA": ("Javier Milei", "#8B5CF6"),
 "HACEMOS POR NUESTRO PAIS": ("Juan Schiaretti", OUTRO),
}
def ar_cand(ano, nome):
    n = nome.upper().replace("ALIANZA ", "").strip()
    if n.startswith("JUNTOS POR EL CAMBIO"):
        return ("Mauricio Macri", "#F2C230") if ano == "2019" else ("Patricia Bullrich", "#F2C230")
    if n.startswith("FRENTE DE IZQUIERDA"):
        return ("Myriam Bregman", OUTRO) if ano == "2023" else ("Nicolás del Caño", OUTRO)
    for k, v in AR_CAND.items():
        if v and n.startswith(k): return v
    return (nome.title(), OUTRO)

def argentina():
    B = json.load(open(os.path.join(RAW, "ar_bruto.json")))
    el = []
    for ano in sorted(B):
        tt = {}
        for t, P in sorted(B[ano].items()):
            nomes, tot = {}, {}
            for d in P.values():
                for a, v in d["ag"].items(): tot[a] = tot.get(a, 0) + v; nomes[a] = d["agn"][a]
            ordem = sorted(tot, key=lambda a: -tot[a])
            cands = []
            for a in ordem:
                nm, cor = ar_cand(ano, nomes[a])
                cands.append({"id": a, "nome": nm, "grupo": nomes[a].title().replace("Alianza ", ""), "cor": cor})
            reg = []
            for did, d in sorted(P.items(), key=lambda x: int(x[0])):
                tp = d["tipos"]; vot = sum(tp.values())
                reg.append({"id": did, "n": AR_PROV[did], "eleitores": d["electores"], "votantes": vot,
                            "brancos": tp.get("EN BLANCO", 0), "nulos": tp.get("NULO", 0),
                            "validos": tp.get("POSITIVO", 0), "v": {a: d["ag"].get(a, 0) for a in ordem}})
            tt[t] = turno(cands, reg)
        el.append({"ano": int(ano), "turnos": tt})
    return {"pais": "AR", "nome": "Argentina", "nivel": "Província", "sistema": "2 turnos",
            "fonte": "Dirección Nacional Electoral (DINE), resultados provisórios por mesa, somados por província",
            "fonte_url": "https://datos.gob.ar/dataset?tags=elecciones",
            "nota": "Percentual sobre votos positivos (sem brancos), como manda a lei argentina. Números provisórios: o escrutínio definitivo da Justiça Eleitoral difere em menos de 0,1 ponto. Em 2019 não houve 2º turno.",
            "eleicoes": el}

# ---------------- França (Ministère de l'Intérieur) ----------------
FR_COR = {"MACRON": "#E3B505", "LE PEN": "#1F3A93", "HOLLANDE": "#E8508F", "SARKOZY": "#2E6BE6",
          "MÉLENCHON": "#C9462C", "MELENCHON": "#C9462C", "FILLON": "#2E6BE6", "BAYROU": "#F08A24", "ZEMMOUR": "#6B4A2E", "PÉCRESSE": "#2E6BE6"}
def fr_num(x):
    if x is None or x == "": return 0
    return int(float(str(x).replace("\xa0", "").replace(" ", "").replace(",", ".")))

def fr_linhas_txt(path):
    txt = open(path, encoding="latin-1").read().splitlines()
    h = txt[0].split(";")
    return h, [l.split(";") for l in txt[1:] if l.strip()]

def fr_reg_from_rows(rows, base, step, i_ins, i_vot, i_bl, i_nul, i_exp, i_blnul=None):
    """rows: lista de listas; base = índice do 1º 'Sexe' do 1º candidato; step = colunas por candidato."""
    reg, cands = [], {}
    for r in rows:
        if not r or r[0] in (None, "") or str(r[1]).strip() == "": continue
        v = {}
        j = base
        while j + 3 < len(r) and r[j + 1] not in (None, ""):
            nome = f"{str(r[j + 2]).strip().title()} {str(r[j + 1]).strip().title()}"
            key = str(r[j + 1]).strip().upper()
            cands.setdefault(key, nome)
            v[key] = fr_num(r[j + 3])
            j += step
        bl = fr_num(r[i_bl]) if i_bl is not None else None
        nu = fr_num(r[i_nul]) if i_nul is not None else None
        if i_blnul is not None: bl, nu = None, fr_num(r[i_blnul])
        code = str(r[0]).strip()
        if code.endswith(".0"): code = code[:-2]
        reg.append({"id": code, "n": str(r[1]).strip().title(), "eleitores": fr_num(r[i_ins]), "votantes": fr_num(r[i_vot]),
                    "brancos": bl, "nulos": nu, "validos": fr_num(r[i_exp]), "v": v})
    tot = {}
    for x in reg:
        for k, n in x["v"].items(): tot[k] = tot.get(k, 0) + n
    ordem = sorted(tot, key=lambda k: -tot[k])
    cl = [{"id": k, "nome": cands[k], "grupo": "", "cor": FR_COR.get(k, OUTRO)} for k in ordem]
    return turno(cl, reg)

def fr_xlsx_rows(path, sheet):
    ws = openpyxl.load_workbook(path, read_only=True)[sheet]
    rows = list(ws.iter_rows(values_only=True))
    hi = next(i for i, r in enumerate(rows) if r and r[0] and str(r[0]).startswith("Code"))
    return rows[hi], [list(r) for r in rows[hi + 1:]]

def franca(xlsdir):
    el = []
    # 2012: Départements T1/T2 (brancos e nulos juntos)
    t = {}
    for k in ("1", "2"):
        h, rows = fr_xlsx_rows(os.path.join(xlsdir, "2012_b.xlsx"), f"Départements T{k}")
        t[k] = fr_reg_from_rows(rows, h.index("Sexe"), 6, h.index("Inscrits"), h.index("Votants"), None, None, h.index("Exprimés"), i_blnul=7)
    el.append({"ano": 2012, "turnos": t})
    t = {}
    for k in ("1", "2"):
        h, rows = fr_xlsx_rows(os.path.join(xlsdir, f"2017_t{k}.xlsx"), f"Départements Tour {k}")
        t[k] = fr_reg_from_rows(rows, h.index("Sexe"), 6, h.index("Inscrits"), h.index("Votants"), h.index("Blancs"), h.index("Nuls"), h.index("Exprimés"))
    el.append({"ano": 2017, "turnos": t})
    t = {}
    for k in ("1", "2"):
        h, rows = fr_linhas_txt(os.path.join(RAW, "fr", f"2022_t{k}_dpt.txt"))
        hs = [x.strip() for x in h]
        base = hs.index("Sexe") if "N°Panneau" not in hs else hs.index("N°Panneau")
        step = 6 if "N°Panneau" not in hs else 7
        rows2 = []
        for r in rows:
            if step == 7:  # remove N°Panneau para cair no mesmo formato
                rr = r[:base]; j = base
                while j < len(r):
                    rr += r[j + 1:j + 7]; j += 7
                rows2.append(rr)
            else: rows2.append(r)
        t[k] = fr_reg_from_rows(rows2, base, 6, hs.index("Inscrits"), hs.index("Votants"), hs.index("Blancs"), hs.index("Nuls"), hs.index("Exprimés"))
    el.append({"ano": 2022, "turnos": t})
    return {"pais": "FR", "nome": "França", "nivel": "Departamento", "sistema": "2 turnos",
            "fonte": "Ministère de l'Intérieur, resultados definitivos por departamento (data.gouv.fr)",
            "fonte_url": "https://www.data.gouv.fr/",
            "nota": "Percentual sobre votos expressos (sem brancos e nulos). Inclui departamentos de ultramar e franceses no exterior. Em 2012 o ministério publicou brancos e nulos somados.",
            "eleicoes": el}

# ---------------- Estados Unidos (FEC) ----------------
US_NOME = {"AL":"Alabama","AK":"Alasca","AZ":"Arizona","AR":"Arkansas","CA":"Califórnia","CO":"Colorado","CT":"Connecticut","DE":"Delaware","DC":"Distrito de Colúmbia","FL":"Flórida","GA":"Geórgia","HI":"Havaí","ID":"Idaho","IL":"Illinois","IN":"Indiana","IA":"Iowa","KS":"Kansas","KY":"Kentucky","LA":"Luisiana","ME":"Maine","MD":"Maryland","MA":"Massachusetts","MI":"Michigan","MN":"Minnesota","MS":"Mississippi","MO":"Missouri","MT":"Montana","NE":"Nebraska","NV":"Nevada","NH":"Nova Hampshire","NJ":"Nova Jersey","NM":"Novo México","NY":"Nova York","NC":"Carolina do Norte","ND":"Dakota do Norte","OH":"Ohio","OK":"Oklahoma","OR":"Oregon","PA":"Pensilvânia","RI":"Rhode Island","SC":"Carolina do Sul","SD":"Dakota do Sul","TN":"Tennessee","TX":"Texas","UT":"Utah","VT":"Vermont","VA":"Virgínia","WA":"Washington","WV":"Virgínia Ocidental","WI":"Wisconsin","WY":"Wyoming"}
R_COR, D_COR = "#E0353D", "#3B78EA"
def ni(x):
    d = re.sub(r"[^0-9]", "", str(x or ""))
    return int(d) if d else 0
def eua():
    el = []
    for ano, (dem, rep) in {2016: ("Hillary Clinton", "Donald Trump"), 2020: ("Joe Biden", "Donald Trump")}.items():
        wb = openpyxl.load_workbook(os.path.join(RAW, "us", f"fec_{ano}.xlsx"), read_only=True)
        sn = [s for s in wb.sheetnames if "Electoral" in s and "Pop" in s][0]
        rows = list(wb[sn].iter_rows(values_only=True))
        hi = next(i for i, r in enumerate(rows) if r and r[0] == "STATE")
        sub = rows[hi + 1]
        cols = {}
        for j, x in enumerate(sub):
            if not x: continue
            tipo = rows[hi][j] if rows[hi][j] else rows[hi][j - 1]
            cols[(str(tipo).strip(), str(x).strip())] = j
        def col(tipo, pref):
            return next(j for (tp, x), j in cols.items() if tp.startswith(tipo) and x.upper().startswith(pref))
        jD, jR = col("POPULAR", "BIDEN" if ano == 2020 else "CLINTON"), col("POPULAR", "TRUNP" if ano == 2020 else "TRUMP")
        jO, jT = col("POPULAR", "ALL"), col("POPULAR", "TOTAL")
        eD, eR = col("ELECTORAL", "BIDEN" if ano == 2020 else "CLINTON"), col("ELECTORAL", "TRUNP" if ano == 2020 else "TRUMP")
        reg = []
        for r in rows[hi + 2:]:
            if not r or not r[0] or str(r[0]).strip().rstrip("*") not in US_NOME: continue
            st = str(r[0]).strip().rstrip("*")
            reg.append({"id": st, "n": US_NOME[st], "eleitores": None, "votantes": None, "brancos": None, "nulos": None,
                        "validos": ni(r[jT]), "v": {"D": ni(r[jD]), "R": ni(r[jR]), "O": ni(r[jO])},
                        "ev": {"D": ni(r[eD]), "R": ni(r[eR])}})
        cands = [{"id": "R", "nome": rep, "grupo": "Republicano", "cor": R_COR}, {"id": "D", "nome": dem, "grupo": "Democrata", "cor": D_COR}, {"id": "O", "nome": "Outros", "grupo": "", "cor": OUTRO}]
        T = turno(cands, reg); T["nac"]["ev"] = {k: sum(x["ev"][k] for x in reg) for k in ("D", "R")}
        el.append({"ano": ano, "turnos": {"1": T}})
    ws = openpyxl.load_workbook(os.path.join(RAW, "us", "fec_2024.xlsx"), read_only=True).active
    rows = list(ws.iter_rows(values_only=True)); h = [str(x).strip() if x else "" for x in rows[0]]
    jR, jD, jT = h.index("TRUMP"), h.index("HARRIS"), h.index("TOTAL VOTES")
    eR, eD = h.index("ELECTORAL VOTE: TRUMP (R)"), h.index("ELECTORAL VOTE: HARRIS (D)")
    reg = []
    for r in rows[1:]:
        if not r or not r[0] or str(r[0]).strip().rstrip("*") not in US_NOME: continue
        st = str(r[0]).strip().rstrip("*"); R, D, T = ni(r[jR]), ni(r[jD]), ni(r[jT])
        reg.append({"id": st, "n": US_NOME[st], "eleitores": None, "votantes": None, "brancos": None, "nulos": None,
                    "validos": T, "v": {"R": R, "D": D, "O": T - R - D}, "ev": {"D": ni(r[eD]), "R": ni(r[eR])}})
    cands = [{"id": "R", "nome": "Donald Trump", "grupo": "Republicano", "cor": R_COR}, {"id": "D", "nome": "Kamala Harris", "grupo": "Democrata", "cor": D_COR}, {"id": "O", "nome": "Outros", "grupo": "", "cor": OUTRO}]
    T = turno(cands, reg); T["nac"]["ev"] = {k: sum(x["ev"][k] for x in reg) for k in ("D", "R")}
    el.append({"ano": 2024, "turnos": {"1": T}})
    return {"pais": "US", "nome": "Estados Unidos", "nivel": "Estado", "sistema": "Colégio eleitoral",
            "fonte": "Federal Election Commission (FEC), resultados oficiais certificados por estado",
            "fonte_url": "https://www.fec.gov/introduction-campaign-finance/election-results-and-voting-information/",
            "nota": "Turno único: vence quem soma 270 delegados no colégio eleitoral, não quem tem mais votos. A FEC não publica eleitorado nem brancos e nulos, por isso não há comparecimento. Delegados infiéis (votos dados a outros nomes) não aparecem nos totais.",
            "eleicoes": el}

# ---------------- Brasil (TSE, base do histórico) ----------------
BR_COR = {"13": "#E0353D", "22": "#3B78EA", "17": "#3B78EA", "45": "#2E6BE6"}
def brasil(base_path):
    B = json.load(open(base_path)); el = {}
    for row in B["rows"]:
        if row["ano"] < 2014: continue
        key = f'{row["ano"]}-{row["turno"]}'
        names = B["names"][key]
        t = el.setdefault(row["ano"], {}).setdefault(str(row["turno"]), {"names": names, "reg": []})
        t["reg"].append({"id": row["uf"], "n": "Exterior" if row["uf"] == "ZZ" else row["uf"], "eleitores": row["eleitorado"], "votantes": row["comparecimento"],
                         "brancos": row["brancos"], "nulos": row["nulos"], "validos": row["validos"], "v": row["cands"]})
    out = []
    for ano in sorted(el):
        tt = {}
        for k, t in el[ano].items():
            tot = {}
            for r in t["reg"]:
                for c, v in r["v"].items(): tot[c] = tot.get(c, 0) + v
            ordem = sorted(tot, key=lambda c: -tot[c])
            cands = [{"id": c, "nome": t["names"][c]["nm"].title(), "grupo": t["names"][c]["sg"], "cor": BR_COR.get(c, OUTRO) if k == "2" or ordem.index(c) < 2 else OUTRO} for c in ordem]
            tt[k] = turno(cands, t["reg"])
        out.append({"ano": ano, "turnos": tt})
    return {"pais": "BR", "nome": "Brasil", "nivel": "UF", "sistema": "2 turnos",
            "fonte": "Tribunal Superior Eleitoral (TSE)", "fonte_url": "https://dadosabertos.tse.jus.br/",
            "nota": "Percentual sobre votos válidos (sem brancos e nulos). ZZ = eleitores no exterior.", "eleicoes": out}

if __name__ == "__main__":
    xlsdir = sys.argv[3]
    for P in (argentina(), franca(xlsdir), eua(), brasil(sys.argv[4])):
        json.dump(P, open(os.path.join(OUT, P["pais"].lower() + ".json"), "w"), ensure_ascii=False, separators=(",", ":"))
        for e in P["eleicoes"]:
            for k, T in e["turnos"].items():
                n = T["nac"]; tot = n["validos"] or 1
                top = sorted(T["cand"], key=lambda c: -n["v"].get(c["id"], 0))[:3]
                print(P["pais"], e["ano"], k, len(T["reg"]), "reg | eleit", n["eleitores"], "vot", n["votantes"], "val", n["validos"], "|",
                      " · ".join(f'{c["nome"]} {n["v"][c["id"]]:,} ({n["v"][c["id"]]/tot*100:.2f}%)' for c in top))
