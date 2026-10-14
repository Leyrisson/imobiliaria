#!/usr/bin/env python3
"""Inteligência de propostas de venda da Imobiliaria.

Este módulo é importado por ``app.py`` — não é um servidor. Ele contém a IA
local que monta **propostas de venda personalizadas** combinando dados
históricos de negociação com as tendências de mercado de cada segmento.

Peças principais:

* ``HISTORICO``: negócios passados (preço pedido, preço fechado, dias em
  mercado) por imóvel e por trimestre, derivados do ``CATALOGO``.
* ``analisar_mercado``: tendências por segmento — preço/m², desconto médio,
  tempo de venda e direção da tendência.
* ``avaliar``: avaliação comparativa (valor justo e faixa de negociação).
* ``gerar_proposta``: a proposta personalizada para um cliente.

Sem dependências externas: apenas a biblioteca padrão do Python.
"""

from __future__ import annotations

import re
import unicodedata
from datetime import datetime

import busca

CATALOGO = busca.CATALOGO

# --------------------------------------------------------------------------- #
# Histórico de negociações (dados de treino da IA)
# --------------------------------------------------------------------------- #
_QUARTIS = ("2025-T3", "2025-T4", "2026-T1")
_VALORIZACAO_TRIMESTRE = 0.011


def _arredonda(valor: float) -> int:
    return int(round(valor / 1000.0) * 1000)


def _carregar_historico() -> list[dict]:
    """Gera o histórico de negócios a partir do catálogo.

    Cada imóvel rende um registro por trimestre, com valorização crescente
    (tendência de alta) e um desconto de fechamento próprio — assim a IA
    aprende tanto o preço praticado quanto o comportamento de desconto.
    """
    registros: list[dict] = []
    for posicao, imovel in enumerate(CATALOGO):
        valorizacao = (posicao % 4) * 0.004
        desconto = 0.895 + (posicao % 6) * 0.008
        for indice, trimestre in enumerate(_QUARTIS):
            fator_tempo = 1 + (_VALORIZACAO_TRIMESTRE + valorizacao) * indice
            pedido = _arredonda(imovel["preco"] * fator_tempo)
            registros.append({
                "imovel_id": imovel["id"],
                "tipo": imovel["tipo"],
                "cidade": imovel["cidade"],
                "bairro": imovel["bairro"],
                "area_m2": imovel["area_m2"],
                "trimestre": trimestre,
                "preco_pedido": pedido,
                "preco_fechado": _arredonda(pedido * desconto),
                "dias_mercado": 30 + (posicao * 7 + indice * 11) % 55,
            })
    return registros


HISTORICO: list[dict] = _carregar_historico()

# --------------------------------------------------------------------------- #
# Utilidades
# --------------------------------------------------------------------------- #
def _norm(texto: str) -> str:
    texto = unicodedata.normalize("NFKD", str(texto or ""))
    return "".join(c for c in texto if not unicodedata.combining(c)).lower()


def _media(valores: list) -> float:
    limpos = [float(v) for v in valores if v not in (None, 0)]
    return sum(limpos) / len(limpos) if limpos else 0.0


def _brl(valor) -> str:
    if valor in (None, ""):
        return "—"
    inteiro = f"{int(round(float(valor))):,}".replace(",", ".")
    return f"R$ {inteiro}"


def _preco_m2(registro: dict) -> float | None:
    area = registro.get("area_m2") or 0
    return registro["preco_fechado"] / area if area else None


def _achar_imovel(imovel_id) -> dict | None:
    for imovel in CATALOGO:
        if str(imovel["id"]) == str(imovel_id):
            return imovel
    return None


def _ultimos_por_imovel(registros: list[dict]) -> list[dict]:
    """Mantém só o registro mais recente de cada imóvel (evita contar 3x)."""
    escolhidos: dict[int, dict] = {}
    for registro in registros:
        atual = escolhidos.get(registro["imovel_id"])
        if atual is None or registro["trimestre"] > atual["trimestre"]:
            escolhidos[registro["imovel_id"]] = registro
    return list(escolhidos.values())


# --------------------------------------------------------------------------- #
# Análise de mercado (tendências)
# --------------------------------------------------------------------------- #
def _filtrar(tipo: str | None, cidade: str | None) -> list[dict]:
    return [r for r in HISTORICO
            if (not tipo or r["tipo"] == tipo)
            and (not cidade or r["cidade"] == cidade)]


