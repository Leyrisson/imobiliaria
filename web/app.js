"use strict";

const moeda = new Intl.NumberFormat("pt-BR", {
  style: "currency", currency: "BRL", maximumFractionDigits: 0,
});

async function api(caminho) {
  const resp = await fetch(caminho, { headers: { "Accept": "application/json" } });
  if (!resp.ok) throw new Error("falha na requisição: " + resp.status);
  return resp.json();
}

async function carregarEstado() {
  const badge = document.getElementById("status-app");
  try {
    const estado = await api("/api/estado");
    badge.textContent = `${estado.app} v${estado.versao} · busca com IA no ar`;
  } catch (err) {
    badge.textContent = "offline";
    console.error(err);
  }
}

async function carregarFiltros() {
  try {
    const { tipos, localidades } = await api("/api/filtros");
    const selTipo = document.getElementById("f-tipo");
    const selLocal = document.getElementById("f-local");
    tipos.forEach((t) => selTipo.append(new Option(t, t)));
    localidades.forEach((l) => selLocal.append(new Option(l, l)));
  } catch (err) {
    console.error(err);
  }
}

function valorFiltros() {
  return {
    tipo: document.getElementById("f-tipo").value,
    local: document.getElementById("f-local").value,
    quartos_min: document.getElementById("f-quartos").value,
    preco_max: document.getElementById("f-preco").value,
    operacao: document.getElementById("f-operacao").value,
  };
}

function montarCartao(imovel) {
  const card = document.createElement("article");
  card.className = "imovel";

  const selo = document.createElement("span");
  selo.className = "relevancia";
  selo.textContent = `${imovel.relevancia}% match`;
  selo.title = "Relevância calculada pela IA";

  const titulo = document.createElement("h3");
  titulo.textContent = imovel.titulo;

  const local = document.createElement("p");
  local.className = "local";
  local.textContent = `${imovel.bairro}, ${imovel.cidade} · ${imovel.operacao}`;

  const preco = document.createElement("p");
  preco.className = "preco";
  preco.textContent = moeda.format(imovel.preco) +
    (imovel.operacao === "aluguel" ? " /mês" : "");

  const atributos = document.createElement("p");
  atributos.className = "atributos";
  atributos.textContent = [
    `${imovel.quartos} quarto(s)`,
    `${imovel.banheiros} banheiro(s)`,
    `${imovel.vagas} vaga(s)`,
    `${imovel.area_m2} m²`,
    imovel.tipo,
  ].join(" · ");

  card.append(selo, titulo, local, preco, atributos);

  if (imovel.razoes && imovel.razoes.length) {
    const razoes = document.createElement("p");
    razoes.className = "razoes";
    razoes.textContent = "IA: " + imovel.razoes.join("; ") + ".";
    card.append(razoes);
  }
  return card;
}

function descreverInterpretacao(interp) {
  const partes = [];
  if (interp.tipo) partes.push(`tipo ${interp.tipo}`);
  if (interp.operacao) partes.push(`para ${interp.operacao}`);
  if (interp.local) partes.push(`em ${interp.local}`);
  if (interp.quartos_min) partes.push(`com ${interp.quartos_min}+ quartos`);
  if (interp.vagas_min) partes.push(`${interp.vagas_min}+ vagas`);
  if (interp.area_min) partes.push(`${interp.area_min}+ m²`);
  if (interp.preco_max) partes.push(`até ${moeda.format(interp.preco_max)}`);
  if (interp.preco_min) partes.push(`a partir de ${moeda.format(interp.preco_min)}`);
  return partes.length ? "Entendi: " + partes.join(", ") + "." : "";
}

function render(dados) {
  const secao = document.getElementById("resultados");
  const lista = document.getElementById("lista-imoveis");
  const resumo = document.getElementById("resumo-busca");
  const interpEl = document.getElementById("interpretacao");
  const vazio = document.getElementById("sem-resultados");

  secao.hidden = false;
  lista.replaceChildren();

  const n = dados.resultados.length;
  resumo.textContent = `${n} imóvel(is) encontrado(s)` +
    (dados.relaxado ? " — filtros numéricos relaxados pela IA" : "");
  interpEl.textContent = descreverInterpretacao(dados.interpretacao);

  if (!n) {
    vazio.hidden = false;
    return;
  }
  vazio.hidden = true;
  dados.resultados.forEach((im) => lista.append(montarCartao(im)));
}

function caminhoBusca(termo, filtros) {
  const params = new URLSearchParams();
  if (termo) params.set("q", termo);
  Object.entries(filtros).forEach(([k, v]) => { if (v) params.set(k, v); });
  return "/api/busca?" + params.toString();
}

