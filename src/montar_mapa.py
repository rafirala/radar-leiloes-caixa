"""Monta a página do radar: docs/mapa_modelo.html + docs/dados_mapa.json + contornos dos estados (IBGE).
Saída: docs/mapa.html (para a prévia) e docs/index.html (documento completo, para abrir no navegador ou no GitHub Pages).
Uso: python src/montar_mapa.py   (depois de oportunidades.py)
"""
import json
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
DOCS = RAIZ / "docs"
IBGE = RAIZ / "dados" / "bruto" / "ibge"


def main():
    feats = []
    for uf in ("41", "42", "35"):  # PR, SC, SP
        feats += json.loads((IBGE / f"uf_{uf}.json").read_text(encoding="utf-8"))["features"]
    ufs = json.dumps({"type": "FeatureCollection", "features": feats}, separators=(",", ":"))
    dados = (DOCS / "dados_mapa.json").read_text(encoding="utf-8")
    modelo = (DOCS / "mapa_modelo.html").read_text(encoding="utf-8")
    assert "/*DADOS*/null" in modelo and "/*UFS*/null" in modelo
    pagina = modelo.replace("/*DADOS*/null", dados).replace("/*UFS*/null", ufs)
    (DOCS / "mapa.html").write_text(pagina, encoding="utf-8")
    completo = ('<!doctype html>\n<html lang="pt-BR">\n<head>\n<meta charset="utf-8">\n'
                '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n</head>\n<body>\n'
                + pagina + "\n</body>\n</html>\n")
    (DOCS / "index.html").write_text(completo, encoding="utf-8")
    print(f"ok -> docs/mapa.html ({len(pagina) / 1024:.0f} KB)")


if __name__ == "__main__":
    main()
