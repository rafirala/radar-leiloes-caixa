"""Publica o radar sozinho quando a Caixa solta lista nova (pedido do Rafael, 23/10/2026).

Roda às 06:05 (tarefa do Windows "TARS Radar Publicar"), 5 min depois do download das 06:00 (baixar_caixa.py).
1. Confere as 3 planilhas em dados/bruto: são CSV da Caixa (não a página de bloqueio) e têm data de geração.
2. Se nenhuma for mais nova que a lista publicada (docs/dados_mapa.json), para: "sem novidade".
3. Roda o radar inteiro: ler_caixa -> geocodificar -> oportunidades -> montar_mapa.
4. Bom senso: se o total de imóveis cair mais de 30%, NÃO publica (algo veio errado).
5. Commit só de docs/dados_mapa.json e docs/index.html e push (GitHub Pages atualiza sozinho).
Resultado numa linha em dados/publicacao.log (o TARS lê no bom dia).
"""
import datetime as dt
import json
import re
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
BRUTO = RAIZ / "dados" / "bruto"
DADOS_SITE = RAIZ / "docs" / "dados_mapa.json"
LOG = RAIZ / "dados" / "publicacao.log"
UFS = ("PR", "SC", "SP")
QUEDA_MAX = 0.30


def registrar(msg):
    linha = f"{dt.datetime.now():%Y-%m-%d %H:%M} {msg}"
    print(linha)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(linha + "\n")


def data_br(s):
    return dt.datetime.strptime(s, "%d/%m/%Y").date()


def data_planilha(uf):
    arq = BRUTO / f"Lista_imoveis_{uf}.csv"
    if not arq.exists():
        raise ValueError(f"{uf}: arquivo não existe")
    inicio = arq.read_bytes()[:600].decode("latin-1", errors="ignore")
    if "radware" in inicio.lower() or "<html" in inicio.lower():
        raise ValueError(f"{uf}: é a página de bloqueio, não a planilha")
    if "N° do imóvel" not in inicio:
        raise ValueError(f"{uf}: cabeçalho da Caixa não encontrado")
    m = re.search(r"(\d{2}/\d{2}/\d{4})", next(l for l in inicio.splitlines() if l.strip()))
    if not m:
        raise ValueError(f"{uf}: sem data de geração")
    return data_br(m.group(1))


def rodar(*args):
    r = subprocess.run([sys.executable, *args], cwd=RAIZ, capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    if r.returncode != 0:
        raise RuntimeError(f"{' '.join(args)} falhou: {(r.stderr or r.stdout)[-300:]}")
    return r.stdout


def git(*args):
    r = subprocess.run(["git", *args], cwd=RAIZ, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if r.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} falhou: {(r.stderr or r.stdout)[-300:]}")
    return r.stdout


def main():
    try:
        datas = {uf: data_planilha(uf) for uf in UFS}
    except ValueError as e:
        registrar(f"ERRO planilha: {e}. Nada publicado.")
        return 1

    antes = json.loads(DADOS_SITE.read_text(encoding="utf-8"))
    publicada = data_br(antes["data_lista"]) if antes.get("data_lista") else dt.date.min
    nova = max(datas.values())
    if nova <= publicada:
        registrar(f"sem novidade: planilhas de {nova:%d/%m/%Y}, site já está com {publicada:%d/%m/%Y}.")
        return 0

    try:
        for script in ("ler_caixa.py", "geocodificar.py", "oportunidades.py", "montar_mapa.py"):
            rodar(f"src/{script}")
    except RuntimeError as e:
        git("checkout", "--", "docs/dados_mapa.json", "docs/index.html")
        registrar(f"ERRO no radar: {e}. Site mantido como estava.")
        return 1

    depois = json.loads(DADOS_SITE.read_text(encoding="utf-8"))
    n_antes, n_depois = len(antes["imoveis"]), len(depois["imoveis"])
    if n_antes and n_depois < n_antes * (1 - QUEDA_MAX):
        git("checkout", "--", "docs/dados_mapa.json", "docs/index.html")
        registrar(f"ALERTA: imóveis caíram de {n_antes} para {n_depois} (mais de {QUEDA_MAX:.0%}). Nada publicado.")
        return 1

    ids_antes = {i.get("id") for i in antes["imoveis"]}
    ids_depois = {i.get("id") for i in depois["imoveis"]}
    entraram, sairam = len(ids_depois - ids_antes), len(ids_antes - ids_depois)
    try:
        git("add", "docs/dados_mapa.json", "docs/index.html")
        git("commit", "-m", f"Lista da Caixa de {nova:%d/%m/%Y} ({n_depois} imóveis)")
        git("push")
    except RuntimeError as e:
        registrar(f"ERRO ao publicar: {e}. Radar atualizado no PC, não no site.")
        return 1
    registrar(f"PUBLICADO lista de {nova:%d/%m/%Y}: {n_antes} -> {n_depois} imóveis (+{entraram} / -{sairam}).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
