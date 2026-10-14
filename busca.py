#!/usr/bin/env python3
"""Busca avançada com IA local para a Imobiliaria.

Este módulo é importado por ``app.py`` — não é um servidor. Ele contém:

* ``CATALOGO``: catálogo de imóveis de demonstração.
* ``interpretar``: motor de IA local que traduz uma frase em critérios
  estruturados (preço, localização, quartos, tipo, vagas, área).
* ``buscar``: aplica os critérios, pontua a relevância e explica o porquê.

Sem dependências externas: apenas a biblioteca padrão do Python, para
funcionar 100% offline, sem chaves nem nuvem.
"""

from __future__ import annotations

import re
import unicodedata

# --------------------------------------------------------------------------- #
# Catálogo de demonstração
# --------------------------------------------------------------------------- #
CATALOGO: list[dict] = [
    {"id": 1, "titulo": "Apartamento reformado na Vila Madalena",
     "tipo": "apartamento", "operacao": "venda", "cidade": "São Paulo",
     "bairro": "Vila Madalena", "preco": 780000, "quartos": 2, "banheiros": 2,
     "vagas": 1, "area_m2": 68,
     "descricao": "Dois quartos, varanda gourmet e perto do metrô; ótimo para "
                  "quem busca vida de bairro em São Paulo."},
    {"id": 2, "titulo": "Cobertura duplex em Moema",
     "tipo": "cobertura", "operacao": "venda", "cidade": "São Paulo",
     "bairro": "Moema", "preco": 2450000, "quartos": 4, "banheiros": 5,
     "vagas": 4, "area_m2": 260,
     "descricao": "Cobertura com piscina privativa, quatro suítes e vista "
                  "para o parque Ibirapuera."},
    {"id": 3, "titulo": "Studio compacto na Vila Olímpia",
     "tipo": "studio", "operacao": "aluguel", "cidade": "São Paulo",
     "bairro": "Vila Olímpia", "preco": 3200, "quartos": 1, "banheiros": 1,
     "vagas": 1, "area_m2": 32,
     "descricao": "Studio mobiliado no coração da Vila Olímpia, ideal para "
                  "quem trabalha na Faria Lima."},
    {"id": 4, "titulo": "Casa térrea com quintal em Perdizes",
     "tipo": "casa", "operacao": "venda", "cidade": "São Paulo",
     "bairro": "Perdizes", "preco": 1350000, "quartos": 3, "banheiros": 3,
     "vagas": 2, "area_m2": 180,
     "descricao": "Casa de três quartos com quintal arborizado e edícula, em "
                  "rua tranquila de Perdizes."},
    {"id": 5, "titulo": "Apartamento 3 quartos em Pinheiros",
     "tipo": "apartamento", "operacao": "venda", "cidade": "São Paulo",
     "bairro": "Pinheiros", "preco": 1120000, "quartos": 3, "banheiros": 3,
     "vagas": 2, "area_m2": 96,
     "descricao": "Três quartos, suíte ampla e duas vagas a poucos passos da "
                  "estação Fradique Coutinho."},
    {"id": 6, "titulo": "Apartamento 2 quartos em Botafogo",
     "tipo": "apartamento", "operacao": "aluguel", "cidade": "Rio de Janeiro",
     "bairro": "Botafogo", "preco": 4500, "quartos": 2, "banheiros": 2,
     "vagas": 1, "area_m2": 72,
     "descricao": "Dois quartos com armários planejados, perto do metrô "
                  "Botafogo e do shopping."},
    {"id": 7, "titulo": "Cobertura vista mar em Ipanema",
     "tipo": "cobertura", "operacao": "venda", "cidade": "Rio de Janeiro",
     "bairro": "Ipanema", "preco": 4100000, "quartos": 4, "banheiros": 4,
     "vagas": 3, "area_m2": 240,
     "descricao": "Cobertura de frente para a praia de Ipanema, quatro "
                  "suítes e terraço com churrasqueira."},
    {"id": 8, "titulo": "Casa em condomínio na Barra da Tijuca",
     "tipo": "casa", "operacao": "venda", "cidade": "Rio de Janeiro",
     "bairro": "Barra da Tijuca", "preco": 1900000, "quartos": 4, "banheiros": 5,
     "vagas": 4, "area_m2": 320,
     "descricao": "Casa em condomínio fechado com segurança 24h, lazer "
                  "completo e quatro vagas."},
    {"id": 9, "titulo": "Apartamento 1 quarto no Centro de Curitiba",
     "tipo": "apartamento", "operacao": "aluguel", "cidade": "Curitiba",
     "bairro": "Centro", "preco": 1800, "quartos": 1, "banheiros": 1,
     "vagas": 0, "area_m2": 40,
     "descricao": "Apartamento de um quarto e sala, mobiliado, no centro de "
                  "Curitiba, perto da Rua XV."},
    {"id": 10, "titulo": "Casa 3 quartos em Santa Felicidade",
     "tipo": "casa", "operacao": "venda", "cidade": "Curitiba",
     "bairro": "Santa Felicidade", "preco": 890000, "quartos": 3, "banheiros": 3,
     "vagas": 2, "area_m2": 160,
     "descricao": "Casa com três quartos, churrasqueira e amplo terreno em "
                  "Santa Felicidade."},
    {"id": 11, "titulo": "Apartamento 3 quartos em Batel",
     "tipo": "apartamento", "operacao": "venda", "cidade": "Curitiba",
     "bairro": "Batel", "preco": 1500000, "quartos": 3, "banheiros": 4,
     "vagas": 3, "area_m2": 130,
     "descricao": "Apartamento de alto padrão no Batel, três suítes e lazer "
                  "completo no prédio."},
    {"id": 12, "titulo": "Sala comercial na Avenida Paulista",
     "tipo": "comercial", "operacao": "aluguel", "cidade": "São Paulo",
     "bairro": "Bela Vista", "preco": 8900, "quartos": 0, "banheiros": 2,
     "vagas": 2, "area_m2": 110,
     "descricao": "Conjunto comercial pronto para uso na Avenida Paulista, "
                  "com recepção e duas vagas."},
    {"id": 13, "titulo": "Apartamento 2 quartos em Cambuí",
     "tipo": "apartamento", "operacao": "venda", "cidade": "Campinas",
     "bairro": "Cambuí", "preco": 620000, "quartos": 2, "banheiros": 2,
     "vagas": 2, "area_m2": 78,
     "descricao": "Dois quartos com varanda, em uma das melhores regiões de "
                  "Campinas para morar."},
    {"id": 14, "titulo": "Casa de campo em Sousas",
     "tipo": "casa", "operacao": "venda", "cidade": "Campinas",
     "bairro": "Sousas", "preco": 980000, "quartos": 4, "banheiros": 4,
     "vagas": 4, "area_m2": 300,
     "descricao": "Casa de campo com piscina, pomar e quatro quartos em "
                  "Sousas."},
    {"id": 15, "titulo": "Studio na Savassi",
     "tipo": "studio", "operacao": "aluguel", "cidade": "Belo Horizonte",
     "bairro": "Savassi", "preco": 2400, "quartos": 1, "banheiros": 1,
     "vagas": 1, "area_m2": 35,
     "descricao": "Studio moderno na Savassi, cercado de bares, cafés e "
                  "transporte público."},
    {"id": 16, "titulo": "Apartamento 3 quartos no Buritis",
     "tipo": "apartamento", "operacao": "venda", "cidade": "Belo Horizonte",
     "bairro": "Buritis", "preco": 720000, "quartos": 3, "banheiros": 2,
     "vagas": 2, "area_m2": 92,
     "descricao": "Três quartos, área de lazer e vista para a Serra do "
                  "Curral em Belo Horizonte."},
    {"id": 17, "titulo": "Apartamento 4 quartos em Boa Viagem",
     "tipo": "apartamento", "operacao": "venda", "cidade": "Recife",
     "bairro": "Boa Viagem", "preco": 1450000, "quartos": 4, "banheiros": 4,
     "vagas": 3, "area_m2": 165,
     "descricao": "Quatro quartos a duas quadras da praia de Boa Viagem, com "
                  "vista para o mar."},
    {"id": 18, "titulo": "Casa em Aldeia dos Camarás",
     "tipo": "casa", "operacao": "aluguel", "cidade": "Recife",
     "bairro": "Aldeia", "preco": 3500, "quartos": 3, "banheiros": 3,
     "vagas": 2, "area_m2": 150,
     "descricao": "Casa de três quartos com quintal e área verde, no "
                  "condomínio Aldeia dos Camarás."},
    {"id": 19, "titulo": "Apartamento 2 quartos na Trindade",
     "tipo": "apartamento", "operacao": "venda", "cidade": "Florianópolis",
     "bairro": "Trindade", "preco": 560000, "quartos": 2, "banheiros": 2,
     "vagas": 1, "area_m2": 70,
     "descricao": "Dois quartos próximos à universidade, ideal para "
                  "investidores e estudantes."},
    {"id": 20, "titulo": "Cobertura na Lagoa da Conceição",
     "tipo": "cobertura", "operacao": "venda", "cidade": "Florianópolis",
     "bairro": "Lagoa da Conceição", "preco": 2100000, "quartos": 3,
     "banheiros": 3, "vagas": 2, "area_m2": 200,
     "descricao": "Cobertura com vista para a lagoa, três quartos e deck "
                  "para contemplar o pôr do sol."},
    {"id": 21, "titulo": "Apartamento 2 quartos em Boaço",
     "tipo": "apartamento", "operacao": "aluguel", "cidade": "Belo Horizonte",
     "bairro": "Boa Viagem", "preco": 2100, "quartos": 2, "banheiros": 1,
     "vagas": 1, "area_m2": 60,
     "descricao": "Apartamento de dois quartos e sala, ótima localização e "
                  "aluguel acessível."},
    {"id": 22, "titulo": "Terreno em Alphaville",
     "tipo": "terreno", "operacao": "venda", "cidade": "São Paulo",
     "bairro": "Alphaville", "preco": 1300000, "quartos": 0, "banheiros": 0,
     "vagas": 0, "area_m2": 450,
     "descricao": "Terreno plano de 450 m² em condomínio de Alphaville, "
                  "pronto para construir."},
    {"id": 23, "titulo": "Apartamento 3 quartos no Meireles",
     "tipo": "apartamento", "operacao": "venda", "cidade": "Fortaleza",
     "bairro": "Meireles", "preco": 890000, "quartos": 3, "banheiros": 3,
     "vagas": 2, "area_m2": 105,
     "descricao": "Três quartos com sacada e vista para o mar do Meireles, "
                  "em Fortaleza."},
    {"id": 24, "titulo": "Casa de praia em Cumbuco",
     "tipo": "casa", "operacao": "aluguel", "cidade": "Fortaleza",
     "bairro": "Cumbuco", "preco": 6500, "quartos": 4, "banheiros": 4,
     "vagas": 3, "area_m2": 280,
     "descricao": "Casa de praia com piscina, quatro quartos e acesso "
                  "direto às dunas do Cumbuco."},
]

