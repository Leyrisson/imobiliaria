#!/usr/bin/env python3
"""Gestão de condomínios da Imobiliaria.

Este módulo é importado por ``app.py`` — não é um servidor. Ele implementa a
plataforma de **gestão de condomínios** em três frentes:

* **Coleta de dados**: ``CONDOMINIOS`` reúne o cadastro de cada edifício e o
  estado de suas unidades (ocupação, contratos, inadimplência); ``coletar``
  registra novas leituras enviadas pela interface.
* **Análise de rotatividade**: ``analisar_rotatividade`` mede a entrada e a
  saída de moradores, o tempo médio de permanência, a vacância e as saídas
  previstas pelos contratos que vencem.
* **Planejamento de manutenção**: ``planejar_manutencao`` prioriza os serviços
  preventivos e corretivos, aponta atrasos e monta o cronograma e o custo
  previsto.

Sem dependências externas: apenas a biblioteca padrão do Python, para
funcionar 100% offline, sem chaves nem nuvem.
"""

from __future__ import annotations

import unicodedata
from datetime import date, datetime

# --------------------------------------------------------------------------- #
# Catálogo de condomínios (coleta de dados)
# --------------------------------------------------------------------------- #
_MORADORES = (
    "Família Almeida", "Família Barros", "Família Castro", "Família Duarte",
    "Família Esteves", "Família Fonseca", "Família Godoy", "Família Henriques",
    "Família Iglesias", "Família Junqueira", "Família Klein", "Família Lopes",
    "Família Machado", "Família Nogueira", "Família Oliveira", "Família Prado",
    "Família Queiroz", "Família Ramos", "Família Siqueira", "Família Teixeira",
)

_CONDOMINIOS_BASE: list[dict] = [
    {"id": 1, "nome": "Edifício Aurora", "endereco": "Rua Harmonia, 320",
     "bairro": "Vila Madalena", "cidade": "São Paulo", "ano_construcao": 2008,
     "unidades": 48, "taxa_condominial_media": 780, "unidades_por_andar": 6,
     "sindico": "Marcos Tavares", "administradora": "Gestora Prime",
     "perfil": "residencial",
     "manutencoes": [
         {"item": "Revisão anual dos elevadores", "categoria": "preventiva",
          "criticidade": "alta", "ultima_execucao": "2025-03-10",
          "intervalo_meses": 12, "custo_estimado": 4200},
         {"item": "Limpeza e pintura da fachada", "categoria": "preventiva",
          "criticidade": "media", "ultima_execucao": "2022-06-01",
          "intervalo_meses": 60, "custo_estimado": 38000},
         {"item": "Inspeção da bomba d'água", "categoria": "preventiva",
          "criticidade": "alta", "ultima_execucao": "2026-01-15",
          "intervalo_meses": 6, "custo_estimado": 900},
         {"item": "Reparo do portão de garagem", "categoria": "corretiva",
          "criticidade": "media", "ultima_execucao": "2025-11-20",
          "intervalo_meses": 12, "custo_estimado": 2600},
         {"item": "Desinsetização das áreas comuns", "categoria": "preventiva",
          "criticidade": "baixa", "ultima_execucao": "2026-05-05",
          "intervalo_meses": 12, "custo_estimado": 1400},
     ]},
    {"id": 2, "nome": "Residencial Bosque Verde", "endereco": "Av. das Acácias, 1500",
     "bairro": "Barra da Tijuca", "cidade": "Rio de Janeiro",
     "ano_construcao": 2015, "unidades": 120, "taxa_condominial_media": 950,
     "unidades_por_andar": 8, "sindico": "Renata Coelho",
     "administradora": "Condomax", "perfil": "residencial",
     "manutencoes": [
         {"item": "Manutenção das piscinas", "categoria": "preventiva",
          "criticidade": "alta", "ultima_execucao": "2026-07-01",
          "intervalo_meses": 3, "custo_estimado": 3200},
         {"item": "Revisão das câmeras de segurança", "categoria": "preventiva",
          "criticidade": "alta", "ultima_execucao": "2025-10-01",
          "intervalo_meses": 12, "custo_estimado": 5400},
         {"item": "Troca do quadro elétrico", "categoria": "corretiva",
          "criticidade": "alta", "ultima_execucao": "2023-02-01",
          "intervalo_meses": 48, "custo_estimado": 22000},
         {"item": "Jardins e paisagismo", "categoria": "preventiva",
          "criticidade": "baixa", "ultima_execucao": "2026-09-01",
          "intervalo_meses": 2, "custo_estimado": 1800},
     ]},
    {"id": 3, "nome": "Edifício Monumental", "endereco": "Rua XV de Novembro, 88",
     "bairro": "Centro", "cidade": "Curitiba", "ano_construcao": 1998,
     "unidades": 36, "taxa_condominial_media": 640, "unidades_por_andar": 4,
     "sindico": "Paulo Meireles", "administradora": "Gestora Prime",
     "perfil": "misto",
     "manutencoes": [
         {"item": "Retrofit da instalação hidráulica", "categoria": "corretiva",
          "criticidade": "alta", "ultima_execucao": "2016-04-01",
          "intervalo_meses": 120, "custo_estimado": 65000},
         {"item": "Revisão do telhado", "categoria": "preventiva",
          "criticidade": "media", "ultima_execucao": "2024-03-01",
          "intervalo_meses": 36, "custo_estimado": 12000},
         {"item": "Repintura das escadas", "categoria": "preventiva",
          "criticidade": "baixa", "ultima_execucao": "2025-08-15",
          "intervalo_meses": 24, "custo_estimado": 4600},
     ]},
    {"id": 4, "nome": "Condomínio Villa Cambuí", "endereco": "Rua Coronel Quirino, 410",
     "bairro": "Cambuí", "cidade": "Campinas", "ano_construcao": 2019,
     "unidades": 24, "taxa_condominial_media": 1100, "unidades_por_andar": 4,
     "sindico": "Juliana Prado", "administradora": "Condomax",
     "perfil": "residencial",
     "manutencoes": [
         {"item": "Manutenção do gerador", "categoria": "preventiva",
          "criticidade": "alta", "ultima_execucao": "2026-04-01",
          "intervalo_meses": 6, "custo_estimado": 3800},
         {"item": "Limpeza das caixas de gordura", "categoria": "preventiva",
          "criticidade": "media", "ultima_execucao": "2026-02-01",
          "intervalo_meses": 6, "custo_estimado": 1200},
         {"item": "Revisão do portão social", "categoria": "corretiva",
          "criticidade": "media", "ultima_execucao": "2026-01-20",
          "intervalo_meses": 12, "custo_estimado": 1900},
     ]},
]


