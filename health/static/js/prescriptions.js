const prescriptionState = {
    activePrescription: null,
};

document.addEventListener("DOMContentLoaded", () => {
    initPrescriptionsPage();
});

async function initPrescriptionsPage() {
    const api = window.HealthAI;
    const container = document.getElementById("prescription-list");
    api.renderSkeleton(container, 3, 1);

    document.getElementById("confirm-delete-prescription-btn")?.addEventListener("click", confirmDeletePrescription);
    window.deleteCurrentPrescription = deletePrescriptionFromDetail;
    window.openDeletePrescriptionModalFromDetail = openDeletePrescriptionModalFromDetail;
    window.confirmDeletePrescriptionRecord = confirmDeletePrescription;

    try {
        const prescriptions = await api.apiGet("/api/prescriptions/");
        renderPrescriptions(Array.isArray(prescriptions) ? prescriptions : []);
    } catch (error) {
        api.renderEmptyState(
            container,
            "fa-solid fa-file-medical",
            "Unable to load prescriptions",
            error.message || "No prescription data was returned."
        );
        api.showToast(error.message || "Unable to load prescriptions.", "error", "Prescriptions");
    }
}

function renderPrescriptions(items) {
    const api = window.HealthAI;
    const container = document.getElementById("prescription-list");

    if (!items.length) {
        api.renderEmptyState(
            container,
            "fa-solid fa-file-medical",
            "No prescriptions yet",
            "Upload a prescription to create the first record.",
            `<a href="/upload/" class="btn btn-primary btn-sm">Upload Prescription</a>`
        );
        return;
    }

    container.innerHTML = items.map((item) => `
        <div class="content-card mb-3">
            <div class="d-flex justify-content-between align-items-start gap-3 flex-wrap">
                <div>
                    <h5 class="mb-1">${api.escapeHtml(item.doctor_name || "Prescription")}</h5>
                    <p class="text-muted mb-2">${api.escapeHtml(item.patient_name || "-")} • ${api.escapeHtml(api.formatDate(item.created_at))}</p>
                    <div class="d-flex flex-wrap gap-2">
                        <span class="badge bg-primary rounded-pill">${item.medicine_count ?? 0} medicines</span>
                        <span class="badge bg-light text-dark rounded-pill">${api.escapeHtml(item.hospital_name || "No hospital")}</span>
                    </div>
                </div>
                <div class="d-flex gap-2">
                    <button class="btn btn-outline-primary btn-sm prescription-view-btn" type="button" data-id="${item.id}">View details</button>
                    <button class="btn btn-outline-danger btn-sm prescription-delete-btn" type="button" data-id="${item.id}">Delete</button>
                </div>
            </div>
        </div>
    `).join("");

    container.querySelectorAll(".prescription-view-btn").forEach((button) => {
        button.addEventListener("click", async () => {
            const id = Number(button.dataset.id);
            const detail = await api.apiGet(`/api/prescriptions/${id}/`);
            showPrescriptionModal(detail);
        });
    });

    container.querySelectorAll(".prescription-delete-btn").forEach((button) => {
        button.addEventListener("click", () => {
            openDeletePrescriptionModal(Number(button.dataset.id));
        });
    });
}

function showPrescriptionModal(item) {
    const api = window.HealthAI;
    prescriptionState.activePrescription = item;
    document.getElementById("prescription-detail-title").textContent = item.doctor_name || "Prescription";

    const medicines = item.medicines || [];
    document.getElementById("prescription-detail-content").innerHTML = `
        <div class="row g-4">
            <div class="col-lg-6">
                <div class="detail-section">
                    ${detailRow("Patient", item.patient_name)}
                    ${detailRow("Doctor", item.doctor_name)}
                    ${detailRow("Hospital", item.hospital_name)}
                    ${detailRow("Diagnosis", item.diagnosis)}
                    ${detailRow("Prescription date", api.formatDate(item.prescription_date))}
                    ${detailRow("Review date", api.formatDate(item.review_date))}
                </div>
            </div>
            <div class="col-lg-6">
                <div class="detail-section">
                    ${detailRow("Medicines", item.medicine_count)}
                    ${detailRow("Notes", item.notes)}
                </div>
            </div>
            <div class="col-12">
                <div class="detail-section">
                    <h5>Medicines</h5>
                    ${medicines.length ? medicines.map((medicine) => `
                        <div class="detail-row">
                            <span class="detail-label">${api.escapeHtml(medicine.medicine_name)}</span>
                            <span class="detail-value">${api.escapeHtml(medicine.dosage || "-")} • ${api.escapeHtml(medicine.frequency_display || "-")}</span>
                        </div>
                    `).join("") : `<div class="text-muted">No medicines were attached to this prescription.</div>`}
                </div>
            </div>
        </div>
    `;

    bootstrap.Modal.getOrCreateInstance(document.getElementById("prescriptionDetailModal")).show();
}

function openDeletePrescriptionModal(prescriptionId) {
    document.getElementById("delete-prescription-id").value = prescriptionId;
    bootstrap.Modal.getOrCreateInstance(document.getElementById("deletePrescriptionModal")).show();
}

function openDeletePrescriptionModalFromDetail() {
    if (!prescriptionState.activePrescription) {
        return;
    }

    const detailModalEl = document.getElementById("prescriptionDetailModal");
    const deleteModalEl = document.getElementById("deletePrescriptionModal");

    if (detailModalEl && deleteModalEl) {
        detailModalEl.addEventListener(
            "hidden.bs.modal",
            () => openDeletePrescriptionModal(prescriptionState.activePrescription.id),
            { once: true }
        );
        bootstrap.Modal.getOrCreateInstance(detailModalEl).hide();
    } else {
        openDeletePrescriptionModal(prescriptionState.activePrescription.id);
    }
}

async function deletePrescriptionFromDetail() {
    if (!prescriptionState.activePrescription) {
        return;
    }

    const api = window.HealthAI;
    const confirmed = window.confirm(`Delete prescription "${prescriptionState.activePrescription.doctor_name || "Prescription"}"? This cannot be undone.`);
    if (!confirmed) {
        return;
    }

    const button = document.getElementById("delete-prescription-btn");
    api.setButtonLoading(button, true, "Deleting");
    try {
        await api.apiDelete(`/api/prescriptions/${prescriptionState.activePrescription.id}/`);
        bootstrap.Modal.getOrCreateInstance(document.getElementById("prescriptionDetailModal")).hide();
        api.showToast("Prescription deleted successfully.", "success", "Prescriptions");
        await initPrescriptionsPage();
    } catch (error) {
        api.showToast(error.message || "Unable to delete prescription.", "error", "Prescriptions");
    } finally {
        api.setButtonLoading(button, false);
    }
}

async function confirmDeletePrescription() {
    const api = window.HealthAI;
    const id = Number(document.getElementById("delete-prescription-id").value);
    const button = document.getElementById("confirm-delete-prescription-btn");

    api.setButtonLoading(button, true, "Deleting");
    try {
        await api.apiDelete(`/api/prescriptions/${id}/`);
        bootstrap.Modal.getOrCreateInstance(document.getElementById("deletePrescriptionModal")).hide();
        bootstrap.Modal.getOrCreateInstance(document.getElementById("prescriptionDetailModal")).hide();
        api.showToast("Prescription deleted successfully.", "success", "Prescriptions");
        await initPrescriptionsPage();
    } catch (error) {
        api.showToast(error.message || "Unable to delete prescription.", "error", "Prescriptions");
    } finally {
        api.setButtonLoading(button, false);
    }
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