# --------------------------------------------------------------------------- #
# Motor de interpretação (IA local por regras)
# --------------------------------------------------------------------------- #
_NUMEROS_TEXTO = {
    "um": 1, "uma": 1, "dois": 2, "duas": 2, "tres": 3, "quatro": 4,
    "cinco": 5, "seis": 6,
}

_TIPOS = {
    "apartamento": "apartamento", "apto": "apartamento", "ap": "apartamento",
    "casa": "casa", "sobrado": "casa", "cobertura": "cobertura",
    "studio": "studio", "flat": "studio", "kitnet": "studio",
    "terreno": "terreno", "lote": "terreno",
    "comercial": "comercial", "sala": "comercial", "loja": "comercial",
    "conjunto": "comercial",
}

_OPERACOES = {
    "venda": "venda", "comprar": "venda", "compra": "venda",
    "aluguel": "aluguel", "alugar": "aluguel", "locacao": "aluguel",
    "locação": "aluguel",
}

_VAZIO = {"tipo": None, "operacao": None, "quartos_min": None,
          "preco_max": None, "preco_min": None, "vagas_min": None,
          "area_min": None, "local": None}


def _sem_acento(texto: str) -> str:
    return "".join(
        c for c in unicodedata.normalize("NFKD", texto)
        if not unicodedata.combining(c)
    )