def _iso_para_data(texto: str) -> date:
    return datetime.strptime(texto, "%Y-%m-%d").date()


def _soma_meses(referencia: date, meses: int) -> date:
    total = referencia.month - 1 + meses
    ano = referencia.year + total // 12
    mes = total % 12 + 1
    dia = min(referencia.day, 28)
    return date(ano, mes, dia)


def _gerar_unidades(condominio: dict) -> list[dict]:
    """Materializa as unidades do edifício de forma determinística.

    Distribui ocupação, contratos e inadimplência a partir de um padrão
    derivado do ``id`` do condomínio, para que a demonstração seja rica e
    reproduzível sem depender de banco de dados.
    """
    hoje = date.today()
    total = condominio["unidades"]
    por_andar = condominio.get("unidades_por_andar", 4)
    base_vacancia = (condominio["id"] % 3) * 0.04 + 0.06
    unidades: list[dict] = []
    for indice in range(total):
        numero = f"{(indice // por_andar) + 1:02d}{indice % por_andar + 1:02d}"
        ocupada = (indice * 7 + condominio["id"] * 3) % 100 >= int(base_vacancia * 100)
        em_obra = not ocupada and (indice % 11 == 0)
        idade_contrato = (indice * 5 + condominio["id"] * 2) % 36
        entrada = _soma_meses(hoje, -idade_contrato - 1)
        duracao = 12 + (indice % 3) * 6
        contrato_fim = _soma_meses(entrada, duracao)
        situacao = "em_obra" if em_obra else ("ocupado" if ocupada else "vago")
        morador = None
        if ocupada:
            morador = _MORADORES[(indice * 3 + condominio["id"]) % len(_MORADORES)]
        inadimplente = ocupada and (indice * 13 + condominio["id"]) % 23 == 0
        saida = None
        if not ocupada and not em_obra:
            saida = _soma_meses(hoje, -((indice * 2 + condominio["id"]) % 14) - 1)
        unidades.append({
            "numero": numero,
            "area_m2": 40 + (indice % 8) * 15,
            "valor_aluguel": condominio["taxa_condominial_media"] * 4 + (indice % 5) * 180,
            "situacao": situacao,
            "morador": morador,
            "entrada": entrada.isoformat() if ocupada else None,
            "saida": saida.isoformat() if saida else None,
            "contrato_fim": contrato_fim.isoformat() if ocupada else None,
            "inadimplente": inadimplente,
        })
    return unidades


