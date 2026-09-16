const caregiverState = {
    caregivers: [],
};

document.addEventListener("DOMContentLoaded", () => {
    document.getElementById("caregiver-form")?.addEventListener("submit", saveCaregiver);
    document.getElementById("cancel-caregiver-edit")?.addEventListener("click", resetCaregiverForm);
    document.getElementById("refresh-caregivers")?.addEventListener("click", loadCaregivers);
    loadCaregivers();
    loadCarePlan();
});

async function loadCaregivers() {
    const api = window.HealthAI;
    const container = document.getElementById("caregiver-list");
    if (!container) {
        return;
    }

    api.renderSkeleton(container, 3, 2);
    try {
        const caregivers = await api.apiGet("/api/caregivers/");
        caregiverState.caregivers = Array.isArray(caregivers) ? caregivers : [];
        renderCaregivers();
    } catch (error) {
        api.renderEmptyState(
            container,
            "fa-solid fa-triangle-exclamation",
            "Unable to load caregivers",
            error.message || "Caregiver records could not be loaded."
        );
    }
}

function renderCaregivers() {
    const api = window.HealthAI;
    const container = document.getElementById("caregiver-list");
    const caregivers = caregiverState.caregivers || [];

    if (!container) {
        return;
    }

    if (!caregivers.length) {
        api.renderEmptyState(
            container,
            "fa-solid fa-user-plus",
            "No caregivers added",
            "Add a caregiver so missed medicine alerts can be escalated after 10 minutes."
        );
        return;
    }

    container.innerHTML = caregivers.map((item) => `
        <div class="reminder-card animate-fade-up mb-3">
            <div class="d-flex justify-content-between align-items-start gap-3 flex-wrap">
                <div>
                    <div class="reminder-title">
                        ${api.escapeHtml(item.name || "Caregiver")}
                        ${item.is_primary ? '<span class="badge bg-primary rounded-pill ms-2">Primary</span>' : ""}
                    </div>
                    <div class="reminder-meta">
                        ${api.escapeHtml(item.relationship || "Caregiver")} &bull;
                        ${api.escapeHtml(formatPreference(item.notification_preference))}
                    </div>
                    <div class="d-flex flex-wrap gap-2 mt-2">
                        ${item.email ? `<span class="badge bg-light text-dark rounded-pill"><i class="fa-regular fa-envelope me-1"></i>${api.escapeHtml(item.email)}</span>` : ""}
                        ${item.phone ? `<span class="badge bg-light text-dark rounded-pill"><i class="fa-solid fa-phone me-1"></i>${api.escapeHtml(item.phone)}</span>` : ""}
                        <span class="badge ${item.enable_notifications ? "bg-success" : "bg-secondary"} rounded-pill">
                            ${item.enable_notifications ? "Alerts enabled" : "Alerts paused"}
                        </span>
                    </div>
                </div>
                <div class="d-flex gap-2">
                    <button class="btn btn-outline-primary btn-sm edit-caregiver-btn" type="button" data-id="${item.id}">
                        <i class="fa-regular fa-pen-to-square me-1"></i>Edit
                    </button>
                    <button class="btn btn-outline-danger btn-sm delete-caregiver-btn" type="button" data-id="${item.id}">
                        <i class="fa-regular fa-trash-can me-1"></i>Delete
                    </button>
                </div>
            </div>
        </div>
    `).join("");

    container.querySelectorAll(".edit-caregiver-btn").forEach((button) => {
        button.addEventListener("click", () => fillCaregiverForm(Number(button.dataset.id)));
    });
    container.querySelectorAll(".delete-caregiver-btn").forEach((button) => {
        button.addEventListener("click", () => deleteCaregiver(Number(button.dataset.id)));
    });
}

function formatPreference(value) {
    const map = {
        email: "Email alerts",
        sms: "SMS alerts",
        email_sms: "Email + SMS alerts",
    };
    return map[value] || "Email alerts";
}