async function procurar() {
  const aviso = document.getElementById("aviso");
  const termo = document.getElementById("campo-busca").value.trim();
  const filtros = valorFiltros();
  aviso.textContent = "";
  try {
    const dados = await api(caminhoBusca(termo, filtros));
    render(dados);
    if (dados.total === 0) {
      aviso.textContent = "Sem resultados exatos; ajuste a busca ou os filtros.";
    }
  } catch (err) {
    aviso.textContent = "Não foi possível buscar agora.";
    console.error(err);
  }
}

function ligarBusca() {
  document.getElementById("form-busca").addEventListener("submit", (ev) => {
    ev.preventDefault();
    procurar();
  });
  document.getElementById("btn-limpar").addEventListener("click", () => {
    document.getElementById("form-busca").reset();
    document.getElementById("resultados").hidden = true;
    document.getElementById("aviso").textContent = "";
  });
}

// --------------------------- Propostas de venda --------------------------- //

const rotulo = (v) => v.charAt(0).toUpperCase() + v.slice(1);

async function carregarOpcoesProposta() {
  try {
    const opcoes = await api("/api/propostas/opcoes");
    const selImovel = document.getElementById("p-imovel");
    opcoes.imoveis.forEach((im) => {
      selImovel.append(new Option(
        `${im.titulo} — ${moeda.format(im.preco)} (${im.operacao})`, im.id));
    });
    const selForma = document.getElementById("p-forma");
    opcoes.formas_pagamento.forEach((f) =>
      selForma.append(new Option(rotulo(f), f)));
    const selUrg = document.getElementById("p-urgencia");
    opcoes.urgencias.forEach((u) => selUrg.append(new Option(rotulo(u), u)));
    const selTom = document.getElementById("p-tom");
    opcoes.tons.forEach((t) => selTom.append(new Option(rotulo(t), t)));
  } catch (err) {
    console.error(err);
  }
}

function dadoProposta() {
  const numero = (id) => {
    const v = document.getElementById(id).value;
    return v === "" ? null : Number(v);
  };
  return {
    imovel_id: document.getElementById("p-imovel").value,
    tom: document.getElementById("p-tom").value || "consultivo",
    cliente: {
      nome: document.getElementById("p-nome").value.trim(),
      orcamento: numero("p-orcamento"),
      forma_pagamento: document.getElementById("p-forma").value,
      urgencia: document.getElementById("p-urgencia").value,
      preferencias: document.getElementById("p-preferencias").value.trim(),
      observacoes: document.getElementById("p-obs").value.trim(),
    },
  };
}

function bloco(titulo, no) {
  const el = document.createElement("div");
  el.className = "bloco";
  const h = document.createElement("h3");
  h.textContent = titulo;
  el.append(h, no);
  return el;
}

function lista(itens) {
  const ul = document.createElement("ul");
  itens.forEach((t) => {
    const li = document.createElement("li");
    li.textContent = t;
    ul.append(li);
  });
  return ul;
}

function graficoTendencia(serie) {
  const wrap = document.createElement("div");
  wrap.className = "serie";
  const max = Math.max(...serie.map((p) => p.preco_m2)) || 1;
  serie.forEach((p) => {
    const b = document.createElement("div");
    b.className = "barra";
    const valor = document.createElement("span");
    valor.className = "valor";
    valor.textContent = `${Math.round(p.preco_m2 / 1000)}k`;
    const coluna = document.createElement("div");
    coluna.className = "coluna";
    coluna.style.height = `${Math.max(8, (p.preco_m2 / max) * 46)}px`;
    const rotuloT = document.createElement("span");
    rotuloT.className = "rotulo";
    rotuloT.textContent = p.trimestre;
    b.append(valor, coluna, rotuloT);
    wrap.append(b);
  });
  return wrap;
}