def _montar() -> list[dict]:
    condominios: list[dict] = []
    for base in _CONDOMINIOS_BASE:
        condominio = dict(base)
        condominio["unidades_detalhe"] = _gerar_unidades(base)
        condominios.append(condominio)
    return condominios


CONDOMINIOS: list[dict] = _montar()

# Registro de coletas enviadas pela interface (memória do processo).
_COLETAS: list[dict] = []


def _norm(texto: str) -> str:
    texto = unicodedata.normalize("NFKD", str(texto or ""))
    return "".join(c for c in texto if not unicodedata.combining(c)).lower()


def _brl(valor) -> str:
    if valor in (None, ""):
        return "—"
    inteiro = f"{int(round(float(valor))):,}".replace(",", ".")
    return f"R$ {inteiro}"


def _media(valores: list) -> float:
    limpos = [float(v) for v in valores if v not in (None, "")]
    return sum(limpos) / len(limpos) if limpos else 0.0


def _achar(condominio_id) -> dict | None:
    for condominio in CONDOMINIOS:
        if str(condominio["id"]) == str(condominio_id):
            return condominio
    return None


# --------------------------------------------------------------------------- #
# Rotatividade
# --------------------------------------------------------------------------- #
def analisar_rotatividade(condominio_id) -> dict:
    """Mede a entrada e a saída de moradores e o risco de vacância."""
    condominio = _achar(condominio_id)
    if not condominio:
        raise ValueError(f"condomínio {condominio_id} não encontrado")

    hoje = date.today()
    limite_12m = _soma_meses(hoje, -12)
    limite_90d = _soma_meses(hoje, 3)
    unidades = condominio["unidades_detalhe"]

    ocupadas = [u for u in unidades if u["situacao"] == "ocupado"]
    vagas = [u for u in unidades if u["situacao"] == "vago"]
    em_obra = [u for u in unidades if u["situacao"] == "em_obra"]

    saidas_12m = [u for u in unidades
                  if u["saida"] and _iso_para_data(u["saida"]) >= limite_12m]
    entradas_12m = [u for u in ocupadas
                    if u["entrada"] and _iso_para_data(u["entrada"]) >= limite_12m]

    permanencias: list[float] = []
    for unidade in unidades:
        if not unidade["entrada"]:
            continue
        inicio = _iso_para_data(unidade["entrada"])
        fim = _iso_para_data(unidade["saida"]) if unidade["saida"] else hoje
        permanencias.append((fim - inicio).days / 30.4)

    vencendo = [u for u in ocupadas
                if u["contrato_fim"]
                and hoje <= _iso_para_data(u["contrato_fim"]) <= limite_90d]

    inadimplentes = [u for u in ocupadas if u["inadimplente"]]

    total = len(unidades)
    taxa_rotatividade = (len(saidas_12m) / total * 100) if total else 0.0
    taxa_vacancia = (len(vagas) / total * 100) if total else 0.0

    if taxa_rotatividade >= 25 or taxa_vacancia >= 15:
        risco = "alto"
    elif taxa_rotatividade >= 12 or taxa_vacancia >= 7:
        risco = "medio"
    else:
        risco = "baixo"

    return {
        "condominio_id": condominio["id"],
        "total_unidades": total,
        "ocupadas": len(ocupadas),
        "vagas": len(vagas),
        "em_obra": len(em_obra),
        "taxa_ocupacao_pct": round((len(ocupadas) / total * 100) if total else 0, 1),
        "entradas_12m": len(entradas_12m),
        "saidas_12m": len(saidas_12m),
        "rotatividade_pct": round(taxa_rotatividade, 1),
        "vacancia_pct": round(taxa_vacancia, 1),
        "permanencia_media_meses": round(_media(permanencias), 1),
        "contratos_vencendo_90d": len(vencendo),
        "inadimplencia_pct": round((len(inadimplentes) / len(ocupadas) * 100)
                                   if ocupadas else 0, 1),
        "risco_vacancia": risco,
        "vencendo": [
            {"numero": u["numero"], "morador": u["morador"],
             "contrato_fim": u["contrato_fim"]}
            for u in sorted(vencendo, key=lambda x: x["contrato_fim"])[:8]
        ],
        "saidas": [
            {"numero": u["numero"], "saida": u["saida"],
             "dias_vago": (hoje - _iso_para_data(u["saida"])).days}
            for u in sorted(saidas_12m, key=lambda x: x["saida"], reverse=True)[:8]
        ],
    }


