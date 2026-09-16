const reminderState = {
    items: [],
};

document.addEventListener("DOMContentLoaded", () => {
    initReminderPage();
});

async function initReminderPage() {
    const api = window.HealthAI;
    const container = document.getElementById("reminder-list");
    const historyContainer = document.getElementById("reminder-history-list");
    const confirmDeleteBtn = document.getElementById("confirm-delete-reminder-btn");
    api.renderSkeleton(container, 3, 1);
    api.renderSkeleton(historyContainer, 2, 1);

    if (!historyContainer.dataset.boundDeleteClick) {
        historyContainer.dataset.boundDeleteClick = "true";
        historyContainer.addEventListener("click", onReminderHistoryClick);
    }

    if (confirmDeleteBtn && !confirmDeleteBtn.dataset.boundDeleteAction) {
        confirmDeleteBtn.dataset.boundDeleteAction = "true";
        confirmDeleteBtn.addEventListener("click", confirmDeleteReminderDelete);
    }

    try {
        const reminders = await api.apiGet("/api/reminders/today/");
        reminderState.items = Array.isArray(reminders) ? reminders : [];
        renderReminderStats(reminderState.items);
        renderReminders();
        renderReminderHistory();
    } catch (error) {
        api.renderEmptyState(
            container,
            "fa-solid fa-bell",
            "Unable to load reminders",
            error.message || "No reminder data was returned."
        );
        api.renderEmptyState(
            historyContainer,
            "fa-solid fa-clock-rotate-left",
            "Unable to load history",
            "Completed reminders could not be loaded."
        );
        api.showToast(error.message || "Unable to load reminders.", "error", "Reminders");
    }
}

function renderReminderStats(items) {
    const taken = items.filter((item) => item.response_status === "Taken").length;
    const pending = items.filter((item) => ["Pending", "Upcoming", "Sent", "Delivered", "Read"].includes(item.status) && item.response_status === "Pending").length;
    const completed = items.filter((item) => ["Taken", "Skipped", "Snooze", "Missed"].includes(item.response_status)).length;

    document.getElementById("reminder-total").textContent = items.length;
    document.getElementById("reminder-taken").textContent = taken;
    document.getElementById("reminder-pending").textContent = pending;
    const pendingLabel = document.querySelector(".reminder-stat.stat-amber p");
    if (pendingLabel) {
        pendingLabel.textContent = completed ? "Pending / Done" : "Pending";
    }
}

function getActiveReminders() {
    return reminderState.items.filter((item) => item.response_status === "Pending" && ["Pending", "Upcoming", "Sent", "Delivered", "Read"].includes(item.status));
}

function getHistoryReminders() {
    return reminderState.items.filter((item) => item.response_status !== "Pending" || ["Failed"].includes(item.status));
}

function renderReminders() {
    const api = window.HealthAI;
    const container = document.getElementById("reminder-list");
    const items = getActiveReminders();

    if (!items.length) {
        api.renderEmptyState(
            container,
            "fa-solid fa-bell-slash",
            "No pending reminders",
            "Active reminders will appear here until you mark them taken, skipped, or snoozed."
        );
        return;
    }

    container.innerHTML = items.map((item) => `
        <div class="reminder-card animate-fade-up" data-reminder-id="${item.reminder_id || item.id}">
            <div class="d-flex justify-content-between align-items-start gap-3">
                <div>
                    <div class="reminder-time">${api.escapeHtml(api.formatTime(item.reminder_time))}</div>
                    <div class="reminder-title">${api.escapeHtml(item.medicine_name || "-")}</div>
                    <div class="reminder-meta">${api.escapeHtml(item.doctor_name || item.patient_name || "Prescription medicine")}</div>
                </div>
                <span class="status-pill ${api.statusClass(item.status)}">
                    <i class="fa-solid fa-circle"></i>
                    ${api.escapeHtml(api.formatStatusText(item.status))}
                </span>
            </div>
            <div class="d-flex justify-content-between align-items-center mt-3 flex-wrap gap-2">
                <div class="reminder-actions">
                    <button class="btn btn-success btn-sm" type="button" data-action="taken" data-reminder-id="${item.reminder_id || item.id}">Taken</button>
                    <button class="btn btn-outline-danger btn-sm" type="button" data-action="skipped" data-reminder-id="${item.reminder_id || item.id}">Skipped</button>
                    <button class="btn btn-outline-warning btn-sm" type="button" data-action="snooze" data-reminder-id="${item.reminder_id || item.id}">Snooze</button>
                </div>
            </div>
        </div>
    `).join("");

    container.querySelectorAll("button[data-action]").forEach((button) => {
        button.addEventListener("click", async () => {
            const action = button.dataset.action;
            const reminderId = Number(button.dataset.reminderId);
            await respondToReminder(reminderId, action);
        });
    });
}

function renderReminderHistory() {
    const api = window.HealthAI;
    const container = document.getElementById("reminder-history-list");
    const items = getHistoryReminders();

    if (!items.length) {
        api.renderEmptyState(
            container,
            "fa-solid fa-clock-rotate-left",
            "No completed reminders yet",
            "Confirmed or skipped reminders will appear here after you take action."
        );
        return;
    }

    container.innerHTML = items.map((item) => `
        <div class="reminder-card animate-fade-up">
            <div class="d-flex justify-content-between align-items-start gap-3">
                <div>
                    <div class="reminder-time">${api.escapeHtml(api.formatTime(item.reminder_time))}</div>
                    <div class="reminder-title">${api.escapeHtml(item.medicine_name || "-")}</div>
                    <div class="reminder-meta">${api.escapeHtml(item.response_status || item.status || "Completed")}</div>
                </div>
                <span class="status-pill ${api.statusClass(item.response_status || item.status)}">
                    <i class="fa-solid fa-circle"></i>
                    ${api.escapeHtml(api.formatStatusText(item.response_status || item.status))}
                </span>
            </div>
            <div class="d-flex justify-content-end mt-3">
                <button class="btn btn-outline-danger btn-sm" type="button" data-action="delete" data-reminder-id="${item.reminder_id || item.id}">
                    Delete
                </button>
            </div>
        </div>
    `).join("");
}

function onReminderHistoryClick(event) {
    const button = event.target.closest("button[data-action=\"delete\"]");
    if (!button) {
        return;
    }

    const reminderId = Number(button.dataset.reminderId);
    document.getElementById("delete-reminder-id").value = reminderId;
    bootstrap.Modal.getOrCreateInstance(document.getElementById("deleteReminderModal")).show();
}

async function respondToReminder(reminderId, action) {
    const api = window.HealthAI;
    try {
        await api.apiPost("/api/reminders/respond/", {
            reminder_id: reminderId,
            action,
        });
        api.showToast(`Marked as ${action}.`, "success", "Reminders");
        await initReminderPage();
    } catch (error) {
        api.showToast(error.message || "Unable to update reminder.", "error", "Reminders");
    }
}

async function confirmDeleteReminderDelete() {
    const api = window.HealthAI;
    const reminderId = Number(document.getElementById("delete-reminder-id").value);
    const button = document.getElementById("confirm-delete-reminder-btn");

    api.setButtonLoading(button, true, "Deleting");
    try {
        await api.apiDelete(`/api/reminders/${reminderId}/`);
        bootstrap.Modal.getOrCreateInstance(document.getElementById("deleteReminderModal")).hide();
        api.showToast("Reminder deleted successfully.", "success", "Reminders");
        await initReminderPage();
    } catch (error) {
        api.showToast(error.message || "Unable to delete reminder.", "error", "Reminders");
    } finally {
        api.setButtonLoading(button, false);
    }
}