function renderProposta(d) {
  const alvo = document.getElementById("proposta-resultado");
  alvo.replaceChildren();
  alvo.hidden = false;

  const aval = document.createElement("div");
  const conf = document.createElement("span");
  conf.className = "badge-confianca";
  conf.textContent = `confiança ${d.confianca}%`;
  const preco = document.createElement("p");
  preco.className = "preco-destaque";
  preco.textContent = moeda.format(d.avaliacao.valor_estimado);
  const faixa = document.createElement("p");
  faixa.className = "faixa";
  faixa.textContent =
    `Faixa sugerida ${moeda.format(d.avaliacao.faixa_min)} – ` +
    `${moeda.format(d.avaliacao.faixa_max)} · anunciar por ` +
    `${moeda.format(d.avaliacao.preco_anuncio_sugerido)}`;
  const detalhe = document.createElement("p");
  detalhe.className = "mercado-linha";
  detalhe.textContent =
    `Base: ${d.avaliacao.comparaveis} comparáveis (${d.avaliacao.criterio}) · ` +
    `${moeda.format(d.avaliacao.preco_m2_mercado)}/m²`;
  const resumoBloco = bloco("Avaliação da IA", preco);
  resumoBloco.querySelector("h3").append(conf);
  resumoBloco.append(faixa, detalhe);

  const m = d.mercado;
  const mercadoDiv = document.createElement("div");
  const tend = document.createElement("span");
  tend.className = `tendencia ${m.tendencia}`;
  tend.textContent = m.tendencia;
  const linha1 = document.createElement("p");
  linha1.className = "mercado-linha";
  linha1.textContent =
    `Preço/m²: ${moeda.format(m.preco_m2_medio)} · desconto médio ` +
    `${m.desconto_medio_pct}% · venda em ~${m.dias_medio_mercado} dias`;
  const linha2 = document.createElement("p");
  linha2.className = "mercado-linha";
  linha2.append(document.createTextNode(
    `Tendência do período: ${m.variacao_pct}% — `));
  linha2.append(tend);
  const linha3 = document.createElement("p");
  linha3.className = "mercado-linha";
  linha3.textContent = `Segmento: ${m.escopo} (${m.amostra} negócios)`;
  mercadoDiv.append(linha1, linha2, linha3, graficoTendencia(m.serie));

  const estrategia = document.createElement("div");
  const pE = document.createElement("p");
  pE.className = "mercado-linha";
  pE.textContent =
    `Abrir em ${moeda.format(d.estrategia.abertura)}, meta ` +
    `${moeda.format(d.estrategia.meta)}, piso ${moeda.format(d.estrategia.piso)}.`;

  const roteiro = lista(d.roteiro.map((r) => `${r.etapa}: ${r.acao}`));

  const docBloco = document.createElement("div");
  docBloco.className = "documento";
  const hDoc = document.createElement("h3");
  hDoc.textContent = "Documento da proposta";
  const pre = document.createElement("pre");
  pre.textContent = d.documento;
  docBloco.append(hDoc, pre);

  alvo.append(
    resumoBloco,
    bloco("Leitura de mercado", mercadoDiv),
    bloco("Argumentos para " + d.cliente.nome, lista(d.argumentos)),
    bloco("Estratégia de preço", estrategia),
    bloco("Concessões", lista(d.concessoes)),
    bloco("Roteiro de negociação", roteiro),
    docBloco,
  );
}

async function gerarProposta() {
  const aviso = document.getElementById("aviso-proposta");
  aviso.textContent = "";
  try {
    const resp = await fetch("/api/propostas", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(dadoProposta()),
    });
    const dados = await resp.json();
    if (!resp.ok) throw new Error(dados.erro || "falha ao gerar proposta");
    renderProposta(dados);
  } catch (err) {
    aviso.textContent = err.message || "Não foi possível gerar a proposta.";
    console.error(err);
  }
}

function ligarProposta() {
  document.getElementById("form-proposta").addEventListener("submit", (ev) => {
    ev.preventDefault();
    gerarProposta();
  });
}

// --------------------------- Gestão de condomínios --------------------------- //

const rotuloRisco = (r) =>
  ({ alto: "risco alto", medio: "risco médio", baixo: "risco baixo" }[r] || r);
const rotuloStatus = (s) =>
  ({ atrasada: "atrasada", a_vencer: "a vencer", em_dia: "em dia" }[s] || s);
const rotuloSituacao = (s) =>
  ({ ocupado: "ocupado", vago: "vago", em_obra: "em obra" }[s] || s);

let condominioAtivo = null;

function stat(rotulo, valor) {
  const el = document.createElement("div");
  el.className = "stat";
  const v = document.createElement("span");
  v.className = "stat-valor";
  v.textContent = valor;
  const r = document.createElement("span");
  r.className = "stat-rotulo";
  r.textContent = rotulo;
  el.append(v, r);
  return el;
}

function renderResumoCondo(resumo) {
  const alvo = document.getElementById("condo-resumo");
  alvo.replaceChildren(
    stat("condomínios", resumo.condominios),
    stat("unidades", resumo.total_unidades),
    stat("ocupação média", resumo.ocupacao_media_pct + "%"),
    stat("rotatividade média", resumo.rotatividade_media_pct + "%"),
    stat("manutenções atrasadas", resumo.manutencoes_atrasadas),
    stat("manutenção prevista", moeda.format(resumo.custo_manutencao_previsto)),
  );
}