# --------------------------------------------------------------------------- #
# Planejamento de manutenção
# --------------------------------------------------------------------------- #
_CRITICIDADE_PESO = {"alta": 45, "media": 26, "baixa": 12}


def _avaliar_manutencao(item: dict, hoje: date) -> dict:
    ultima = _iso_para_data(item["ultima_execucao"])
    proxima = _soma_meses(ultima, item["intervalo_meses"])
    atraso_meses = round((hoje - proxima).days / 30.4, 1)
    if atraso_meses > 1:
        status = "atrasada"
    elif atraso_meses > -1:
        status = "a_vencer"
    else:
        status = "em_dia"

    score = _CRITICIDADE_PESO.get(item["criticidade"], 10)
    score += min(max(atraso_meses, 0) * 8, 40)
    score += min(item["custo_estimado"] / 2000, 15)
    if item["categoria"] == "corretiva":
        score += 6
    score = int(max(5, min(round(score), 100)))

    return {
        "item": item["item"],
        "categoria": item["categoria"],
        "criticidade": item["criticidade"],
        "ultima_execucao": item["ultima_execucao"],
        "proxima_prevista": proxima.isoformat(),
        "atraso_meses": atraso_meses,
        "status": status,
        "custo_estimado": item["custo_estimado"],
        "prioridade": score,
    }


def planejar_manutencao(condominio_id) -> dict:
    """Prioriza os serviços, marca atrasos e monta cronograma e custo."""
    condominio = _achar(condominio_id)
    if not condominio:
        raise ValueError(f"condomínio {condominio_id} não encontrado")

    hoje = date.today()
    itens = [_avaliar_manutencao(m, hoje) for m in condominio["manutencoes"]]
    itens.sort(key=lambda i: i["prioridade"], reverse=True)

    for posicao, item in enumerate(itens):
        item["ordem"] = posicao + 1
        item["janela"] = _janela(hoje, posicao)

    custo_total = sum(i["custo_estimado"] for i in itens)
    atrasadas = [i for i in itens if i["status"] == "atrasada"]

    return {
        "condominio_id": condominio["id"],
        "total_itens": len(itens),
        "atrasadas": len(atrasadas),
        "custo_previsto": custo_total,
        "custo_por_unidade": round(custo_total / condominio["unidades"])
        if condominio["unidades"] else 0,
        "cronograma": itens,
        "recomendacao": _recomendar(itens, atrasadas),
    }


def _janela(hoje: date, posicao: int) -> str:
    mes_base = hoje.month - 1 + posicao
    ano = hoje.year + mes_base // 12
    mes = mes_base % 12 + 1
    return f"{ano}-{mes:02d}"


def _recomendar(itens: list[dict], atrasadas: list[dict]) -> str:
    if not itens:
        return "Nenhum serviço de manutenção cadastrado."
    if atrasadas:
        nomes = ", ".join(i["item"] for i in atrasadas[:2])
        return (f"Priorizar {len(atrasadas)} serviço(s) atrasado(s) — "
                f"começando por {nomes} — antes dos preventivos em dia.")
    critico = itens[0]
    return (f"Manutenção em ordem; iniciar por “{critico['item']}” "
            f"(prioridade {critico['prioridade']}).")