def _norm(texto: str) -> str:
    return _sem_acento(texto.lower())


def _para_numero(bruto: str, escala: str | None) -> float | None:
    bruto = bruto.replace(".", "").replace(",", ".").strip()
    try:
        valor = float(bruto)
    except ValueError:
        return None
    escala = (escala or "").lower()
    if escala in ("k", "mil"):
        valor *= 1_000
    elif escala in ("milhao", "milhoes", "milhão", "milhões", "mi"):
        valor *= 1_000_000
    return valor


def _local_conhecido(texto_norm: str) -> str | None:
    """Procura no texto um bairro ou cidade do catálogo."""
    for imovel in CATALOGO:
        for campo in ("bairro", "cidade"):
            alvo = _norm(imovel[campo])
            if alvo and alvo in texto_norm:
                return imovel[campo]
    return None


def interpretar(consulta: str) -> dict:
    """Traduz uma frase livre em critérios estruturados.

    Ex.: ``"casa com 3 quartos até 1 milhão em Campinas"`` →
    ``{"tipo": "casa", "quartos_min": 3, "preco_max": 1000000, ...}``
    """
    texto = _norm(consulta or "")
    interp = dict(_VAZIO, texto=(consulta or "").strip(), termos=[])

    # Tipo de imóvel (procura a palavra mais longa para evitar "ap"/"apto")
    for chave in sorted(_TIPOS, key=len, reverse=True):
        if re.search(rf"\b{re.escape(chave)}\b", texto):
            interp["tipo"] = _TIPOS[chave]
            break

    # Operação (venda/aluguel)
    for chave, valor in _OPERACOES.items():
        if chave in texto:
            interp["operacao"] = valor
            break

    # Quartos: "3 quartos", "dois quartos", "2+ quartos"
    m = re.search(r"(\d+|[a-z]+)\s*\+?\s*quartos?", texto)
    if m:
        bruto = m.group(1)
        q = int(bruto) if bruto.isdigit() else _NUMEROS_TEXTO.get(bruto)
        if q:
            interp["quartos_min"] = q

    # Vagas: "2 vagas"
    m = re.search(r"(\d+|um|uma|dois|duas|tres|quatro)\s+vagas?", texto)
    if m:
        bruto = m.group(1)
        v = int(bruto) if bruto.isdigit() else _NUMEROS_TEXTO.get(bruto)
        if v is not None:
            interp["vagas_min"] = v

    # Área: "a partir de 80 m2"
    m = re.search(r"(\d+)\s*(?:m2|m²|metros)", texto)
    if m:
        interp["area_min"] = float(m.group(1))

    escala = r"(milhao|milhoes|mil|mi|k)"

    # Faixa de preço "entre X e Y"
    faixa = re.search(
        rf"entre\s+(r\$?\s*)?([\d.,]+)\s*{escala}?\s+e\s+"
        rf"(r\$?\s*)?([\d.,]+)\s*{escala}?", texto)
    if faixa:
        escala_min, escala_max = faixa.group(3), faixa.group(6)
        if escala_min is None and escala_max is not None:
            escala_min = escala_max  # "entre 500 e 700 mil"
        interp["preco_min"] = _para_numero(faixa.group(2), escala_min)
        interp["preco_max"] = _para_numero(faixa.group(5), escala_max)
    else:
        # "até / abaixo de / no máximo X"
        teto = re.search(
            rf"(?:ate|abaixo de|menos de|no maximo|maximo de|por ate)\s+"
            rf"(r\$?\s*)?([\d.,]+)\s*{escala}?", texto)
        if teto:
            interp["preco_max"] = _para_numero(teto.group(2), teto.group(3))
        # "acima de / a partir de X"
        piso = re.search(
            rf"(?:acima de|a partir de|mais de|minimo de)\s+"
            rf"(r\$?\s*)?([\d.,]+)\s*{escala}?", texto)
        if piso:
            interp["preco_min"] = _para_numero(piso.group(2), piso.group(3))

    # Localização
    interp["local"] = _local_conhecido(texto)

    # Palavras-chave livres (para pontuação de relevância)
    ruido = {"de", "da", "do", "com", "sem", "em", "no", "na", "para", "por",
             "e", "ou", "um", "uma", "que", "os", "as", "o", "a", "ate",
             "acima", "abaixo", "quero", "procuro", "busco", "preciso"}
    interp["termos"] = [p for p in re.findall(r"[a-z0-9]{3,}", texto)
                        if p not in ruido]
    return interp