function cartaoCondo(c) {
  const card = document.createElement("article");
  card.className = "condo-card" + (condominioAtivo === c.id ? " ativo" : "");

  const nome = document.createElement("h3");
  nome.textContent = c.nome;

  const risco = document.createElement("span");
  risco.className = `risco ${c.risco_vacancia}`;
  risco.textContent = rotuloRisco(c.risco_vacancia);

  const local = document.createElement("p");
  local.className = "condo-local";
  local.textContent = `${c.bairro}, ${c.cidade} · ${c.total_unidades} unidades`;

  const linha = document.createElement("p");
  linha.className = "condo-linha";
  linha.textContent =
    `Ocupação ${c.ocupacao_pct}% · rotatividade ${c.rotatividade_pct}% · ` +
    `${c.manutencoes_atrasadas} manutenção(ões) atrasada(s)`;

  const rec = document.createElement("p");
  rec.className = "condo-rec";
  rec.textContent = "IA: " + c.recomendacao;

  const btn = document.createElement("button");
  btn.className = "btn btn-claro";
  btn.type = "button";
  btn.textContent = "Abrir painel";
  btn.addEventListener("click", () => abrirCondominio(c.id));

  card.append(nome, risco, local, linha, rec, btn);
  return card;
}

function renderListaCondos(condominios) {
  const alvo = document.getElementById("lista-condos");
  alvo.replaceChildren();
  condominios.forEach((c) => alvo.append(cartaoCondo(c)));
}

function tabelaManutencao(itens) {
  const tabela = document.createElement("table");
  tabela.className = "tabela-manutencao";
  const thead = document.createElement("thead");
  const hr = document.createElement("tr");
  ["#", "Serviço", "Criticidade", "Status", "Janela", "Prior.", "Custo"]
    .forEach((t) => {
      const th = document.createElement("th");
      th.textContent = t;
      hr.append(th);
    });
  thead.append(hr);

  const tbody = document.createElement("tbody");
  itens.forEach((m) => {
    const tr = document.createElement("tr");
    const selo = document.createElement("span");
    selo.className = `status-manut ${m.status}`;
    selo.textContent = rotuloStatus(m.status);
    [m.ordem, m.item, m.criticidade, selo, m.janela, m.prioridade,
      moeda.format(m.custo_estimado)].forEach((val) => {
      const td = document.createElement("td");
      if (val instanceof Node) td.append(val);
      else td.textContent = val;
      tr.append(td);
    });
    tbody.append(tr);
  });
  tabela.append(thead, tbody);
  return tabela;
}

function renderDetalheCondo(d) {
  const alvo = document.getElementById("condo-detalhe");
  alvo.replaceChildren();
  alvo.hidden = false;

  const c = d.condominio;
  const r = d.rotatividade;
  const man = d.manutencao;

  const topo = document.createElement("div");
  topo.className = "condo-detalhe-topo";
  const h = document.createElement("h3");
  h.textContent = c.nome;
  const risco = document.createElement("span");
  risco.className = `risco ${c.risco_vacancia}`;
  risco.textContent = rotuloRisco(c.risco_vacancia);
  const sub = document.createElement("p");
  sub.textContent =
    `${c.endereco} · síndico ${d.sindico} · administradora ${d.administradora}`;
  topo.append(h, risco, sub);

  const metrics = document.createElement("div");
  metrics.className = "condo-metricas";
  metrics.append(
    stat("ocupadas", r.ocupadas),
    stat("vagas", r.vagas),
    stat("em obra", r.em_obra),
    stat("entradas 12m", r.entradas_12m),
    stat("saídas 12m", r.saidas_12m),
    stat("rotatividade", r.rotatividade_pct + "%"),
    stat("vacância", r.vacancia_pct + "%"),
    stat("permanência média", r.permanencia_media_meses + " meses"),
    stat("contratos vencendo", r.contratos_vencendo_90d),
    stat("inadimplência", r.inadimplencia_pct + "%"),
  );

  const saidasLista = lista(r.saidas.length
    ? r.saidas.map((s) =>
        `Unidade ${s.numero} — vaga há ${s.dias_vago} dia(s) (saída em ${s.saida})`)
    : ["Nenhuma saída nos últimos 12 meses."]);
  const vencLista = lista(r.vencendo.length
    ? r.vencendo.map((v) =>
        `Unidade ${v.numero} — ${v.morador} (contrato até ${v.contrato_fim})`)
    : ["Nenhum contrato vencendo em 90 dias."]);

  const manWrap = document.createElement("div");
  const manLinha = document.createElement("p");
  manLinha.className = "condo-linha";
  manLinha.textContent =
    `Custo previsto ${moeda.format(man.custo_previsto)} ` +
    `(${moeda.format(man.custo_por_unidade)}/unidade) · ` +
    `${man.atrasadas} atrasada(s)`;
  const manRec = document.createElement("p");
  manRec.className = "condo-rec";
  manRec.textContent = "Recomendação da IA: " + man.recomendacao;
  manWrap.append(manLinha, tabelaManutencao(man.cronograma), manRec);

  const unidadesLista = lista(d.unidades.map((u) =>
    `Unidade ${u.numero} — ${u.area_m2} m² · ${rotuloSituacao(u.situacao)}` +
    (u.morador ? ` · ${u.morador}` : "") +
    (u.inadimplente ? " · inadimplente" : "")));

  alvo.append(
    topo,
    bloco("Rotatividade", metrics),
    bloco("Saídas recentes", saidasLista),
    bloco("Contratos vencendo (90 dias)", vencLista),
    bloco("Plano de manutenção", manWrap),
    bloco("Unidades", unidadesLista),
  );
}