function getCaregiverPayload() {
    return {
        name: document.getElementById("caregiver-name")?.value.trim() || "",
        relationship: document.getElementById("caregiver-relationship")?.value.trim() || "",
        email: document.getElementById("caregiver-email")?.value.trim() || "",
        phone: document.getElementById("caregiver-phone")?.value.trim() || "",
        notification_preference: document.getElementById("caregiver-preference")?.value || "email",
        enable_notifications: Boolean(document.getElementById("caregiver-enabled")?.checked),
        is_primary: Boolean(document.getElementById("caregiver-primary")?.checked),
    };
}

function fillCaregiverForm(id) {
    const caregiver = caregiverState.caregivers.find((item) => item.id === id);
    if (!caregiver) {
        return;
    }

    document.getElementById("caregiver-id").value = caregiver.id;
    document.getElementById("caregiver-name").value = caregiver.name || "";
    document.getElementById("caregiver-relationship").value = caregiver.relationship || "";
    document.getElementById("caregiver-email").value = caregiver.email || "";
    document.getElementById("caregiver-phone").value = caregiver.phone || "";
    document.getElementById("caregiver-preference").value = caregiver.notification_preference || "email";
    document.getElementById("caregiver-enabled").checked = Boolean(caregiver.enable_notifications);
    document.getElementById("caregiver-primary").checked = Boolean(caregiver.is_primary);
    document.getElementById("cancel-caregiver-edit")?.classList.remove("d-none");
    document.getElementById("save-caregiver-btn").textContent = "Update caregiver";
}

function resetCaregiverForm() {
    const form = document.getElementById("caregiver-form");
    form?.reset();
    document.getElementById("caregiver-id").value = "";
    document.getElementById("caregiver-enabled").checked = true;
    document.getElementById("caregiver-primary").checked = false;
    document.getElementById("caregiver-preference").value = "email";
    document.getElementById("cancel-caregiver-edit")?.classList.add("d-none");
    document.getElementById("save-caregiver-btn").textContent = "Save caregiver";
}

function errorMessage(error) {
    const errors = error.payload?.errors;
    if (!errors || typeof errors !== "object") {
        return error.message || "Unable to save caregiver.";
    }
    const firstKey = Object.keys(errors)[0];
    const firstValue = Array.isArray(errors[firstKey]) ? errors[firstKey][0] : errors[firstKey];
    return `${firstKey}: ${firstValue}`;
}

async function saveCaregiver(event) {
    event.preventDefault();
    const api = window.HealthAI;
    const button = document.getElementById("save-caregiver-btn");
    const id = document.getElementById("caregiver-id")?.value;
    const payload = getCaregiverPayload();

    if (!payload.name) {
        api.showToast("Caregiver name is required.", "error", "Caregivers");
        return;
    }

    if (["email", "email_sms"].includes(payload.notification_preference) && !payload.email) {
        api.showToast("Email is required for email caregiver alerts.", "error", "Caregivers");
        return;
    }

    if (["sms", "email_sms"].includes(payload.notification_preference) && !payload.phone) {
        api.showToast("Phone is required for SMS caregiver alerts.", "error", "Caregivers");
        return;
    }

    api.setButtonLoading(button, true, id ? "Updating" : "Saving");
    try {
        if (id) {
            await api.apiPut(`/api/caregivers/${id}/`, payload);
            api.showToast("Caregiver updated.", "success", "Caregivers");
        } else {
            await api.apiPost("/api/caregivers/", payload);
            api.showToast("Caregiver added.", "success", "Caregivers");
        }
        resetCaregiverForm();
        await loadCaregivers();
    } catch (error) {
        api.showToast(errorMessage(error), "error", "Caregivers");
    } finally {
        api.setButtonLoading(button, false);
        if (!document.getElementById("caregiver-id")?.value && button) {
            button.textContent = "Save caregiver";
        }
    }
}

