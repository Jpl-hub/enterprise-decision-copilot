async function submitAgentQuestion(event) {
    event.preventDefault();
    const input = document.getElementById("agent-question");
    const result = document.getElementById("agent-result");
    const question = input.value.trim();

    if (!question) {
        result.classList.remove("empty");
        result.innerHTML = "<p>请输入问题。</p>";
        return;
    }

    result.classList.remove("empty");
    result.innerHTML = "<p>正在分析...</p>";

    const response = await fetch("/api/agent/query", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question }),
    });

    if (!response.ok) {
        result.innerHTML = "<p>请求失败，请稍后重试。</p>";
        return;
    }

    const data = await response.json();
    renderResult(result, data);
}

function renderResult(container, data) {
    const highlights = (data.highlights || []).map((item) => `<li>${item}</li>`).join("");
    const suggested = (data.suggested_questions || []).join(" / ");
    const evidence = renderEvidence(data.evidence);
    const trace = renderTrace(data.trace);
    container.innerHTML = `
        <h3>${data.title}</h3>
        <p>${data.summary}</p>
        <ul>${highlights}</ul>
        ${evidence}
        ${trace}
        ${suggested ? `<p><strong>建议继续：</strong>${suggested}</p>` : ""}
    `;
}

function renderEvidence(evidence) {
    if (!evidence) {
        return "";
    }
    const rows = [];
    const queryTerms = (evidence.query_terms || []).map((item) => `<span class="query-term-chip">${item}</span>`).join("");
    if (evidence.financial_source_url) {
        rows.push(`<li><a href="${evidence.financial_source_url}" target="_blank" rel="noreferrer">财报原文</a></li>`);
    }
    for (const item of evidence.research_reports || []) {
        rows.push(`<li><a href="${item.source_url}" target="_blank" rel="noreferrer">${item.report_date} ${item.institution}：${item.title}</a></li>`);
    }
    for (const item of evidence.industry_reports || []) {
        rows.push(`<li><a href="${item.source_url}" target="_blank" rel="noreferrer">${item.report_date} ${item.industry_name}：${item.title}</a></li>`);
    }
    for (const item of evidence.semantic_stock_reports || []) {
        rows.push(`<li><a href="${item.source_url}" target="_blank" rel="noreferrer">${item.report_date} ${item.institution}：${item.title}（证据召回）</a>${item.matched_excerpt ? `<div class="evidence-snippet">${item.matched_excerpt}</div>` : ""}${item.rerank_score !== undefined ? `<div class="evidence-meta">重排分 ${item.rerank_score}</div>` : ""}</li>`);
    }
    for (const item of evidence.semantic_industry_reports || []) {
        rows.push(`<li><a href="${item.source_url}" target="_blank" rel="noreferrer">${item.report_date} ${item.industry_name}：${item.title}（证据召回）</a>${item.matched_excerpt ? `<div class="evidence-snippet">${item.matched_excerpt}</div>` : ""}${item.rerank_score !== undefined ? `<div class="evidence-meta">重排分 ${item.rerank_score}</div>` : ""}</li>`);
    }
    if (!rows.length && !queryTerms) {
        return "";
    }
    return `<div class="evidence-box"><strong>来源追溯</strong>${queryTerms ? `<div class="query-term-list"><span>命中主题词</span>${queryTerms}</div>` : ""}<ul>${rows.join("")}</ul></div>`;
}

function renderTrace(trace) {
    if (!trace || !trace.length) {
        return "";
    }
    const rows = trace
        .map((item) => `<li><strong>${item.step}</strong><span>${item.detail}</span></li>`)
        .join("");
    return `<div class="trace-box"><strong>执行轨迹</strong><ul>${rows}</ul></div>`;
}

function renderReport(container, data) {
    const sections = (data.sections || [])
        .map((section) => `<div class="report-section"><h4>${section.title}</h4><p>${section.content}</p></div>`)
        .join("");
    const evidence = renderEvidence(data.evidence);
    container.classList.remove("empty");
    container.innerHTML = `
        <h3>${data.company_name} 综合报告</h3>
        <p>${data.summary}</p>
        ${sections}
        ${evidence}
    `;
}

function renderBrief(container, data) {
    const judgements = (data.key_judgements || []).map((item) => `<li>${item}</li>`).join("");
    const actions = (data.action_recommendations || []).map((item) => `<li>${item}</li>`).join("");
    const evidenceHighlights = (data.evidence_highlights || []).map((item) => `<li>${item}</li>`).join("");
    const evidence = renderEvidence(data.evidence);
    container.classList.remove("empty");
    container.innerHTML = `
        <h3>${data.company_name} 决策简报</h3>
        <p><strong>经营判断：</strong>${data.verdict}</p>
        <p>${data.summary}</p>
        <div class="brief-block"><h4>关键判断</h4><ul>${judgements}</ul></div>
        <div class="brief-block"><h4>行动建议</h4><ul>${actions}</ul></div>
        ${evidenceHighlights ? `<div class="brief-block"><h4>证据摘要</h4><ul>${evidenceHighlights}</ul></div>` : ""}
        ${evidence}
    `;
}