def analisar_mercado(tipo: str | None = None,
                     cidade: str | None = None) -> dict:
    """Mede o mercado de um segmento e aponta a tendência de preço."""
    segmento = _filtrar(tipo, cidade)
    escopo = "geral"
    if tipo or cidade:
        escopo = " · ".join(p for p in (tipo, cidade) if p)

    amostra = segmento
    if len(segmento) < 4:
        ampliado = _filtrar(tipo, None)
        if len(ampliado) >= len(amostra):
            amostra = ampliado
        if len(amostra) < 4:
            amostra = HISTORICO

    if not amostra:
        amostra = HISTORICO

    por_trimestre: dict[str, list[float]] = {}
    for registro in amostra:
        m2 = _preco_m2(registro)
        if m2:
            por_trimestre.setdefault(registro["trimestre"], []).append(m2)
    serie = [{"trimestre": t, "preco_m2": round(_media(por_trimestre[t]))}
             for t in sorted(por_trimestre)]

    variacao = 0.0
    if len(serie) > 1 and serie[0]["preco_m2"]:
        variacao = serie[-1]["preco_m2"] / serie[0]["preco_m2"] - 1

    if variacao > 0.01:
        tendencia = "alta"
    elif variacao < -0.01:
        tendencia = "queda"
    else:
        tendencia = "estável"

    desconto = _media([1 - r["preco_fechado"] / r["preco_pedido"]
                       for r in amostra if r["preco_pedido"]])

    return {
        "escopo": escopo,
        "amostra": len(amostra),
        "preco_m2_medio": round(_media([_preco_m2(r) for r in amostra])),
        "desconto_medio_pct": round(desconto * 100, 1),
        "dias_medio_mercado": round(_media([r["dias_mercado"] for r in amostra])),
        "tendencia": tendencia,
        "variacao_pct": round(variacao * 100, 1),
        "serie": serie,
    }


# --------------------------------------------------------------------------- #
# Avaliação comparativa
# --------------------------------------------------------------------------- #
def avaliar(imovel_id) -> dict:
    """Estima o valor justo do imóvel e a faixa de negociação."""
    imovel = _achar_imovel(imovel_id)
    if not imovel:
        raise ValueError(f"imóvel {imovel_id} não encontrado")

    comparaveis = [r for r in HISTORICO
                   if r["tipo"] == imovel["tipo"]
                   and r["cidade"] == imovel["cidade"]]
    criterio = "mesmo tipo e cidade"
    if len(comparaveis) < 3:
        alternativa = [r for r in HISTORICO if r["bairro"] == imovel["bairro"]]
        if alternativa:
            comparaveis, criterio = alternativa, "mesmo bairro"
        else:
            comparaveis = [r for r in HISTORICO if r["tipo"] == imovel["tipo"]]
            criterio = "mesmo tipo"
    comparaveis = _ultimos_por_imovel(comparaveis)
    if not comparaveis:
        comparaveis = _ultimos_por_imovel(HISTORICO)
        criterio = "mercado geral"

    preco_m2 = _media([_preco_m2(r) for r in comparaveis])
    desconto = _media([1 - r["preco_fechado"] / r["preco_pedido"]
                       for r in comparaveis if r["preco_pedido"]])
    valor_comparativo = preco_m2 * imovel["area_m2"]
    valor_estimado = _arredonda(0.65 * valor_comparativo + 0.35 * imovel["preco"])

    return {
        "imovel_id": imovel["id"],
        "valor_estimado": valor_estimado,
        "valor_comparativo": _arredonda(valor_comparativo),
        "preco_m2_mercado": round(preco_m2),
        "desconto_medio_pct": round(desconto * 100, 1),
        "preco_anuncio_sugerido": _arredonda(valor_estimado * (1 + desconto + 0.01)),
        "faixa_min": _arredonda(valor_estimado * (1 - desconto)),
        "faixa_max": _arredonda(valor_estimado * 1.02),
        "comparaveis": len(comparaveis),
        "criterio": criterio,
    }


# --------------------------------------------------------------------------- #
# Cliente
# --------------------------------------------------------------------------- #
_FORMA_PAGAMENTO = ("vista", "financiamento", "fgts", "permuta", "a definir")
_URGENCIAS = ("alta", "media", "baixa")


def _normaliza_cliente(cliente: dict | None) -> dict:
    cliente = cliente or {}
    bruto = cliente.get("orcamento")
    try:
        orcamento = float(bruto) if bruto not in (None, "") else None
    except (TypeError, ValueError):
        orcamento = None

    prefs = cliente.get("preferencias") or ""
    if isinstance(prefs, str):
        preferencias = [p.strip() for p in re.split(r"[;,]", prefs) if p.strip()]
    else:
        preferencias = [str(p).strip() for p in prefs if str(p).strip()]

    forma = _norm(cliente.get("forma_pagamento") or "a definir")
    forma = forma if forma in _FORMA_PAGAMENTO else "a definir"
    urgencia = _norm(cliente.get("urgencia") or "media")
    urgencia = urgencia if urgencia in _URGENCIAS else "media"

    return {
        "nome": (cliente.get("nome") or "Cliente").strip(),
        "orcamento": orcamento,
        "forma_pagamento": forma,
        "urgencia": urgencia,
        "preferencias": preferencias,
        "observacoes": (cliente.get("observacoes") or "").strip(),
    }


