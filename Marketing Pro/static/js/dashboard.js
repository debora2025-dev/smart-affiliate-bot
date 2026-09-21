// Todos os gráficos aqui são HTML/CSS puro — sem dependência de CDN externo.
// Isso evita que uma rede corporativa, firewall ou antivírus bloqueando um
// script de terceiros derrube o dashboard inteiro (a causa do "localhost abre
// mas fica em branco"). Cada seção também é renderizada dentro do seu próprio
// try/catch, então uma falha isolada nunca impede as demais seções de aparecer.

const PLATFORM_LABEL = {
  meta: "Meta",
  google: "Google",
  linkedin: "LinkedIn",
  tiktok: "TikTok",
};

// Paleta categórica validada (CVD-safe) — ordem fixa, nunca ciclada.
const PLATFORM_COLOR = {
  meta: "#2a78d6", // slot 1 · blue
  google: "#eb6834", // slot 2 · orange
  linkedin: "#1baf7a", // slot 3 · aqua
  tiktok: "#eda100", // slot 4 · yellow
};

function fmtCurrency(value) {
  return (value || 0).toLocaleString("pt-BR", { style: "currency", currency: "BRL" });
}

function fmtDateTime(iso) {
  return new Date(iso).toLocaleString("pt-BR", { day: "2-digit", month: "2-digit", hour: "2-digit", minute: "2-digit" });
}

function el(tag, attrs = {}, children = []) {
  const node = document.createElement(tag);
  for (const [key, value] of Object.entries(attrs)) {
    if (key === "className") node.className = value;
    else node.setAttribute(key, value);
  }
  for (const child of children) node.appendChild(typeof child === "string" ? document.createTextNode(child) : child);
  return node;
}

function renderStatus(statusMap) {
  const container = document.getElementById("platform-status");
  container.innerHTML = "";
  Object.entries(statusMap).forEach(([key, info]) => {
    const chip = el("span", { className: "status-chip" });
    chip.innerHTML = `<span class="status-dot ${info.connected ? "connected" : "demo"}"></span>${PLATFORM_LABEL[key] || key} · ${info.connected ? "API real" : "demo"}`;
    container.appendChild(chip);
  });
}

function renderKpis(data) {
  const kpis = [
    { label: "Leads recebidos (30d)", value: data.prospeccao.total_leads_recebidos },
    { label: "Taxa de qualificação", value: `${data.prospeccao.taxa_qualificacao_pct}%` },
    { label: "Taxa de fechamento", value: `${data.funil_fechamento.taxa_fechamento_pct}%` },
    { label: "Receita fechada", value: fmtCurrency(data.vendas.receita_total) },
    { label: "Pipeline em proposta", value: fmtCurrency(data.vendas.pipeline_em_proposta) },
    { label: "Reuniões (7 dias)", value: data.calendario.compromissos_proximos_7_dias },
  ];
  const row = document.getElementById("kpi-row");
  row.innerHTML = "";
  kpis.forEach((kpi) => {
    row.appendChild(
      el("div", { className: "kpi-card" }, [
        el("div", { className: "kpi-label" }, [kpi.label]),
        el("div", { className: "kpi-value" }, [String(kpi.value)]),
      ])
    );
  });
}

// Barras horizontais (usadas no funil: uma série, valores em ordem decrescente).
function renderHorizontalBars(containerId, rows, valueFormatter = (v) => String(v)) {
  const container = document.getElementById(containerId);
  container.innerHTML = "";
  const max = Math.max(1, ...rows.map((r) => r.value));
  rows.forEach((row) => {
    const pct = Math.max(2, Math.round((row.value / max) * 100));
    const bar = el("div", { className: "bar-row", title: `${row.label}: ${valueFormatter(row.value)}` }, [
      el("span", { className: "bar-label" }, [row.label]),
      el("div", { className: "bar-track" }, [el("div", { className: "bar-fill", style: `width:${pct}%` })]),
      el("span", { className: "bar-value" }, [valueFormatter(row.value)]),
    ]);
    container.appendChild(bar);
  });
}