async function deleteCaregiver(id) {
    const api = window.HealthAI;
    if (!window.confirm("Delete this caregiver?")) {
        return;
    }

    try {
        await api.apiDelete(`/api/caregivers/${id}/`);
        api.showToast("Caregiver deleted.", "success", "Caregivers");
        await loadCaregivers();
        resetCaregiverForm();
    } catch (error) {
        api.showToast(error.message || "Unable to delete caregiver.", "error", "Caregivers");
    }
}

async function loadCarePlan() {
    const api = window.HealthAI;
    const summary = document.getElementById("caregiver-care-summary");
    const medicines = document.getElementById("caregiver-medicine-list");

    if (summary) {
        api.renderSkeleton(summary, 3, 1);
    }
    if (medicines) {
        api.renderSkeleton(medicines, 4, 2);
    }

    try {
        const data = await api.apiGet("/api/dashboard/summary/");
        renderCareSummary(data);
        renderMedicineContext(data.recent_medicines || []);
    } catch (error) {
        if (summary) {
            api.renderEmptyState(summary, "fa-solid fa-triangle-exclamation", "Unable to load care plan", error.message || "Try refreshing.");
        }
        if (medicines) {
            api.renderEmptyState(medicines, "fa-solid fa-pills", "Unable to load medicines", error.message || "Try refreshing.");
        }
    }
}

function renderCareSummary(data) {
    const api = window.HealthAI;
    const container = document.getElementById("caregiver-care-summary");
    if (!container) {
        return;
    }

    container.innerHTML = `
        <div class="row g-3">
            <div class="col-6">
                <div class="summary-box">
                    <i class="fa-solid fa-pills fa-2x text-primary"></i>
                    <h3>${api.escapeHtml(data.active_medicines ?? data.total_medicines ?? 0)}</h3>
                    <p>Active medicines</p>
                </div>
            </div>
            <div class="col-6">
                <div class="summary-box">
                    <i class="fa-solid fa-bell fa-2x text-warning"></i>
                    <h3>${api.escapeHtml(data.total_reminders ?? 0)}</h3>
                    <p>Today reminders</p>
                </div>
            </div>
            <div class="col-6">
                <div class="summary-box">
                    <i class="fa-solid fa-file-medical fa-2x text-success"></i>
                    <h3>${api.escapeHtml(data.total_prescriptions ?? 0)}</h3>
                    <p>Prescriptions</p>
                </div>
            </div>
            <div class="col-6">
                <div class="summary-box">
                    <i class="fa-solid fa-triangle-exclamation fa-2x text-danger"></i>
                    <h3>${api.escapeHtml(data.missed_count ?? 0)}</h3>
                    <p>Missed logs</p>
                </div>
            </div>
        </div>
    `;
}

function renderMedicineContext(items) {
    const api = window.HealthAI;
    const container = document.getElementById("caregiver-medicine-list");
    if (!container) {
        return;
    }

    if (!items.length) {
        api.renderEmptyState(
            container,
            "fa-solid fa-prescription-bottle-medical",
            "No medicines yet",
            "Once prescriptions are created, recent medicines will appear here."
        );
        return;
    }

    container.innerHTML = items.slice(0, 6).map((item) => `
        <div class="activity-item animate-fade-up">
            <div class="activity-icon">
                <i class="fa-solid fa-pills"></i>
            </div>
            <div class="flex-grow-1">
                <h5 class="activity-title">${api.escapeHtml(item.medicine_name || "-")}</h5>
                <p class="activity-subtitle">
                    ${api.escapeHtml(item.dosage || "No dosage")}
                    ${item.duration ? ` &bull; ${api.escapeHtml(item.duration)}` : ""}
                </p>
                <p class="activity-meta">${api.escapeHtml(item.doctor_name || item.hospital_name || "Prescription medicine")}</p>
            </div>
            <span class="status-pill ${api.statusClass(item.status)}">
                <i class="fa-solid fa-circle"></i>
                ${api.escapeHtml(api.formatStatusText(item.status))}
            </span>
        </div>
    `).join("");
}
