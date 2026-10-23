"""Baixa automaticamente as listas de imóveis da Caixa (PR, SC, SP).

Salva em dados/bruto/Lista_imoveis_{UF}.csv.
Usa o curl do Windows, com verificação de certificado ligada (23/10: testado, a Caixa entrega a planilha normal).
Uso: python src/baixar_caixa.py
"""
import datetime
import os
import subprocess
import sys
import time
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
BRUTO = RAIZ / "dados" / "bruto"

URLS = {
    "PR": "https://venda-imoveis.caixa.gov.br/listaweb/Lista_imoveis_PR.csv",
    "SC": "https://venda-imoveis.caixa.gov.br/listaweb/Lista_imoveis_SC.csv",
    "SP": "https://venda-imoveis.caixa.gov.br/listaweb/Lista_imoveis_SP.csv",
}


def baixar_estados():
    BRUTO.mkdir(parents=True, exist_ok=True)
    agora = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{agora}] Iniciando download das listas da Caixa...")

    erros = []

    for uf, url in URLS.items():
        destino = BRUTO / f"Lista_imoveis_{uf}.csv"
        try:
            cmd = ["curl.exe", "-s", "--max-time", "60", url]
            resultado = subprocess.run(cmd, capture_output=True, check=False)

            if resultado.returncode != 0:
                msg = f"{uf}: curl falhou com código {resultado.returncode} ({resultado.stderr.decode('latin-1', errors='ignore').strip()})"
                print(f"  [ERRO] {msg}")
                erros.append(msg)
                continue

            conteudo = resultado.stdout

            # Validações de segurança contra páginas de bloqueio (Radware/WAF)
            inicio = conteudo[:400].decode("latin-1", errors="ignore").lower()
            if "radware" in inicio or "<html" in inicio or "<!doctype html" in inicio:
                msg = f"{uf}: Retornou tela de bloqueio Radware/HTML da Caixa. Arquivo mantido sem alteração."
                print(f"  [ERRO] {msg}")
                erros.append(msg)
                continue

            if len(conteudo) < 2000:
                msg = f"{uf}: Arquivo muito pequeno ({len(conteudo)} bytes). Possível erro na Caixa."
                print(f"  [AVISO] {msg}")

            with open(destino, "wb") as f:
                f.write(conteudo)

            tamanho_kb = len(conteudo) / 1024
            print(f"  [OK] {uf}: {tamanho_kb:.1f} KB baixado com sucesso -> {destino.name}")

            # Pequeno intervalo entre downloads para não engatilhar rate limit
            time.sleep(1)

        except Exception as e:
            msg = f"{uf}: Exceção ao tentar baixar ({e})"
            print(f"  [ERRO] {msg}")
            erros.append(msg)

    if erros:
        print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] Concluído com {len(erros)} erro(s).")
        sys.exit(1)
    else:
        print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] Todas as listas baixadas e salvas em {BRUTO}.")


if __name__ == "__main__":
    baixar_estados()

