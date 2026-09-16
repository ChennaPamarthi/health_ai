document.addEventListener("DOMContentLoaded", () => {
    initAppointmentPage();
});

async function initAppointmentPage() {
    const api = window.HealthAI;
    const body = document.getElementById("appointment-table-body");
    api.renderSkeleton(body, 4, 6);

    try {
        const appointments = await api.apiGet("/api/appointments/");
        const list = Array.isArray(appointments) ? appointments : [];
        renderAppointmentStats(list);
        renderAppointments(list);
    } catch (error) {
        api.renderEmptyState(
            body,
            "fa-solid fa-calendar-xmark",
            "Unable to load appointments",
            error.message || "No appointment data was returned."
        );
        api.showToast(error.message || "Unable to load appointments.", "error", "Appointments");
    }
}

function renderAppointmentStats(items) {
    const upcoming = items.filter((item) => item.status === "Upcoming").length;
    const completed = items.filter((item) => item.status === "Completed").length;
    const cancelled = items.filter((item) => item.status === "Cancelled").length;

    document.getElementById("appointment-total").textContent = items.length;
    document.getElementById("appointment-upcoming").textContent = upcoming;
    document.getElementById("appointment-completed").textContent = completed;
    document.getElementById("appointment-cancelled").textContent = cancelled;
}

function renderAppointments(items) {
    const api = window.HealthAI;
    const body = document.getElementById("appointment-table-body");
    const summary = document.getElementById("appointment-summary");

    summary.textContent = `Showing ${items.length} appointments`;

    if (!items.length) {
        api.renderEmptyState(
            body,
            "fa-solid fa-calendar-days",
            "No appointments yet",
            "Appointments created in the backend will appear here."
        );
        return;
    }

    body.innerHTML = items.map((item) => `
        <tr class="animate-fade-up">
            <td>${api.escapeHtml(item.patient_name || "-")}</td>
            <td>${api.escapeHtml(item.doctor_name || "-")}</td>
            <td>${api.escapeHtml(api.formatDate(item.appointment_date))}</td>
            <td>${api.escapeHtml(item.appointment_time || "-")}</td>
            <td>
                <span class="status-pill ${api.statusClass(item.status)}">
                    <i class="fa-solid fa-circle"></i>
                    ${api.escapeHtml(api.formatStatusText(item.status))}
                </span>
            </td>
            <td class="text-end">
                <button class="btn btn-outline-primary btn-sm appointment-view-btn" data-id="${item.id}" type="button">View</button>
            </td>
        </tr>
    `).join("");

    body.querySelectorAll(".appointment-view-btn").forEach((button) => {
        button.addEventListener("click", () => showAppointmentModal(items.find((item) => item.id === Number(button.dataset.id))));
    });
}

function showAppointmentModal(item) {
    const api = window.HealthAI;
    if (!item) {
        return;
    }

    document.getElementById("appointment-detail-title").textContent = item.doctor_name || "Appointment";
    document.getElementById("appointment-detail-content").innerHTML = `
        <div class="appointment-detail-grid">
            <div class="detail-section">
                ${detailRow("Patient", item.patient_name)}
                ${detailRow("Doctor", item.doctor_name)}
                ${detailRow("Hospital", item.hospital_name)}
                ${detailRow("Department", item.department)}
                ${detailRow("Status", api.formatStatusText(item.status))}
            </div>
            <div class="detail-section">
                ${detailRow("Date", api.formatDate(item.appointment_date))}
                ${detailRow("Time", item.appointment_time)}
                ${detailRow("Purpose", item.purpose)}
                ${detailRow("Notes", item.notes)}
            </div>
        </div>
    `;

    bootstrap.Modal.getOrCreateInstance(document.getElementById("appointmentDetailModal")).show();
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
