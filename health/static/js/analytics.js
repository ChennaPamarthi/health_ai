document.addEventListener("DOMContentLoaded", () => {
    initAnalyticsPage();
});

async function initAnalyticsPage() {
    const api = window.HealthAI;
    document.getElementById("analytics-daily").innerHTML = `<div class="skeleton" style="height: 120px;"></div>`;
    document.getElementById("analytics-top-missed").innerHTML = `<div class="skeleton" style="height: 90px;"></div>`;
    document.getElementById("analytics-activity").innerHTML = `<div class="skeleton" style="height: 90px;"></div>`;

    try {
        const response = await api.apiGet("/api/analytics/summary/");
        renderAnalytics(response);
    } catch (error) {
        api.renderEmptyState(
            document.getElementById("analytics-daily"),
            "fa-solid fa-chart-line",
            "Unable to load analytics",
            error.message || "No analytics data was returned."
        );
        api.showToast(error.message || "Unable to load analytics.", "error", "Analytics");
    }
}

function renderAnalytics(response) {
    const api = window.HealthAI;
    const summary = response.summary || {};
    const daily = response.daily || [];
    const missed = response.top_missed_medicines || [];

    document.getElementById("analytics-prescriptions").textContent = summary.total_prescriptions ?? 0;
    document.getElementById("analytics-medicines").textContent = summary.total_medicines ?? 0;
    document.getElementById("analytics-reminders").textContent = summary.total_reminders ?? 0;
    document.getElementById("analytics-adherence").textContent = `${summary.adherence_percentage ?? 0}%`;

    const dailyContainer = document.getElementById("analytics-daily");
    if (!daily.length) {
        api.renderEmptyState(
            dailyContainer,
            "fa-solid fa-chart-column",
            "No trend data",
            "Create medicine logs to populate the adherence chart."
        );
    } else {
        dailyContainer.innerHTML = daily.map((day) => `
            <div class="analytics-day">
                <div class="day-head">
                    <span>${api.escapeHtml(day.label)} ${api.escapeHtml(api.formatDate(day.date))}</span>
                    <span>${api.escapeHtml(day.adherence_percentage)}%</span>
                </div>
                <div class="progress">
                    <div class="progress-bar bg-primary" style="width: ${day.adherence_percentage}%"></div>
                </div>
                <div class="day-meta">
                    <span>Taken: ${day.taken}</span>
                    <span>Missed: ${day.missed}</span>
                    <span>Pending: ${day.pending}</span>
                </div>
            </div>
        `).join("");
    }

    const missedContainer = document.getElementById("analytics-top-missed");
    if (!missed.length) {
        api.renderEmptyState(
            missedContainer,
            "fa-solid fa-pills",
            "Nothing missed yet",
            "Once data exists, the most missed medicines will appear here."
        );
    } else {
        missedContainer.innerHTML = missed.map((item) => `
            <div class="analytics-missed-item">
                <span>${api.escapeHtml(item.schedule__medicine__medicine_name || "-")}</span>
                <span class="badge bg-danger rounded-pill">${item.missed_count}</span>
            </div>
        `).join("");
    }

    const activityContainer = document.getElementById("analytics-activity");
    const activity = summary.recent_activity || [];
    if (!activity.length) {
        api.renderEmptyState(
            activityContainer,
            "fa-solid fa-clock-rotate-left",
            "No recent activity",
            "Uploaded prescriptions and appointments will appear here."
        );
    } else {
        activityContainer.innerHTML = activity.map((item) => `
            <div class="analytics-activity-item">
                <div class="d-flex justify-content-between gap-2">
                    <strong>${api.escapeHtml(item.type || "-")}</strong>
                    <span class="text-muted">${api.escapeHtml(api.formatDateTime(item.timestamp))}</span>
                </div>
                <div class="text-muted">${api.escapeHtml(item.title || "-")} ${item.subtitle ? `• ${api.escapeHtml(item.subtitle)}` : ""}</div>
            </div>
        `).join("");
    }
}

