document.addEventListener("DOMContentLoaded", () => {
    initDashboardPage();
});

async function initDashboardPage() {
    const api = window.HealthAI;
    const metrics = {
        prescriptions: document.getElementById("metric-prescriptions"),
        medicines: document.getElementById("metric-medicines"),
        reminders: document.getElementById("metric-reminders"),
        appointments: document.getElementById("metric-appointments"),
        reports: document.getElementById("metric-reports"),
    };

    const prescriptionsBody = document.getElementById("dashboard-prescriptions-body");
    const remindersList = document.getElementById("dashboard-reminders-list");
    const reminderCount = document.getElementById("today-reminder-count");
    const documentsList = document.getElementById("recent-documents-list");
    const reportsList = document.getElementById("recent-reports-list");
    const workoutCard = document.getElementById("dashboard-workout-card");

    api.renderSkeleton(prescriptionsBody, 3, 4);
    api.renderSkeleton(remindersList, 3, 1);
    api.renderSkeleton(documentsList, 3, 2);
    api.renderSkeleton(reportsList, 3, 2);

    try {
        const data = await api.apiGet("/api/dashboard/summary/");
        metrics.prescriptions.textContent = data.total_prescriptions ?? 0;
        metrics.medicines.textContent = data.active_medicines ?? data.total_medicines ?? 0;
        metrics.reminders.textContent = data.total_reminders ?? 0;
        metrics.appointments.textContent = data.total_appointments ?? 0;
        if (metrics.reports) {
            metrics.reports.textContent = data.total_reports ?? 0;
        }

        renderRecentPrescriptions(data.recent_prescriptions || [], prescriptionsBody);
        renderTodaySchedule(data.recent_medicines || [], data.recent_activity || [], remindersList, reminderCount);
        renderRecentDocuments(data.recent_documents || [], documentsList);
        renderRecentReports(data.recent_reports || [], reportsList);
        renderWorkoutCard(workoutCard);
    } catch (error) {
        api.renderEmptyState(
            prescriptionsBody,
            "fa-solid fa-triangle-exclamation",
            "Unable to load dashboard",
            error.message || "Please try again in a moment."
        );
        api.renderEmptyState(
            remindersList,
            "fa-solid fa-triangle-exclamation",
            "Unable to load dashboard",
            error.message || "Please try again in a moment."
        );
        if (documentsList) {
            api.renderEmptyState(
                documentsList,
                "fa-solid fa-file",
                "Unable to load dashboard",
                error.message || "Please try again in a moment."
            );
        }
        if (reportsList) {
            api.renderEmptyState(
                reportsList,
                "fa-solid fa-file-waveform",
                "Unable to load dashboard",
                error.message || "Please try again in a moment."
            );
        }
        if (workoutCard) {
            workoutCard.style.display = "none";
        }
        api.showToast(error.message || "Dashboard load failed.", "error", "Dashboard");
    }
}

function renderRecentPrescriptions(items, container) {
    const api = window.HealthAI;
    if (!container) {
        return;
    }

    if (!items.length) {
        api.renderEmptyState(
            container,
            "fa-solid fa-file-medical",
            "No prescriptions yet",
            "Upload a prescription to start building your health timeline.",
            `<a href="/upload/" class="btn btn-primary btn-sm">Upload Prescription</a>`
        );
        return;
    }

    container.innerHTML = items.map((item) => `
        <tr class="animate-fade-up">
            <td>${api.escapeHtml(item.patient_name || "-")}</td>
            <td>${api.escapeHtml(item.doctor_name || "-")}</td>
            <td>${api.escapeHtml(api.formatDate(item.created_at))}</td>
            <td><span class="badge bg-primary rounded-pill">${api.escapeHtml(item.medicine_count ?? 0)}</span></td>
        </tr>
    `).join("");
}