function renderRisk(container, data) {
    const drivers = (data.drivers || []).map((item) => `<li>${item}</li>`).join("");
    const monitoring = (data.monitoring_items || []).map((item) => `<li>${item}</li>`).join("");
    const evidence = renderEvidence(data.evidence);
    container.classList.remove("empty");
    container.innerHTML = `
        <h3>${data.company_name} 风险预测</h3>
        <p><strong>预测等级：</strong>${data.risk_level}风险 / ${data.risk_score} 分</p>
        <p>${data.summary}</p>
        <div class="brief-block"><h4>风险驱动</h4><ul>${drivers}</ul></div>
        <div class="brief-block"><h4>监测指标</h4><ul>${monitoring}</ul></div>
        ${evidence}
    `;
}

function renderCompetitionPackage(container, data) {
    const sections = (data.sections || []).map((item) => `<li><strong>${item.title}</strong>：${item.content}</li>`).join("");
    const citations = (data.citations || []).slice(0, 6).map((item) => `<li>[${item.citation_id}] ${item.title}</li>`).join("");
    container.classList.remove("empty");
    container.innerHTML = `
        <h3>${data.company_name} 答辩稿骨架</h3>
        <p>${data.summary}</p>
        <div class="brief-block"><h4>章节提纲</h4><ul>${sections}</ul></div>
        <div class="brief-block"><h4>引用证据</h4><ul>${citations}</ul></div>
        <div class="export-meta">
            <p>引用条数：${data.citation_count}</p>
            ${data.markdown_path ? `<p>Markdown：<code>${data.markdown_path}</code></p>` : ""}
            ${data.evidence_path ? `<p>证据包：<code>${data.evidence_path}</code></p>` : ""}
        </div>
    `;
}

function renderQualitySummary(data) {
    const summary = document.getElementById("quality-summary");
    const anomalies = document.getElementById("quality-anomalies");
    if (!summary || !anomalies) {
        return;
    }

    const exchangeRows = (data.exchange_status || [])
        .map((item) => `
            <div class="quality-stat-pill">
                <strong>${item.exchange}</strong>
                <span>${item.downloaded_rows}/${item.rows || 0} 份</span>
            </div>
        `)
        .join("");

    summary.classList.remove("empty");
    summary.innerHTML = `
        <div class="quality-kpi-grid">
            <div class="quality-kpi-card"><strong>${(data.official_report_coverage_ratio * 100).toFixed(1)}%</strong><span>官方财报覆盖率</span></div>
            <div class="quality-kpi-card"><strong>${data.anomaly_company_count}</strong><span>待关注异常企业</span></div>
            <div class="quality-kpi-card"><strong>${data.pending_review_count}</strong><span>待人工复核</span></div>
            <div class="quality-kpi-card"><strong>${data.missing_report_slots}</strong><span>缺失财报槽位</span></div>
        </div>
        <div class="quality-stat-list">${exchangeRows || '<p>暂无交易所状态。</p>'}</div>
    `;

    const anomalyRows = (data.top_anomalies || []).map((item) => {
        const missing = item.critical_fields_missing.length ? `关键缺失：${item.critical_fields_missing.join("、")}` : "关键字段已齐备";
        const flags = item.anomaly_flags.length ? `异常标记：${item.anomaly_flags.join("；")}` : "暂无额外异常标记";
        const link = item.financial_source_url ? `<a href="${item.financial_source_url}" target="_blank" rel="noreferrer">查看财报</a>` : "";
        return `
            <div class="quality-anomaly-card">
                <div>
                    <strong>${item.company_name} ${item.report_year}</strong>
                    <p>覆盖率 ${(item.field_coverage_ratio * 100).toFixed(1)}%，${missing}</p>
                    <p>${flags}</p>
                    ${link ? `<p>${link}</p>` : ""}
                </div>
                <button type="button" class="quality-review-trigger" data-company-code="${item.company_code}" data-report-year="${item.report_year}">加入复核</button>
            </div>
        `;
    }).join("");

    anomalies.classList.remove("empty");
    anomalies.innerHTML = anomalyRows || "<p>当前没有高优先级异常项。</p>";
    bindQualityReviewTriggers();
}

function bindQualityReviewTriggers() {
    document.querySelectorAll(".quality-review-trigger").forEach((button) => {
        button.addEventListener("click", () => {
            const codeInput = document.getElementById("review-company-code");
            const yearInput = document.getElementById("review-report-year");
            if (codeInput && yearInput) {
                codeInput.value = button.dataset.companyCode;
                yearInput.value = button.dataset.reportYear;
            }
            const note = document.getElementById("review-note");
            if (note) {
                note.focus();
            }
        });
    });
}