def _texto_imovel(imovel: dict) -> str:
    return _norm(" ".join(str(imovel.get(c, "")) for c in
                          ("titulo", "tipo", "bairro", "cidade", "descricao")))


def _argumentos(imovel: dict, cliente: dict, avaliacao: dict,
                mercado: dict) -> list[str]:
    argumentos: list[str] = []

    if cliente["orcamento"]:
        if imovel["preco"] <= cliente["orcamento"]:
            argumentos.append(
                f"O valor pedido ({_brl(imovel['preco'])}) cabe no orçamento "
                f"declarado de {_brl(cliente['orcamento'])}.")
        else:
            excesso = imovel["preco"] - cliente["orcamento"]
            alcance = max(0, cliente["orcamento"] - avaliacao["faixa_min"])
            argumentos.append(
                f"O valor pedido supera o orçamento em {_brl(excesso)}; a "
                f"negociação pode se aproximar de {_brl(avaliacao['faixa_min'])}"
                + (f", ao alcance do cliente." if alcance else "."))

    argumentos.append(
        f"Região {imovel['bairro']}, {imovel['cidade']}: imóveis dessa região "
        f"giram em média em {mercado['dias_medio_mercado']} dias.")

    texto = _texto_imovel(imovel)
    for pref in cliente["preferencias"]:
        if _norm(pref) in texto:
            argumentos.append(f"Atende à preferência declarada: “{pref}”.")

    argumentos.append(
        f"Preço/m² praticado no segmento é {_brl(avaliacao['preco_m2_mercado'])}; "
        f"este imóvel é anunciado a "
        f"{_brl(imovel['preco'] / imovel['area_m2'] if imovel['area_m2'] else imovel['preco'])}/m².")

    if mercado["tendencia"] == "alta":
        argumentos.append(
            f"Tendência de valorização de {mercado['variacao_pct']}% no período — "
            f"comprar agora preserva o poder de compra do cliente.")
    elif mercado["tendencia"] == "queda":
        argumentos.append(
            f"Mercado em acomodação ({mercado['variacao_pct']}%) — há espaço "
            f"para negociar condições melhores.")

    if cliente["urgencia"] == "alta":
        argumentos.append("Perfil de urgência alta: priorizar imóveis prontos "
                          "para uso imediato, sem obras.")
    return argumentos


def _concessoes(cliente: dict, avaliacao: dict, mercado: dict) -> list[str]:
    desconto = mercado["desconto_medio_pct"]
    concessoes = [
        f"Desconto de referência no segmento: até {desconto}% sobre o preço "
        f"anunciado.",
    ]
    if cliente["forma_pagamento"] == "vista":
        concessoes.append("Pagamento à vista: margem extra de negociação e "
                          "prioridade na proposta.")
    elif cliente["forma_pagamento"] == "financiamento":
        concessoes.append("Financiamento: previsibilidade de recebimento — "
                          "usar como argumento para pequeno abatimento.")
    elif cliente["forma_pagamento"] == "fgts":
        concessoes.append("Uso de FGTS na entrada: reduz o valor financiado e "
                          "facilita a aprovação.")
    elif cliente["forma_pagamento"] == "permuta":
        concessoes.append("Permuta: avaliar o bem recebido e equiparar valores.")
    concessoes.append(
        f"Meta de fechamento: {_brl(avaliacao['valor_estimado'])}; piso "
        f"aceitável {_brl(avaliacao['faixa_min'])}.")
    return concessoes


def _roteiro(imovel: dict, cliente: dict, estrategia: dict) -> list[dict]:
    return [
        {"etapa": "1. Abordagem",
         "acao": f"Apresentar {imovel['titulo']} a {cliente['nome']} destacando "
                 f"que está em {imovel['bairro']}, {imovel['cidade']}."},
        {"etapa": "2. Valor",
         "acao": f"Ancorar a conversa no valor de mercado {_brl(estrategia['valor_estimado'])} "
                 f"e abrir pedindo {_brl(estrategia['abertura'])}."},
        {"etapa": "3. Objeções",
         "acao": "Responder com os números de preço/m², tempo de venda e "
                 "tendência do segmento."},
        {"etapa": "4. Fechamento",
         "acao": f"Conduzir para {_brl(estrategia['meta'])} respeitando o piso "
                 f"de {_brl(estrategia['piso'])}."},
        {"etapa": "5. Pós-venda",
         "acao": "Registrar a negociação para alimentar a IA de propostas."},
    ]