function renderTodaySchedule(medicines, activities, container, countBadge) {
    const api = window.HealthAI;
    const reminders = activities.filter((item) => item.type === "Prescription").length
        ? medicines
        : medicines;

    if (countBadge) {
        countBadge.textContent = `${medicines.length} items`;
    }

    if (!container) {
        return;
    }

    if (!medicines.length) {
        api.renderEmptyState(
            container,
            "fa-solid fa-bell",
            "No schedule yet",
            "Once medicines are extracted, today's reminder list will appear here."
        );
        return;
    }

    container.innerHTML = medicines.slice(0, 4).map((medicine) => `
        <div class="schedule-card animate-fade-up">
            <div class="d-flex justify-content-between align-items-start gap-3">
                <div>
                    <div class="time">${api.escapeHtml(medicine.frequency_display || "Scheduled")}</div>
                    <div class="name">${api.escapeHtml(medicine.medicine_name || "-")}</div>
                    <div class="meta">${api.escapeHtml(medicine.doctor_name || medicine.hospital_name || "Prescription medicine")}</div>
                </div>
                <span class="status-pill ${api.statusClass(medicine.status)}">
                    <i class="fa-solid fa-circle"></i>
                    ${api.escapeHtml(api.formatStatusText(medicine.status))}
                </span>
            </div>
        </div>
    `).join("");
}

function renderRecentDocuments(items, container) {
    const api = window.HealthAI;
    if (!container) {
        return;
    }

    if (!items.length) {
        api.renderEmptyState(
            container,
            "fa-solid fa-file",
            "No documents yet",
            "Uploaded reports and prescriptions will appear here."
        );
        return;
    }

    container.innerHTML = items.map((item) => `
        <div class="activity-item animate-fade-up">
            <div class="activity-icon">
                <i class="fa-solid fa-file-lines"></i>
            </div>
            <div class="flex-grow-1">
                <h5 class="activity-title">${api.escapeHtml(item.document_type || "Document")}</h5>
                <p class="activity-subtitle">${api.escapeHtml(item.title || item.description || "Uploaded file")}</p>
                <p class="activity-meta">${api.escapeHtml(api.formatDateTime(item.uploaded_at))}</p>
            </div>
            <span class="status-pill ${api.statusClass(item.status)}">
                <i class="fa-solid fa-circle"></i>
                ${api.escapeHtml(api.formatStatusText(item.status))}
            </span>
        </div>
    `).join("");
}

function renderRecentReports(items, container) {
    const api = window.HealthAI;
    if (!container) {
        return;
    }

    if (!items.length) {
        api.renderEmptyState(
            container,
            "fa-solid fa-file-waveform",
            "No reports yet",
            "Structured report findings will appear here after upload."
        );
        return;
    }

    container.innerHTML = items.map((item) => `
        <div class="activity-item animate-fade-up">
            <div class="activity-icon">
                <i class="fa-solid fa-file-waveform"></i>
            </div>
            <div class="flex-grow-1">
                <h5 class="activity-title">${api.escapeHtml(item.report_type_display || item.report_type || "Report")}</h5>
                <p class="activity-subtitle">${api.escapeHtml(item.report_title || item.summary || "Structured report")}</p>
                <p class="activity-meta">${api.escapeHtml(api.formatDateTime(item.created_at))}</p>
            </div>
            <span class="status-pill ${api.statusClass("Completed")}">
                <i class="fa-solid fa-circle"></i>
                Completed
            </span>
        </div>
    `).join("");
}

function renderWorkoutCard(container) {
    const api = window.HealthAI;
    if (!container) {
        return;
    }

    const enabled = localStorage.getItem("healthai-dashboard-workout") === "true";
    const goalMinutes = Math.max(Number(localStorage.getItem("healthai-workout-goal-minutes") || 30), 5);
    const completedMinutes = 0;
    const progress = Math.min(Math.round((completedMinutes / goalMinutes) * 100), 100);

    if (!enabled) {
        container.style.display = "none";
        return;
    }

    container.style.display = "";
    const goalBadge = document.getElementById("workout-goal-badge");
    const summaryText = document.getElementById("workout-summary-text");
    const summaryMeta = document.getElementById("workout-summary-meta");
    const progressBar = document.getElementById("workout-progress-bar");
    const progressLabel = document.getElementById("workout-progress-label");

    if (goalBadge) {
        goalBadge.textContent = `Goal ${goalMinutes} min`;
    }
    if (summaryText) {
        summaryText.textContent = "Workout card is enabled on your dashboard.";
    }
    if (summaryMeta) {
        summaryMeta.textContent = `Your daily target is ${goalMinutes} minutes.`;
    }
    if (progressBar) {
        progressBar.style.width = `${progress}%`;
        progressBar.setAttribute("aria-valuenow", String(progress));
    }
    if (progressLabel) {
        progressLabel.textContent = `${progress}%`;
    }
}
