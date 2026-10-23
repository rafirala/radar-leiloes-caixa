"""Lê as planilhas "Lista de imóveis" da Caixa (uma por estado, baixadas à mão em dados/bruto/) e gera uma tabela limpa.

Formato da Caixa: CSV com ";" em latin-1; linha 1 = título e data de geração; linha 2 = cabeçalho; depois um imóvel
por linha. A coluna "Descrição" traz tipo, áreas, quartos e vagas em texto, que aqui viram colunas.
Saída: dados/imoveis.csv
Uso: python src/ler_caixa.py
"""
import csv
import re
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
BRUTO = RAIZ / "dados" / "bruto"


def numero_br(txt):
    """'1.331.000,00' -> 1331000.0; '36.27' (desconto) -> 36.27."""
    t = (txt or "").strip()
    if not t:
        return None
    if "," in t:
        t = t.replace(".", "").replace(",", ".")
    try:
        return float(t)
    except ValueError:
        return None


def ler_descricao(d):
    """'Apartamento, 45.48 de área total, 40.00 de área privativa, 0.00 de área do terreno, 2 qto(s), ... 1 vaga(s)'."""
    tipo = d.split(",")[0].strip()

    def area(nome):
        m = re.search(r"([\d.]+) de área " + nome, d)
        return float(m.group(1)) if m and float(m.group(1)) > 0 else None

    q = re.search(r"(\d+) qto", d)
    v = re.search(r"(\d+) vaga", d)
    return {"tipo": tipo, "area_total": area("total"), "area_privativa": area("privativa"), "area_terreno": area("do terreno"),
            "quartos": int(q.group(1)) if q else None, "vagas": int(v.group(1)) if v else None}


def ler_arquivo(caminho):
    texto = caminho.read_bytes().decode("latin-1")
    if "Radware" in texto or "<html" in texto[:200].lower():
        raise ValueError(f"{caminho.name}: veio a página de bloqueio da Caixa, não a planilha. Baixe de novo pelo navegador.")
    linhas = [l for l in texto.splitlines() if l.strip()]
    data_geracao = re.search(r"(\d{2}/\d{2}/\d{4})", linhas[0])
    cab = [c.strip() for c in linhas[1].split(";")]
    saida = []
    for l in csv.reader(linhas[2:], delimiter=";"):
        if len(l) < len(cab):
            continue
        r = dict(zip(cab, (c.strip() for c in l)))
        preco, aval = numero_br(r.get("Preço")), numero_br(r.get("Valor de avaliação"))
        item = {"id": r.get("N° do imóvel"), "uf": r.get("UF"), "cidade": r.get("Cidade"), "bairro": r.get("Bairro"),
                "endereco": r.get("Endereço"), "preco": preco, "avaliacao": aval, "desconto_pct": numero_br(r.get("Desconto")),
                "financiamento": r.get("Financiamento", "").lower().startswith("sim"), "modalidade": r.get("Modalidade de venda"),
                "link": r.get("Link de acesso"), "data_lista": data_geracao.group(1) if data_geracao else ""}
        item.update(ler_descricao(r.get("Descrição", "")))
        area = item["area_privativa"] or item["area_total"]
        item["preco_m2"] = round(preco / area, 2) if preco and area else None
        saida.append(item)
    return saida


def main():
    arquivos = sorted(BRUTO.glob("*.csv"))
    if not arquivos:
        raise SystemExit(f"Nenhuma planilha em {BRUTO}. Baixe a 'Lista de imóveis' de cada estado no site da Caixa.")
    todos = []
    for a in arquivos:
        lote = ler_arquivo(a)
        print(f"{a.name}: {len(lote)} imóveis")
        todos += lote
    with open(RAIZ / "dados" / "imoveis.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(todos[0]))
        w.writeheader()
        w.writerows(todos)
    print(f"total: {len(todos)} -> {RAIZ / 'dados' / 'imoveis.csv'}")


if __name__ == "__main__":
    main()
