"""Envia data/secao/{cd}.json para a tabela raiox do Supabase (acesso só para assinantes).

Precisa dos segredos do GitHub SUPABASE_URL e SUPABASE_SERVICE_KEY (chave service_role,
que nunca vai para o site). Mantém no repositório público apenas a cidade de exemplo.
"""
import glob, json, os, sys, urllib.request

DEMO = {"66397"}  # Limeira: Raio-X de exemplo, aberto ao público
url, key = os.environ.get("SUPABASE_URL", "").rstrip("/"), os.environ.get("SUPABASE_SERVICE_KEY", "")
arquivos = sorted(glob.glob(os.path.join(os.path.dirname(__file__), "..", "data", "secao", "*.json")))
if not url or not key:
    print("Supabase não configurado: arquivos ficam só no repositório.")
    sys.exit(0)
for f in arquivos:
    d = json.load(open(f, encoding="utf-8"))
    body = json.dumps({"cd": d["cd"], "uf": d["uf"], "nome": d["nome"].title(), "dados": d}).encode()
    req = urllib.request.Request(f"{url}/rest/v1/raiox", data=body, method="POST", headers={
        "apikey": key, "Authorization": f"Bearer {key}", "Content-Type": "application/json",
        "Prefer": "resolution=merge-duplicates,return=minimal"})
    with urllib.request.urlopen(req, timeout=120) as r:
        print(d["cd"], d["nome"], "enviado", r.status)
    if d["cd"] not in DEMO:
        os.remove(f)  # dados pagos não ficam no repositório público
        print("  removido do repositório público")
