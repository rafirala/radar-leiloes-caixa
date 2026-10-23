# Radar de leilões da Caixa

**Mapa e ranking dos imóveis à venda pela Caixa (leilão, licitação e venda direta) no Paraná, em Santa Catarina e em São Paulo, com uma nota de oportunidade explicada para cada imóvel.**

O dashboard está em `docs/index.html`: filtre por estado, cidade, tipo, preço e financiamento, veja os imóveis no mapa e abra cada um no site da Caixa.

## O que a ferramenta faz

1. **Lê a lista oficial da Caixa** (uma planilha por estado) e transforma o texto da descrição em colunas: tipo, área, quartos, vagas e preço por m².
2. **Localiza cada imóvel** pelo OpenStreetMap, em fases: centro da cidade, centro do bairro e endereço exato dos destaques. Localizações que caem fora do estado (cidades com o mesmo nome em outro lugar) são descartadas.
3. **Dá uma nota de 0 a 85**, sempre com o motivo:
   - até 40 pontos: desconto sobre a avaliação da própria Caixa;
   - até 15: preço do m² contra a média da cidade no FipeZAP (contexto, porque a média da cidade inclui bairros nobres e prédios novos);
   - 15: aceita financiamento;
   - até 15: modalidade (venda direta é mais simples que leilão).
4. **Marca** os 5% de maior nota como destaque e os casos fora da curva (área acima de 300 m² ou preço acima de R$ 1 milhão) como "conferir".

## Retrato da lista de 22/10/2026

- 3.275 imóveis: 2.694 em SP, 434 no PR e 147 em SC. A maioria são apartamentos (2.131) e casas (913).
- Desconto mediano de 39% sobre o valor de avaliação; só 310 imóveis aceitam financiamento.
- Em Santa Catarina, boa parte aparece com 0% de desconto: são imóveis em "Leilão SFI", cujo primeiro leilão costuma começar pelo valor de avaliação.

## O que a planilha não diz

Se o imóvel está ocupado, se há dívidas de IPTU ou de condomínio e quem paga cada custo. Isso está no edital de cada imóvel. **Nota alta é um convite para olhar o imóvel, não uma recomendação de compra.**

## Como atualizar

A Caixa protege o site contra downloads automáticos, então a lista é baixada à mão, pelo navegador, uma por estado:
`https://venda-imoveis.caixa.gov.br/listaweb/Lista_imoveis_PR.csv` (troque PR por SC ou SP), salva em `dados/bruto/`.

```bash
pip install -r requirements.txt
python src/ler_caixa.py       # lê as planilhas -> dados/imoveis.csv
python src/geocodificar.py    # localiza (1 consulta por segundo; usa cache)
python src/oportunidades.py   # notas -> docs/dados_mapa.json
python src/montar_mapa.py     # docs/index.html
```

O preço de mercado vem da [planilha de séries históricas do FipeZAP](https://downloads.fipe.org.br/indices/fipezap/fipezap-serieshistoricas.xlsx), salva como `dados/bruto/fipezap_series.xlsx`.

## Fontes

Lista de imóveis: [Caixa Econômica Federal](https://venda-imoveis.caixa.gov.br) · preço de mercado: [Índice FipeZAP](https://www.fipe.org.br/pt-br/indices/fipezap/) · localização: © colaboradores do [OpenStreetMap](https://www.openstreetmap.org/copyright) (Nominatim) · contornos dos estados: IBGE. Elaboração própria. Usei assistentes de IA para escrever e revisar o código.

---

## English summary

**Caixa auction radar.** A map and ranking of the ~3,300 properties that Brazil's largest mortgage bank (Caixa) is selling through auctions and direct sales in three states, each with an explained opportunity score: discount versus the bank's own appraisal, price per m² versus the city average (FipeZAP index), mortgage eligibility and sale type. Built with Python (parsing the official lists, geocoding with OpenStreetMap/Nominatim in rate-limited phases with state-boundary checks) and a Leaflet dashboard. The bank blocks automated downloads, so lists are downloaded manually; the tool never bypasses that protection. A high score is an invitation to look, not investment advice.

*Autor / Author:* Rafael Irala · [linkedin.com/in/rafael-irala](https://www.linkedin.com/in/rafael-irala/)