# --------------------------------------------------------------------------- #
# Visões agregadas
# --------------------------------------------------------------------------- #
def _resumo(condominio: dict) -> dict:
    rot = analisar_rotatividade(condominio["id"])
    man = planejar_manutencao(condominio["id"])
    return {
        "id": condominio["id"],
        "nome": condominio["nome"],
        "endereco": condominio["endereco"],
        "bairro": condominio["bairro"],
        "cidade": condominio["cidade"],
        "perfil": condominio["perfil"],
        "ano_construcao": condominio["ano_construcao"],
        "total_unidades": condominio["unidades"],
        "taxa_condominial_media": condominio["taxa_condominial_media"],
        "ocupacao_pct": rot["taxa_ocupacao_pct"],
        "rotatividade_pct": rot["rotatividade_pct"],
        "risco_vacancia": rot["risco_vacancia"],
        "manutencoes_atrasadas": man["atrasadas"],
        "custo_manutencao_previsto": man["custo_previsto"],
        "recomendacao": man["recomendacao"],
    }


def listar() -> list[dict]:
    return [_resumo(c) for c in CONDOMINIOS]


def detalhar(condominio_id) -> dict:
    """Ficha completa: cadastro + rotatividade + plano de manutenção."""
    condominio = _achar(condominio_id)
    if not condominio:
        raise ValueError(f"condomínio {condominio_id} não encontrado")
    return {
        "condominio": _resumo(condominio),
        "rotatividade": analisar_rotatividade(condominio["id"]),
        "manutencao": planejar_manutencao(condominio["id"]),
        "unidades": condominio["unidades_detalhe"],
        "sindico": condominio["sindico"],
        "administradora": condominio["administradora"],
    }


def resumo_geral() -> dict:
    """Indicadores consolidados da carteira de condomínios."""
    fichas = listar()
    total_unidades = sum(f["total_unidades"] for f in fichas)
    custo_total = sum(f["custo_manutencao_previsto"] for f in fichas)
    atrasadas = sum(f["manutencoes_atrasadas"] for f in fichas)
    rotatividade = _media([f["rotatividade_pct"] for f in fichas])
    ocupacao = _media([f["ocupacao_pct"] for f in fichas])
    altos = [f["nome"] for f in fichas if f["risco_vacancia"] == "alto"]
    return {
        "condominios": len(fichas),
        "total_unidades": total_unidades,
        "ocupacao_media_pct": round(ocupacao, 1),
        "rotatividade_media_pct": round(rotatividade, 1),
        "manutencoes_atrasadas": atrasadas,
        "custo_manutencao_previsto": custo_total,
        "risco_alto": altos,
    }


def coletar(registro: dict | None = None) -> dict:
    """Registra uma coleta de dados vinda da interface.

    Aceita ``condominio_id``, ``tipo`` (ocupacao/manutencao/contrato) e
    ``valor``; guarda a leitura em memória e devolve o estado atualizado.
    """
    registro = registro or {}
    condominio_id = registro.get("condominio_id")
    condominio = _achar(condominio_id)
    if not condominio:
        raise ValueError("informe um condomínio válido para a coleta")
    tipo = _norm(registro.get("tipo") or "ocupacao")
    if tipo not in ("ocupacao", "manutencao", "contrato"):
        tipo = "ocupacao"
    leitura = {
        "condominio_id": condominio["id"],
        "condominio": condominio["nome"],
        "tipo": tipo,
        "valor": str(registro.get("valor") or "").strip(),
        "observacao": str(registro.get("observacao") or "").strip(),
        "coletado_em": datetime.now().astimezone().strftime("%Y-%m-%d %H:%M"),
    }
    _COLETAS.append(leitura)
    return {
        "ok": True,
        "leitura": leitura,
        "total_coletas": len(_COLETAS),
        "resumo": resumo_geral(),
    }


def coletas_recentes(limite: int = 10) -> list[dict]:
    return list(reversed(_COLETAS))[:limite]


def opcoes() -> dict:
    """Listas para os formulários da interface."""
    return {
        "condominios": [
            {"id": c["id"], "nome": c["nome"], "cidade": c["cidade"],
             "unidades": c["unidades"]}
            for c in CONDOMINIOS
        ],
        "tipos_coleta": [
            {"id": "ocupacao", "nome": "Ocupação"},
            {"id": "manutencao", "nome": "Manutenção"},
            {"id": "contrato", "nome": "Contrato"},
        ],
    }


if __name__ == "__main__":  # pequeno teste manual
    from pprint import pprint
    pprint(resumo_geral())
    pprint(analisar_rotatividade(1))
    pprint(planejar_manutencao(1)["recomendacao"])
