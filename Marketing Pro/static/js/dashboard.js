const PLATFORM_LABEL = {
  meta: "Meta",
  google: "Google",
  linkedin: "LinkedIn",
  tiktok: "TikTok",
};

const PLATFORM_COLOR = {
  meta: "#1877f2",
  google: "#ea4335",
  linkedin: "#0a66c2",
  tiktok: "#25293c",
};

function fmtCurrency(value) {
  return (value || 0).toLocaleString("pt-BR", { style: "currency", currency: "BRL" });
}

function fmtDateTime(iso) {
  return new Date(iso).toLocaleString("pt-BR", { day: "2-digit", month: "2-digit", hour: "2-digit", minute: "2-digit" });
}

function renderStatus(statusMap) {
  const el = document.getElementById("platform-status");
  el.innerHTML = "";
  Object.entries(statusMap).forEach(([key, info]) => {
    const chip = document.createElement("span");
    chip.className = "status-chip";
    chip.innerHTML = `<span class="status-dot ${info.connected ? "connected" : "demo"}"></span>${PLATFORM_LABEL[key] || key} · ${info.connected ? "API real" : "demo"}`;
    el.appendChild(chip);
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
    const card = document.createElement("div");
    card.className = "kpi-card";
    card.innerHTML = `<div class="kpi-label">${kpi.label}</div><div class="kpi-value">${kpi.value}</div>`;
    row.appendChild(card);
  });
}

function renderFunnelChart(funnel) {
  new Chart(document.getElementById("chart-funnel"), {
    type: "bar",
    data: {
      labels: funnel.stages.map((s) => s.label),
      datasets: [
        {
          label: "Leads que chegaram a essa etapa (ou além)",
          data: funnel.stages.map((s) => s.reached_or_beyond),
          backgroundColor: "#4f46e5",
          borderRadius: 6,
        },
      ],
    },
    options: {
      indexAxis: "y",
      plugins: { legend: { display: false } },
      scales: { x: { beginAtZero: true, grid: { display: false } }, y: { grid: { display: false } } },
    },
  });
}

function renderProspectingChart(prospeccao) {
  const rows = prospeccao.por_plataforma;
  new Chart(document.getElementById("chart-prospecting"), {
    type: "bar",
    data: {
      labels: rows.map((r) => r.label),
      datasets: [
        {
          label: "Total de leads",
          data: rows.map((r) => r.total_leads),
          backgroundColor: rows.map((r) => PLATFORM_COLOR[r.platform]),
          borderRadius: 6,
        },
        {
          label: "Em prospecção ativa",
          data: rows.map((r) => r.leads_ativos_em_prospeccao),
          backgroundColor: "#c7d2fe",
          borderRadius: 6,
        },
      ],
    },
    options: {
      plugins: { legend: { position: "bottom" } },
      scales: { y: { beginAtZero: true, grid: { color: "#eef0f6" } }, x: { grid: { display: false } } },
    },
  });
}

function renderSalesChart(vendas) {
  const entries = Object.entries(vendas.por_plataforma);
  new Chart(document.getElementById("chart-sales"), {
    type: "doughnut",
    data: {
      labels: entries.map(([key]) => PLATFORM_LABEL[key] || key),
      datasets: [
        {
          data: entries.map(([, v]) => v.receita),
          backgroundColor: entries.map(([key]) => PLATFORM_COLOR[key]),
        },
      ],
    },
    options: { plugins: { legend: { position: "bottom" } } },
  });
}

function renderRecovery(recuperacao) {
  document.getElementById("recovery-rate").textContent = `${recuperacao.taxa_recuperacao_pct}%`;
  const list = document.getElementById("recovery-list");
  list.innerHTML = "";
  recuperacao.eventos_recentes.forEach((item) => {
    const li = document.createElement("li");
    li.innerHTML = `<span>${item.lead_name}<span class="mini-sub">${item.recovery_channel}</span></span><span class="badge ${item.platform}">${PLATFORM_LABEL[item.platform]}</span>`;
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
    tr.innerHTML = `<td>${deal.lead_name}</td><td><span class="badge ${deal.platform}">${PLATFORM_LABEL[deal.platform]}</span></td><td>${fmtCurrency(deal.valor)}</td>`;
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
      <td><span class="badge ${lead.platform}">${PLATFORM_LABEL[lead.platform]}</span></td>
      <td>${lead.campaign}</td>
      <td><span class="stage-pill">${lead.stage}</span></td>
      <td>${lead.score}</td>
      <td>${fmtDateTime(lead.created_at)}</td>
    `;
    tbody.appendChild(tr);
  });
}

async function loadDashboard() {
  const response = await fetch("/api/dashboard");
  const data = await response.json();

  document.getElementById("generated-at").textContent = `Atualizado em ${fmtDateTime(data.gerado_em)}`;
  renderStatus(data.status_plataformas);
  renderKpis(data);
  renderFunnelChart(data.funil_fechamento);
  renderProspectingChart(data.prospeccao);
  renderSalesChart(data.vendas);
  renderRecovery(data.recuperacao_leads);
  renderEmails(data.revisao_emails);
  renderCalendar(data.calendario);
  renderSalesTable(data.vendas);
  renderLeadsTable(data.leads_recentes);
}

loadDashboard();
