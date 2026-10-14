# Imobiliária — plataforma de imóveis com IA

Sistema web local para uma imobiliária: **procurar imóveis**, montar
**propostas** de compra/locação e analisar **condomínios**, com apoio de
agentes de IA. Roda 100% na máquina, sem nuvem, sem chave de API e sem
dependências externas — é só Python (biblioteca padrão).

## O que faz

- **Procurar imóveis** — busca com filtros (tipo, faixa de preço, bairro,
  quartos) sobre uma base de imóveis, com ranking de aderência.
- **Propostas** — gera proposta a partir do orçamento e das preferências do
  cliente, comparando com referências de mercado.
- **Condomínios** — consolida dados de condomínios (taxas, estrutura,
  contatos) e produz um resumo comparativo.
- **API HTTP** pronta para integrar com outros sistemas.

## Rodar

### Local (mais rápido)

```bash
sh iniciar.sh
# ou: PORT=8080 python3 app.py
```

Abra <http://127.0.0.1:5000> (a porta vem da variável `PORT`, padrão `5000`).

### Como serviço (sobe com a máquina)

```bash
sh instalar.sh
systemctl --user status app-imobiliaria
```

### Docker

```bash
docker compose up --build
```

## API

| Método | Rota | Descrição |
| --- | --- | --- |
| GET | `/` | Interface web |
| GET | `/api/estado` | Estado geral |
| GET | `/api/ping` | Healthcheck |
| GET | `/api/imoveis` | Lista de imóveis |
| GET | `/api/busca` | Busca com filtros |
| GET | `/api/filtros` | Opções de filtro |
| GET | `/api/propostas/opcoes` | Opções para proposta |
| GET | `/api/propostas/mercado` | Referências de mercado |
| POST | `/api/propostas` | Cria proposta |
| GET | `/api/condominios` | Lista condomínios |
| GET | `/api/condominios/resumo` | Resumo comparativo |
| POST | `/api/condominios/coletar` | Coleta/atualiza dados |

## Estrutura

```
app.py           # entrada única: servidor HTTP + rotas
busca.py         # busca e ranking de imóveis
propostas.py     # geração de propostas
condominios.py   # consolidação de condomínios
web/             # interface (HTML/CSS/JS)
docs/            # instalação, uso e entrega a clientes
```

## Requisitos

- Python 3.10+ (somente biblioteca padrão).
- Opcional: Docker.

Veja também `docs/INSTALACAO.md` e `docs/USO.md`.