def _documento(imovel: dict, cliente: dict, avaliacao: dict, mercado: dict,
               argumentos: list[str], concessoes: list[str],
               roteiro: list[dict], estrategia: dict, tom: str) -> str:
    linhas = [
        f"PROPOSTA DE VENDA — {imovel['titulo']}",
        f"Cliente: {cliente['nome']}",
        f"Tom: {tom}",
        "",
        "1. RESUMO",
        f"Valor de mercado estimado: {_brl(avaliacao['valor_estimado'])} "
        f"(faixa {_brl(avaliacao['faixa_min'])} – {_brl(avaliacao['faixa_max'])}).",
        f"Preço anunciado: {_brl(imovel['preco'])}.",
        "",
        "2. MERCADO",
        f"Segmento {mercado['escopo']}: preço/m² {_brl(mercado['preco_m2_medio'])}, "
        f"desconto médio {mercado['desconto_medio_pct']}%, "
        f"tempo médio {mercado['dias_medio_mercado']} dias, "
        f"tendência {mercado['tendencia']} ({mercado['variacao_pct']}%).",
        "",
        "3. ARGUMENTOS",
    ]
    linhas += [f"- {a}" for a in argumentos]
    linhas += ["", "4. CONCESSÕES E ESTRATÉGIA DE PREÇO"]
    linhas += [f"- {c}" for c in concessoes]
    linhas += ["", "5. ROTEIRO DE NEGOCIAÇÃO"]
    linhas += [f"- {r['etapa']}: {r['acao']}" for r in roteiro]
    if cliente["observacoes"]:
        linhas += ["", "6. OBSERVAÇÕES DO CLIENTE", cliente["observacoes"]]
    return "\n".join(linhas)


# --------------------------------------------------------------------------- #
# Geração da proposta
# --------------------------------------------------------------------------- #
def gerar_proposta(imovel_id, cliente: dict | None = None,
                   tom: str = "consultivo") -> dict:
    """Monta a proposta de venda personalizada e explicável.

    Retorna a avaliação, a leitura de mercado, os argumentos escolhidos para
    aquele cliente, a estratégia de preço e o documento final em texto.
    """
    imovel = _achar_imovel(imovel_id)
    if not imovel:
        raise ValueError(f"imóvel {imovel_id} não encontrado")

    perfil = _normaliza_cliente(cliente)
    mercado = analisar_mercado(imovel["tipo"], imovel["cidade"])
    avaliacao = avaliar(imovel["id"])

    argumentos = _argumentos(imovel, perfil, avaliacao, mercado)
    concessoes = _concessoes(perfil, avaliacao, mercado)
    estrategia = {
        "valor_estimado": avaliacao["valor_estimado"],
        "abertura": avaliacao["preco_anuncio_sugerido"],
        "meta": avaliacao["valor_estimado"],
        "piso": avaliacao["faixa_min"],
        "desconto_segmento_pct": mercado["desconto_medio_pct"],
    }
    roteiro = _roteiro(imovel, perfil, estrategia)

    # Confiança da IA: mais comparáveis e cliente com orçamento => mais alto.
    confianca = 55
    confianca += min(avaliacao["comparaveis"] * 6, 24)
    confianca += 10 if perfil["orcamento"] else 0
    confianca += 8 if perfil["preferencias"] else 0
    confianca = max(40, min(confianca, 97))

    return {
        "imovel": imovel,
        "cliente": perfil,
        "tom": tom,
        "avaliacao": avaliacao,
        "mercado": mercado,
        "argumentos": argumentos,
        "concessoes": concessoes,
        "estrategia": estrategia,
        "roteiro": roteiro,
        "confianca": confianca,
        "documento": _documento(imovel, perfil, avaliacao, mercado,
                                argumentos, concessoes, roteiro,
                                estrategia, tom),
        "gerado_em": datetime.now().astimezone().strftime("%Y-%m-%d %H:%M"),
    }


def opcoes() -> dict:
    """Listas para os formulários da interface."""
    return {
        "formas_pagamento": list(_FORMA_PAGAMENTO),
        "urgencias": list(_URGENCIAS),
        "tons": ["consultivo", "direto", "entusiasta"],
        "imoveis": [{"id": i["id"], "titulo": i["titulo"],
                     "cidade": i["cidade"], "operacao": i["operacao"],
                     "preco": i["preco"]} for i in CATALOGO],
    }


if __name__ == "__main__":  # pequeno teste manual
    from pprint import pprint
    pprint(gerar_proposta(
        1, {"nome": "Ana", "orcamento": 800000,
            "forma_pagamento": "vista", "preferencias": "metrô, varanda"}))
