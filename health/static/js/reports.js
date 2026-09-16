const reportState = {
    items: [],
};

document.addEventListener("DOMContentLoaded", () => {
    initReportsPage();
});

async function initReportsPage() {
    const api = window.HealthAI;
    const container = document.getElementById("report-list");
    api.renderSkeleton(container, 4, 2);

    try {
        const reports = await api.apiGet("/api/reports/");
        reportState.items = Array.isArray(reports) ? reports : [];
        renderReportStats(reportState.items);
        renderReports(reportState.items);
    } catch (error) {
        api.renderEmptyState(
            container,
            "fa-solid fa-file-circle-exclamation",
            "Unable to load reports",
            error.message || "No report data was returned."
        );
        api.showToast(error.message || "Unable to load reports.", "error", "Reports");
    }
}

function renderReportStats(items) {
    const thisMonth = new Date();
    const month = thisMonth.getMonth();
    const year = thisMonth.getFullYear();
    const scans = new Set(["MRI", "ECG", "X-Ray"]);

    document.getElementById("report-total").textContent = items.length;
    document.getElementById("report-blood").textContent = items.filter((item) => item.report_type === "Blood Report").length;
    document.getElementById("report-scan").textContent = items.filter((item) => scans.has(item.report_type)).length;
    document.getElementById("report-recent").textContent = items.filter((item) => {
        const date = new Date(item.created_at || item.report_date);
        return !Number.isNaN(date.getTime()) && date.getMonth() === month && date.getFullYear() === year;
    }).length;
}

function renderReports(items) {
    const api = window.HealthAI;
    const container = document.getElementById("report-list");

    if (!items.length) {
        api.renderEmptyState(
            container,
            "fa-solid fa-file-medical",
            "No reports yet",
            "Upload a blood report, X-ray, MRI, ECG, or other medical report to create a record.",
            `<a href="/upload/" class="btn btn-primary btn-sm">Upload report</a>`
        );
        return;
    }

    container.innerHTML = items.map((item) => `
        <div class="activity-item animate-fade-up">
            <div class="activity-icon">
                <i class="${reportIcon(item.report_type)}"></i>
            </div>
            <div class="flex-grow-1">
                <h5 class="activity-title">${api.escapeHtml(item.report_title || item.report_type_display || item.report_type || "Medical report")}</h5>
                <p class="activity-subtitle">${api.escapeHtml(item.summary || item.findings || item.notes || "Structured report saved")}</p>
                <p class="activity-meta">${api.escapeHtml(item.patient_name || "-")} &bull; ${api.escapeHtml(api.formatDate(item.report_date || item.created_at))}</p>
            </div>
            <button class="btn btn-outline-primary btn-sm report-view-btn" type="button" data-id="${item.id}">View</button>
        </div>
    `).join("");

    container.querySelectorAll(".report-view-btn").forEach((button) => {
        button.addEventListener("click", () => showReportModal(items.find((item) => item.id === Number(button.dataset.id))));
    });
}

function reportIcon(type) {
    const map = {
        "Blood Report": "fa-solid fa-vial",
        MRI: "fa-solid fa-magnet",
        ECG: "fa-solid fa-heart-pulse",
        "X-Ray": "fa-solid fa-x-ray",
    };
    return map[type] || "fa-solid fa-file-waveform";
}

function showReportModal(item) {
    const api = window.HealthAI;
    if (!item) {
        return;
    }

    document.getElementById("report-detail-title").textContent = item.report_title || item.report_type || "Report";
    document.getElementById("report-detail-content").innerHTML = `
        <div class="detail-section">
            ${detailRow("Patient", item.patient_name)}
            ${detailRow("Type", item.report_type_display || item.report_type)}
            ${detailRow("Title", item.report_title)}
            ${detailRow("Report date", api.formatDate(item.report_date))}
            ${detailRow("Summary", item.summary)}
            ${detailRow("Findings", item.findings)}
            ${detailRow("Recommendations", item.recommendations)}
            ${detailRow("Notes", item.notes)}
        </div>
    `;

    bootstrap.Modal.getOrCreateInstance(document.getElementById("reportDetailModal")).show();
}

function detailRow(label, value) {
    const api = window.HealthAI;
    const displayValue = value === null || value === undefined || value === "" ? "-" : value;
    return `
        <div class="detail-row">
            <span class="detail-label">${api.escapeHtml(label)}</span>
            <span class="detail-value">${api.escapeHtml(displayValue)}</span>
        </div>
    `;
}