function renderFunnelChart(funnel) {
  renderHorizontalBars(
    "chart-funnel",
    funnel.stages.map((s) => ({ label: s.label, value: s.reached_or_beyond })),
  );
}

// Barras verticais agrupadas (duas séries por categoria — prospecção por plataforma).
function renderGroupedBars(containerId, categories, series) {
  const container = document.getElementById(containerId);
  container.innerHTML = "";
  const max = Math.max(1, ...series.flatMap((s) => s.values));
  const chart = el("div", { className: "grouped-bars" });
  categories.forEach((label, idx) => {
    const barsWrap = el("div", { className: "grouped-bar-set" });
    series.forEach((s) => {
      const value = s.values[idx];
      const heightPct = Math.max(2, Math.round((value / max) * 100));
      barsWrap.appendChild(
        el("div", {
          className: "grouped-bar",
          style: `height:${heightPct}%; background:${s.color}`,
          title: `${s.label} — ${label}: ${value}`,
        })
      );
    });
    const col = el("div", { className: "grouped-bar-col" }, [barsWrap, el("div", { className: "grouped-bar-group-label" }, [label])]);
    chart.appendChild(col);
  });

  const legend = el(
    "div",
    { className: "legend-row" },
    series.map((s) => {
      const item = el("span", {});
      item.innerHTML = `<span class="legend-swatch" style="background:${s.color}"></span>${s.label}`;
      return item;
    })
  );

  container.appendChild(chart);
  container.appendChild(legend);
}

function renderProspectingChart(prospeccao) {
  const rows = prospeccao.por_plataforma;
  renderGroupedBars(
    "chart-prospecting",
    rows.map((r) => r.label),
    [
      { label: "Total de leads", color: "#4f46e5", values: rows.map((r) => r.total_leads) },
      { label: "Em prospecção ativa", color: "#c7d2fe", values: rows.map((r) => r.leads_ativos_em_prospeccao) },
    ]
  );
}

// Barra 100% empilhada + legenda (participação de cada plataforma na receita).
function renderSalesChart(vendas) {
  const container = document.getElementById("chart-sales");
  container.innerHTML = "";
  const entries = Object.entries(vendas.por_plataforma);
  const total = entries.reduce((sum, [, v]) => sum + v.receita, 0);

  if (!entries.length || total <= 0) {
    container.appendChild(el("div", { className: "chart-error" }, ["Sem vendas fechadas no período."]));
    return;
  }

  const stacked = el("div", { className: "stacked-bar" });
  entries.forEach(([key, v]) => {
    const pct = (v.receita / total) * 100;
    stacked.appendChild(
      el("div", {
        className: "stacked-segment",
        style: `width:${pct}%; background:${PLATFORM_COLOR[key] || "#999"}`,
        title: `${PLATFORM_LABEL[key] || key}: ${fmtCurrency(v.receita)} (${pct.toFixed(1)}%)`,
      })
    );
  });

  const legend = el(
    "div",
    { className: "legend-row" },
    entries.map(([key, v]) => {
      const item = el("span", {});
      item.innerHTML = `<span class="legend-swatch" style="background:${PLATFORM_COLOR[key] || "#999"}"></span>${PLATFORM_LABEL[key] || key} — ${fmtCurrency(v.receita)}`;
      return item;
    })
  );

  container.appendChild(stacked);
  container.appendChild(legend);
}

function renderRecovery(recuperacao) {
  document.getElementById("recovery-rate").textContent = `${recuperacao.taxa_recuperacao_pct}%`;
  const list = document.getElementById("recovery-list");
  list.innerHTML = "";
  recuperacao.eventos_recentes.forEach((item) => {
    const li = document.createElement("li");
    li.innerHTML = `<span>${item.lead_name}<span class="mini-sub">${item.recovery_channel}</span></span><span class="badge" style="background:${PLATFORM_COLOR[item.platform] || "#999"}">${PLATFORM_LABEL[item.platform] || item.platform}</span>`;
    list.appendChild(li);
  });
}