# --------------------------------------------------------------------------- #
# Busca + pontuação de relevância
# --------------------------------------------------------------------------- #
def _texto_imovel(imovel: dict) -> str:
    return _norm(" ".join(str(imovel.get(c, "")) for c in (
        "titulo", "tipo", "operacao", "cidade", "bairro", "descricao")))


def _atende(imovel: dict, crit: dict) -> bool:
    if crit.get("tipo") and imovel["tipo"] != crit["tipo"]:
        return False
    if crit.get("operacao") and imovel["operacao"] != crit["operacao"]:
        return False
    if crit.get("local"):
        alvo = _norm(crit["local"])
        if alvo not in (_norm(imovel["bairro"]), _norm(imovel["cidade"])):
            return False
    if crit.get("quartos_min") and imovel["quartos"] < crit["quartos_min"]:
        return False
    if crit.get("vagas_min") is not None and imovel["vagas"] < crit["vagas_min"]:
        return False
    if crit.get("area_min") and imovel["area_m2"] < crit["area_min"]:
        return False
    if crit.get("preco_max") and imovel["preco"] > crit["preco_max"]:
        return False
    if crit.get("preco_min") and imovel["preco"] < crit["preco_min"]:
        return False
    return True


def _pontuar(imovel: dict, crit: dict, termos: list[str]) -> tuple[int, list[str]]:
    pontos = 40  # base por ser compatível com os filtros
    razoes: list[str] = []

    if crit.get("local") and _norm(crit["local"]) in (
            _norm(imovel["bairro"]), _norm(imovel["cidade"])):
        pontos += 15
        razoes.append(f"em {imovel['bairro']}")
    if crit.get("tipo"):
        pontos += 10
        razoes.append(f"é {imovel['tipo']}")
    if crit.get("quartos_min"):
        pontos += 10
        razoes.append(f"{imovel['quartos']} quartos")

    texto = _texto_imovel(imovel)
    acertos = [t for t in termos if t in texto]
    pontos += min(len(acertos) * 5, 25)
    if acertos:
        razoes.append("combina com " + ", ".join(acertos[:4]))

    return min(pontos, 100), razoes


