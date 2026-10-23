"""Localiza cada imóvel (latitude/longitude) pelo Nominatim, o serviço gratuito do OpenStreetMap.

Regras do serviço respeitadas: no máximo 1 consulta por segundo, User-Agent identificando a aplicação, e cache local
(dados/geocache.json) para nunca repetir a mesma consulta. Roda em fases: centro das cidades, depois dos bairros, depois o endereço exato
só dos destaques. Cada imóvel fica com a localização mais precisa já achada; o campo "precisao" diz qual.
Entrada: dados/imoveis.csv · Saída: dados/imoveis_geo.csv
Uso: python src/geocodificar.py   (pode parar e retomar: o cache guarda o que já foi feito)
"""
import csv
import json
import re
import time
from pathlib import Path

import requests

RAIZ = Path(__file__).resolve().parent.parent
CACHE = RAIZ / "dados" / "geocache.json"
UA = {"User-Agent": "mapa-leiloes-imoveis/0.1 (projeto pessoal de estudo de dados)"}
URL = "https://nominatim.openstreetmap.org/search"


def limpa_endereco(e):
    """'RUA ALFREDO DE ANDRADE, N. 75, Apto 303, BL 07' -> 'RUA ALFREDO DE ANDRADE 75'."""
    e = (e or "").upper()
    m = re.match(r"\s*([^,]+?)\s*,\s*N\.?\s*([0-9]+)", e)
    if m:
        return f"{m.group(1)} {m.group(2)}"
    return e.split(",")[0].strip()


def consulta(q, cache):
    if q in cache:
        return cache[q]
    time.sleep(1.1)
    try:
        r = requests.get(URL, params={"q": q, "format": "json", "limit": 1, "countrycodes": "br"}, headers=UA, timeout=30)
        r.raise_for_status()
        js = r.json()
        res = [float(js[0]["lat"]), float(js[0]["lon"])] if js else None
    except Exception as ex:  # noqa: BLE001
        print("erro", q, ex)
        return None  # não grava erro no cache: tenta de novo na próxima vez
    cache[q] = res
    return res


def main():
    cache = json.loads(CACHE.read_text(encoding="utf-8")) if CACHE.exists() else {}
    imoveis = list(csv.DictReader(open(RAIZ / "dados" / "imoveis.csv", encoding="utf-8")))
    q_cidade = lambda x: f"{x['cidade'].title()}, {x['uf']}"
    q_bairro = lambda x: f"{x['bairro'].title()}, {x['cidade'].title()}, {x['uf']}"
    q_end = lambda x: f"{limpa_endereco(x['endereco'])}, {x['cidade'].title()}, {x['uf']}"
    destaques = set()
    mapa = RAIZ / "docs" / "dados_mapa.json"
    if mapa.exists():
        destaques = {i["id"] for i in json.loads(mapa.read_text(encoding="utf-8"))["imoveis"] if i.get("destaque")}

    # caixa de cada estado: localização fora dela é homônimo de outro lugar (ex.: Palmas-TO no lugar de Palmas-PR)
    CAIXA = {"PR": (-26.8, -22.4, -54.7, -48.0), "SC": (-29.4, -25.9, -53.9, -48.3), "SP": (-25.4, -19.7, -53.2, -44.1)}
    dentro = lambda uf, p: p and (uf not in CAIXA or (CAIXA[uf][0] <= p[0] <= CAIXA[uf][1] and CAIXA[uf][2] <= p[1] <= CAIXA[uf][3]))
    ESTADO = {"PR": "Paraná", "SC": "Santa Catarina", "SP": "São Paulo"}
    q_cidade2 = lambda x: f"{x['cidade'].title()}, {ESTADO.get(x['uf'], x['uf'])}, Brasil"

    def gravar():
        """Cada imóvel fica com a localização mais precisa já conhecida: endereço > bairro > cidade."""
        CACHE.write_text(json.dumps(cache, ensure_ascii=False), encoding="utf-8")
        for x in imoveis:
            x["lat"] = x["lon"] = ""
            x["precisao"] = "nao_achado"
            for nivel, q in (("endereco", q_end(x)), ("bairro", q_bairro(x)), ("cidade", q_cidade(x)), ("cidade", q_cidade2(x))):
                pos = cache.get(q)
                if dentro(x["uf"], pos):
                    x["lat"], x["lon"], x["precisao"] = pos[0], pos[1], nivel
                    break
        with open(RAIZ / "dados" / "imoveis_geo.csv", "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(imoveis[0]))
            w.writeheader()
            w.writerows(imoveis)
        from collections import Counter
        print("  precisão:", dict(Counter(x["precisao"] for x in imoveis)), flush=True)

    # fases: cidades (rápido, o mapa já funciona) -> bairros -> endereço exato só dos destaques
    fases = [("cidades", {q_cidade(x) for x in imoveis}), ("bairros", {q_bairro(x) for x in imoveis}),
             ("endereços dos destaques", {q_end(x) for x in imoveis if x["id"] in destaques}),
             ("cidades com nome do estado (homônimos)", {q_cidade2(x) for x in imoveis
                                                          if not dentro(x["uf"], cache.get(q_cidade(x)))})]
    for nome, consultas in fases:
        pend = sorted(q for q in consultas if q not in cache)
        print(f"fase {nome}: {len(consultas)} consultas, {len(pend)} novas", flush=True)
        for n, q in enumerate(pend, 1):
            consulta(q, cache)
            if n % 100 == 0:
                print(f"  {n}/{len(pend)}", flush=True)
                gravar()
        gravar()


if __name__ == "__main__":
    main()
