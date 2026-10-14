# Como usar

Guia de uso da **Imobiliária**.

## Para que serve

Plataforma web local para uma imobiliária: procurar imóveis com filtros,
montar propostas de compra/locação a partir das preferências do cliente e
consolidar dados de condomínios — tudo rodando na própria máquina.

## Primeiro uso

1. Inicie (ver `docs/INSTALACAO.md`).
2. Abra <http://127.0.0.1:5000>.
3. Use o menu superior: **Procurar Imóveis**, **Propostas** e **Condomínios**.

## Funcionalidades

- **Procurar imóveis:** combine filtros (tipo, faixa de preço, bairro,
  quartos) e veja o ranking de aderência.
- **Propostas:** informe orçamento e preferências do cliente e gere a
  proposta; o sistema compara com referências de mercado.
- **Condomínios:** consulte os dados consolidados e gere o resumo comparativo.

## Dados

- Tudo roda em memória/local; não há serviço externo nem chave de API.
- Se você adicionar persistência, guarde o arquivo em `dados/` (ignorado pelo
  Git) e faça backup copiando essa pasta.

## Solução de problemas

- **Porta ocupada:** `PORT=8080 sh iniciar.sh`.
- **Python não encontrado:** instale Python 3.10+ e confirme com `python3 -V`.