def _filtros_de(interp: dict, filtros: dict | None) -> dict:
    """Combina o que a IA interpretou com filtros explícitos da interface."""
    crit = dict(_VAZIO)
    for chave in _VAZIO:
        valor = interp.get(chave)
        if valor is not None:
            crit[chave] = valor
    for chave, valor in (filtros or {}).items():
        if chave in _VAZIO and valor not in (None, "", "0"):
            if chave in ("preco_min", "preco_max", "area_min"):
                try:
                    crit[chave] = float(valor)
                except (TypeError, ValueError):
                    continue
            elif chave in ("quartos_min", "vagas_min"):
                try:
                    crit[chave] = int(valor)
                except (TypeError, ValueError):
                    continue
            else:
                crit[chave] = valor
    return crit


def buscar(consulta: str = "", filtros: dict | None = None,
           limite: int = 12) -> dict:
    """Executa a busca avançada e devolve resultados explicados."""
    interp = interpretar(consulta)
    crit = _filtros_de(interp, filtros)

    exatos = [i for i in CATALOGO if _atende(i, crit)]
    relaxado = False
    candidatos = exatos

    if not candidatos and any(crit.get(k) for k in
                              ("quartos_min", "vagas_min", "area_min",
                               "preco_max", "preco_min")):
        # IA relaxa os critérios numéricos quando não há resultado exato.
        relaxado = True
        crit_frouxo = {k: (None if k in ("quartos_min", "vagas_min",
                                          "area_min", "preco_max",
                                          "preco_min") else v)
                       for k, v in crit.items()}
        candidatos = [i for i in CATALOGO if _atende(i, crit_frouxo)]

    resultados = []
    for imovel in candidatos:
        relevancia, razoes = _pontuar(imovel, crit, interp["termos"])
        item = dict(imovel)
        item["relevancia"] = relevancia
        item["razoes"] = razoes
        resultados.append(item)

    resultados.sort(key=lambda i: (i["relevancia"], -i["preco"]), reverse=True)
    return {
        "consulta": interp["texto"],
        "interpretacao": {k: v for k, v in crit.items() if v is not None},
        "termos": interp["termos"],
        "total": len(candidatos),
        "relaxado": relaxado,
        "resultados": resultados[:limite],
    }


def localidades() -> list[str]:
    """Bairros e cidades disponíveis, para os filtros da interface."""
    valores = {i["bairro"] for i in CATALOGO} | {i["cidade"] for i in CATALOGO}
    return sorted(valores)


def tipos() -> list[str]:
    return sorted({i["tipo"] for i in CATALOGO})


if __name__ == "__main__":  # pequeno teste manual
    from pprint import pprint
    pprint(buscar("casa com 3 quartos até 1 milhão em Campinas"))