async function loadQualitySummary() {
    const summary = document.getElementById("quality-summary");
    const anomalies = document.getElementById("quality-anomalies");
    if (!summary || !anomalies) {
        return;
    }
    summary.classList.remove("empty");
    anomalies.classList.remove("empty");
    summary.innerHTML = "<p>正在加载数据质量概览...</p>";
    anomalies.innerHTML = "<p>正在加载异常清单...</p>";

    const response = await fetch("/api/quality/summary");
    if (!response.ok) {
        summary.innerHTML = "<p>数据质量概览加载失败。</p>";
        anomalies.innerHTML = "<p>异常清单加载失败。</p>";
        return;
    }
    const data = await response.json();
    renderQualitySummary(data);
}

async function submitManualReview(event) {
    event.preventDefault();
    const result = document.getElementById("quality-review-result");
    const payload = {
        company_code: document.getElementById("review-company-code").value.trim(),
        report_year: Number(document.getElementById("review-report-year").value),
        finding_level: document.getElementById("review-finding-level").value,
        finding_type: document.getElementById("review-finding-type").value.trim(),
        note: document.getElementById("review-note").value.trim(),
    };

    if (!payload.company_code || !payload.report_year || !payload.finding_type || !payload.note) {
        result.classList.remove("empty");
        result.innerHTML = "<p>请完整填写复核信息。</p>";
        return;
    }

    result.classList.remove("empty");
    result.innerHTML = "<p>正在写入人工复核队列...</p>";

    const response = await fetch("/api/quality/reviews", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
    });
    if (!response.ok) {
        result.innerHTML = "<p>人工复核记录提交失败。</p>";
        return;
    }

    const data = await response.json();
    result.innerHTML = `<p>已加入复核队列：${data.review.company_code} ${data.review.report_year} / ${data.review.finding_type}</p>`;
    document.getElementById("review-note").value = "";
    renderQualitySummary(data.summary);
}

async function fetchCompanyReport(companyCode) {
    const container = document.getElementById("report-result");
    container.classList.remove("empty");
    container.innerHTML = "<p>正在生成综合报告...</p>";

    const response = await fetch(`/api/company/${companyCode}/report`);
    if (!response.ok) {
        container.innerHTML = "<p>综合报告生成失败，请稍后重试。</p>";
        return;
    }
    const data = await response.json();
    renderReport(container, data);
}

async function fetchDecisionBrief(companyCode, companyName) {
    const container = document.getElementById("brief-result");
    container.classList.remove("empty");
    container.innerHTML = "<p>正在生成决策简报...</p>";

    const response = await fetch(`/api/company/${companyCode}/decision-brief?question=${encodeURIComponent(`结合行业研报看${companyName}的机会和风险`)}`);
    if (!response.ok) {
        container.innerHTML = "<p>决策简报生成失败，请稍后重试。</p>";
        return;
    }
    const data = await response.json();
    renderBrief(container, data);
}

async function fetchRiskForecast(companyCode) {
    const container = document.getElementById("risk-result");
    container.classList.remove("empty");
    container.innerHTML = "<p>正在生成风险预测...</p>";

    const response = await fetch(`/api/company/${companyCode}/risk-forecast`);
    if (!response.ok) {
        container.innerHTML = "<p>风险预测生成失败，请稍后重试。</p>";
        return;
    }
    const data = await response.json();
    renderRisk(container, data);
}

async function fetchCompetitionPackage(companyCode, companyName) {
    const container = document.getElementById("competition-result");
    container.classList.remove("empty");
    container.innerHTML = "<p>正在导出答辩稿骨架...</p>";

    const response = await fetch(`/api/company/${companyCode}/competition-package?question=${encodeURIComponent(`结合真实数据为${companyName}生成企业运营分析答辩稿`)}`);
    if (!response.ok) {
        container.innerHTML = "<p>答辩稿导出失败，请稍后重试。</p>";
        return;
    }
    const data = await response.json();
    renderCompetitionPackage(container, data);
}

function bindQuickActions() {
    document.querySelectorAll(".quick-report").forEach((button) => {
        button.addEventListener("click", () => {
            fetchCompanyReport(button.dataset.companyCode);
        });
    });
    document.querySelectorAll(".quick-brief").forEach((button) => {
        button.addEventListener("click", () => {
            fetchDecisionBrief(button.dataset.companyCode, button.dataset.companyName);
        });
    });
    document.querySelectorAll(".quick-risk").forEach((button) => {
        button.addEventListener("click", () => {
            fetchRiskForecast(button.dataset.companyCode);
        });
    });
    document.querySelectorAll(".quick-package").forEach((button) => {
        button.addEventListener("click", () => {
            fetchCompetitionPackage(button.dataset.companyCode, button.dataset.companyName);
        });
    });
}

function bindPersonaCards() {
    document.querySelectorAll(".persona-card").forEach((button) => {
        button.addEventListener("click", () => {
            const input = document.getElementById("agent-question");
            if (!input) {
                return;
            }
            input.value = button.dataset.prompt;
            input.focus();
        });
    });
}

const form = document.getElementById("agent-form");
if (form) {
    form.addEventListener("submit", submitAgentQuestion);
}

const reviewForm = document.getElementById("quality-review-form");
if (reviewForm) {
    reviewForm.addEventListener("submit", submitManualReview);
}

bindQuickActions();
bindPersonaCards();
loadQualitySummary();