async function carregarCondominios() {
  try {
    const dados = await api("/api/condominios");
    renderResumoCondo(dados.resumo);
    renderListaCondos(dados.condominios);
  } catch (err) {
    console.error(err);
  }
}

async function abrirCondominio(id) {
  condominioAtivo = id;
  try {
    const d = await api("/api/condominios/" + id);
    await carregarCondominios();
    renderDetalheCondo(d);
  } catch (err) {
    console.error(err);
  }
}

async function carregarOpcoesColeta() {
  try {
    const opcoes = await api("/api/condominios/opcoes");
    const sel = document.getElementById("c-condo");
    opcoes.condominios.forEach((c) =>
      sel.append(new Option(`${c.nome} — ${c.cidade} (${c.unidades} un.)`, c.id)));
    const tipo = document.getElementById("c-tipo");
    opcoes.tipos_coleta.forEach((t) => tipo.append(new Option(t.nome, t.id)));
  } catch (err) {
    console.error(err);
  }
}

async function carregarColetas() {
  try {
    const { coletas } = await api("/api/condominios/coletas");
    const alvo = document.getElementById("coletas");
    if (!coletas.length) {
      alvo.hidden = true;
      return;
    }
    alvo.hidden = false;
    const h = document.createElement("h3");
    h.textContent = "Coletas recentes";
    alvo.replaceChildren(h, lista(coletas.map((c) =>
      `${c.coletado_em} · ${c.condominio} · ${c.tipo}: ${c.valor || "—"}` +
      (c.observacao ? ` — ${c.observacao}` : ""))));
  } catch (err) {
    console.error(err);
  }
}

async function registrarColeta() {
  const aviso = document.getElementById("aviso-coleta");
  aviso.textContent = "";
  const corpo = {
    condominio_id: document.getElementById("c-condo").value,
    tipo: document.getElementById("c-tipo").value,
    valor: document.getElementById("c-valor").value.trim(),
    observacao: document.getElementById("c-obs").value.trim(),
  };
  try {
    const resp = await fetch("/api/condominios/coletar", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(corpo),
    });
    const dados = await resp.json();
    if (!resp.ok) throw new Error(dados.erro || "falha ao registrar coleta");
    aviso.textContent = `Coleta registrada (${dados.total_coletas} no total).`;
    document.getElementById("form-coleta").reset();
    renderResumoCondo(dados.resumo);
    carregarColetas();
    const { condominios } = await api("/api/condominios");
    renderListaCondos(condominios);
    if (condominioAtivo) abrirCondominio(condominioAtivo);
  } catch (err) {
    aviso.textContent = err.message || "Não foi possível registrar a coleta.";
    console.error(err);
  }
}

function ligarCondominios() {
  document.getElementById("form-coleta").addEventListener("submit", (ev) => {
    ev.preventDefault();
    registrarColeta();
  });
}

document.addEventListener("DOMContentLoaded", () => {
  ligarBusca();
  carregarFiltros();
  carregarEstado();
  carregarOpcoesProposta();
  ligarProposta();
  ligarCondominios();
  carregarCondominios();
  carregarOpcoesColeta();
  carregarColetas();
});