function renderEmails(revisao) {
  document.getElementById("email-pending").textContent = revisao.pendentes_de_revisao;
  const list = document.getElementById("email-list");
  list.innerHTML = "";
  revisao.fila_revisao.forEach((item) => {
    const li = document.createElement("li");
    li.innerHTML = `<span>${item.subject}<span class="mini-sub">${item.lead_name} · ${item.status}</span></span>`;
    list.appendChild(li);
  });
}

function renderCalendar(calendario) {
  document.getElementById("calendar-count").textContent = calendario.compromissos_proximos_7_dias;
  const list = document.getElementById("calendar-list");
  list.innerHTML = "";
  calendario.proxima_agenda.forEach((item) => {
    const li = document.createElement("li");
    li.innerHTML = `<span>${item.type}<span class="mini-sub">${item.lead_name} · ${fmtDateTime(item.starts_at)}</span></span>`;
    list.appendChild(li);
  });
}

function renderSalesTable(vendas) {
  const tbody = document.querySelector("#sales-table tbody");
  tbody.innerHTML = "";
  vendas.negocios_recentes.forEach((deal) => {
    const tr = document.createElement("tr");
    tr.innerHTML = `<td>${deal.lead_name}</td><td><span class="badge" style="background:${PLATFORM_COLOR[deal.platform] || "#999"}">${PLATFORM_LABEL[deal.platform] || deal.platform}</span></td><td>${fmtCurrency(deal.valor)}</td>`;
    tbody.appendChild(tr);
  });
}

function renderLeadsTable(leads) {
  const tbody = document.querySelector("#leads-table tbody");
  tbody.innerHTML = "";
  leads.forEach((lead) => {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${lead.name}</td>
      <td><span class="badge" style="background:${PLATFORM_COLOR[lead.platform] || "#999"}">${PLATFORM_LABEL[lead.platform] || lead.platform}</span></td>
      <td>${lead.campaign}</td>
      <td><span class="stage-pill">${lead.stage}</span></td>
      <td>${lead.score}</td>
      <td>${fmtDateTime(lead.created_at)}</td>
    `;
    tbody.appendChild(tr);
  });
}

// Roda cada seção isoladamente: se uma falhar (por exemplo, um campo inesperado
// na resposta da API), registra no console e mostra um aviso discreto no lugar
// da seção — sem impedir que o restante do dashboard renderize normalmente.
function renderSection(containerId, fn) {
  try {
    fn();
  } catch (err) {
    console.error(`Falha ao renderizar "${containerId}":`, err);
    const container = document.getElementById(containerId);
    if (container) {
      const notice = document.createElement("div");
      notice.className = "chart-error";
      notice.textContent = "Não foi possível carregar esta seção.";
      container.replaceChildren ? container.replaceChildren(notice) : (container.innerHTML = "", container.appendChild(notice));
    }
  }
}

function showLoadError(message) {
  const banner = document.getElementById("load-error");
  banner.textContent = message;
  banner.hidden = false;
}

async function loadDashboard() {
  let data;
  try {
    const response = await fetch("/api/dashboard");
    if (!response.ok) throw new Error(`Servidor respondeu ${response.status}`);
    data = await response.json();
  } catch (err) {
    console.error("Falha ao buscar /api/dashboard:", err);
    showLoadError(
      "Não foi possível carregar os dados do dashboard. Confirme se o servidor Flask (python app.py) ainda está rodando e recarregue a página."
    );
    return;
  }

  document.getElementById("generated-at").textContent = `Atualizado em ${fmtDateTime(data.gerado_em)}`;

  renderSection("platform-status", () => renderStatus(data.status_plataformas));
  renderSection("kpi-row", () => renderKpis(data));
  renderSection("chart-funnel", () => renderFunnelChart(data.funil_fechamento));
  renderSection("chart-prospecting", () => renderProspectingChart(data.prospeccao));
  renderSection("chart-sales", () => renderSalesChart(data.vendas));
  renderSection("recovery-list", () => renderRecovery(data.recuperacao_leads));
  renderSection("email-list", () => renderEmails(data.revisao_emails));
  renderSection("calendar-list", () => renderCalendar(data.calendario));
  renderSection("sales-table", () => renderSalesTable(data.vendas));
  renderSection("leads-table", () => renderLeadsTable(data.leads_recentes));
}

loadDashboard();
