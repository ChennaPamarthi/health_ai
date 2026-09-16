const medicineState = {
    allMedicines: [],
    filteredMedicines: [],
    scheduleItems: [],
    searchTerm: "",
    filter: "all",
    page: 1,
    pageSize: 8,
    activeMedicine: null,
    activeSchedule: null,
};

document.addEventListener("DOMContentLoaded", () => {
    initMedicinePage();
});

async function initMedicinePage() {
    const api = window.HealthAI;

    bindMedicineEvents();
    await loadMedicineData();

    window.initMedicinePage = initMedicinePage;
    window.loadMedicines = loadMedicineData;
    window.renderMedicines = renderMedicines;
    window.renderSchedule = renderSchedule;
    window.updateStatistics = updateStatistics;
    window.showMedicineModal = showMedicineModal;
    window.editMedicine = openEditMedicineModal;
    window.deleteMedicine = openDeleteMedicineModal;
    window.updateMedicineStatus = updateMedicineStatus;
}

function bindMedicineEvents() {
    const api = window.HealthAI;
    const searchInput = document.getElementById("medicine-search");
    const filterGroup = document.getElementById("medicine-filters");
    const tableBody = document.getElementById("medicine-table-body");
    const scheduleList = document.getElementById("schedule-list");
    const pagination = document.getElementById("medicine-pagination");
    const detailEditBtn = document.getElementById("medicine-detail-edit-btn");
    const detailContent = document.getElementById("medicine-detail-content");
    const editForm = document.getElementById("medicine-edit-form");
    const confirmDeleteBtn = document.getElementById("confirm-delete-medicine-btn");
    const confirmDeleteScheduleBtn = document.getElementById("confirm-delete-schedule-btn");

    searchInput?.addEventListener("input", () => {
        medicineState.searchTerm = searchInput.value.trim().toLowerCase();
        medicineState.page = 1;
        applyFilters();
    });

    filterGroup?.addEventListener("click", (event) => {
        const button = event.target.closest(".filter-btn");
        if (!button) {
            return;
        }

        filterGroup.querySelectorAll(".filter-btn").forEach((item) => item.classList.remove("active"));
        button.classList.add("active");
        medicineState.filter = button.dataset.filter || "all";
        medicineState.page = 1;
        applyFilters();
    });

    tableBody?.addEventListener("click", onMedicineActionClick);
    scheduleList?.addEventListener("click", onScheduleActionClick);

    pagination?.addEventListener("click", (event) => {
        const button = event.target.closest("[data-page]");
        if (!button || button.classList.contains("disabled")) {
            return;
        }

        const page = Number(button.dataset.page);
        if (!Number.isFinite(page)) {
            return;
        }

        medicineState.page = page;
        renderMedicines();
    });

    detailEditBtn?.addEventListener("click", () => {
        if (medicineState.activeMedicine) {
            openEditMedicineModal(medicineState.activeMedicine);
        }
    });

    detailContent?.addEventListener("click", onMedicineDetailActionClick);
    editForm?.addEventListener("submit", saveMedicineChanges);
    confirmDeleteBtn?.addEventListener("click", confirmDeleteMedicine);
    confirmDeleteScheduleBtn?.addEventListener("click", confirmDeleteSchedule);
}

async function loadMedicineData() {
    const api = window.HealthAI;
    const tableBody = document.getElementById("medicine-table-body");
    const scheduleList = document.getElementById("schedule-list");

    api.renderSkeleton(tableBody, 4, 5);
    api.renderSkeleton(scheduleList, 3, 1);

    try {
        const [medicines, schedules] = await Promise.all([
            api.apiGet("/api/medicines/"),
            api.apiGet("/api/reminders/today/"),
        ]);

        medicineState.allMedicines = Array.isArray(medicines) ? medicines : [];
        medicineState.scheduleItems = Array.isArray(schedules) ? schedules : [];
        medicineState.page = 1;
        applyFilters();
        renderSchedule();
        updateStatistics();
    } catch (error) {
        api.renderEmptyState(
            tableBody,
            "fa-solid fa-triangle-exclamation",
            "Unable to load medicines",
            error.message || "The backend did not return medicine data."
        );
        api.renderEmptyState(
            scheduleList,
            "fa-solid fa-bell",
            "Unable to load reminders",
            error.message || "The backend did not return schedule data."
        );
        api.showToast(error.message || "Unable to load medicines.", "error", "Medicines");
    }
}

function applyFilters() {
    const api = window.HealthAI;
    let items = [...medicineState.allMedicines];

    if (medicineState.filter !== "all") {
        items = items.filter((medicine) => String(medicine.status || "").toLowerCase() === medicineState.filter.toLowerCase());
    }

    if (medicineState.searchTerm) {
        items = items.filter((medicine) => {
            const haystack = [
                medicine.medicine_name,
                medicine.dosage,
                medicine.strength,
                medicine.frequency_display,
                medicine.doctor_name,
                medicine.hospital_name,
            ]
                .filter(Boolean)
                .join(" ")
                .toLowerCase();
            return haystack.includes(medicineState.searchTerm);
        });
    }

    medicineState.filteredMedicines = items;
    renderMedicines();
    updateStatistics();
}

function renderMedicines() {
    const api = window.HealthAI;
    const tableBody = document.getElementById("medicine-table-body");
    const pagination = document.getElementById("medicine-pagination");
    const summary = document.getElementById("medicine-page-summary");
    const totalBadge = document.getElementById("medicine-total");

    const total = medicineState.filteredMedicines.length;
    const pages = Math.max(Math.ceil(total / medicineState.pageSize), 1);
    if (medicineState.page > pages) {
        medicineState.page = pages;
    }

    const start = (medicineState.page - 1) * medicineState.pageSize;
    const pageItems = medicineState.filteredMedicines.slice(start, start + medicineState.pageSize);

    totalBadge.textContent = `${medicineState.allMedicines.length} medicines`;
    summary.textContent = `Showing ${pageItems.length} of ${total} medicines`;

    if (!medicineState.filteredMedicines.length) {
        api.renderEmptyState(
            tableBody,
            "fa-solid fa-pills",
            "No medicines found",
            medicineState.searchTerm || medicineState.filter !== "all"
                ? "Try a different search term or reset the filter."
                : "Medicines created from prescriptions will appear here."
        );
        pagination.innerHTML = "";
        return;
    }

    tableBody.innerHTML = pageItems.map((medicine) => medicineRowHtml(medicine)).join("");
    pagination.innerHTML = buildPaginationHtml(total, pages);
}

function medicineRowHtml(medicine) {
    const api = window.HealthAI;
    const frequency = formatFrequency(medicine.frequency_display || medicine.frequency);
    return `
        <tr class="animate-fade-up">
            <td class="medicine-name-cell">
                <strong>${api.escapeHtml(medicine.medicine_name || "-")}</strong>
                <span class="medicine-subtext">${api.escapeHtml(medicine.doctor_name || medicine.hospital_name || "Prescription medicine")}</span>
            </td>
            <td>
                ${api.escapeHtml(medicine.dosage || "-")}
                ${medicine.strength ? `<span class="medicine-subtext">${api.escapeHtml(medicine.strength)}</span>` : ""}
            </td>
            <td>${api.escapeHtml(frequency)}</td>
            <td>
                <span class="status-pill ${api.statusClass(medicine.status)}">
                    <i class="fa-solid fa-circle"></i>
                    ${api.escapeHtml(api.formatStatusText(medicine.status))}
                </span>
            </td>
            <td class="text-end">
                <div class="medicine-row-actions">
                    <button class="btn btn-outline-primary view-btn" type="button" data-id="${medicine.id}">
                        <i class="fa-regular fa-eye"></i>
                    </button>
                    <button class="btn btn-outline-secondary edit-btn" type="button" data-id="${medicine.id}">
                        <i class="fa-regular fa-pen-to-square"></i>
                    </button>
                    <button class="btn btn-outline-success taken-btn" type="button" data-id="${medicine.id}">
                        <i class="fa-solid fa-check"></i>
                    </button>
                    <button class="btn btn-outline-warning missed-btn" type="button" data-id="${medicine.id}">
                        <i class="fa-solid fa-triangle-exclamation"></i>
                    </button>
                    <button class="btn btn-outline-danger delete-btn" type="button" data-id="${medicine.id}">
                        <i class="fa-regular fa-trash-can"></i>
                    </button>
                </div>
            </td>
        </tr>
    `;
}

function buildPaginationHtml(total, pages) {
    const current = medicineState.page;
    if (pages <= 1) {
        return "";
    }

    const items = [];
    items.push(pageItem("Previous", Math.max(current - 1, 1), current === 1));
    for (let page = 1; page <= pages; page += 1) {
        items.push(pageItem(String(page), page, false, page === current));
    }
    items.push(pageItem("Next", Math.min(current + 1, pages), current === pages));
    return items.join("");
}

function pageItem(label, page, disabled = false, active = false) {
    return `
        <li class="page-item ${disabled ? "disabled" : ""} ${active ? "active" : ""}">
            <button class="page-link" type="button" data-page="${page}" ${disabled ? "disabled" : ""}>${window.HealthAI.escapeHtml(label)}</button>
        </li>
    `;
}

function renderSchedule() {
    const api = window.HealthAI;
    const container = document.getElementById("schedule-list");
    const count = document.getElementById("schedule-count");
    const activeItems = medicineState.scheduleItems.filter(isVisibleScheduleItem);

    count.textContent = `${activeItems.length} items`;

    if (!activeItems.length) {
        api.renderEmptyState(
            container,
            "fa-solid fa-bell",
            "No reminders today",
            "Once schedules are created from prescriptions, they will show up here. Completed reminders disappear from this list."
        );
        return;
    }

    container.innerHTML = activeItems.map((item) => `
        <div class="schedule-item animate-fade-up">
            <div>
                <div class="schedule-time">${api.escapeHtml(api.formatTime(item.reminder_time))}</div>
                <div class="schedule-name">${api.escapeHtml(item.medicine_name || "-")}</div>
                <div class="schedule-meta">${api.escapeHtml(item.doctor_name || item.patient_name || "Prescription medicine")}</div>
            </div>
            <div class="text-end">
                <span class="status-pill ${api.statusClass(item.status)} mb-2 d-inline-flex">
                    <i class="fa-solid fa-circle"></i>
                    ${api.escapeHtml(api.formatStatusText(item.status))}
                </span>
                <div class="schedule-actions">
                    <button class="btn btn-success btn-sm take-schedule-btn" type="button" data-medicine-id="${item.medicine_id}" data-schedule-id="${item.schedule_id || item.id}">
                        Taken
                    </button>
                    <button class="btn btn-outline-danger btn-sm missed-schedule-btn" type="button" data-medicine-id="${item.medicine_id}" data-schedule-id="${item.schedule_id || item.id}">
                        Missed
                    </button>
                </div>
            </div>
        </div>
    `).join("");
}

function updateStatistics() {
    const medicines = medicineState.allMedicines;
    const schedules = medicineState.scheduleItems;
    const api = window.HealthAI;
    const activeSchedules = schedules.filter(isVisibleScheduleItem);

    const totalCount = document.getElementById("total-count");
    const takenCount = document.getElementById("taken-count");
    const pendingCount = document.getElementById("pending-count");
    const todayCount = document.getElementById("today-count");

    const taken = medicines.filter((medicine) => String(medicine.status || "").toLowerCase() === "taken").length;
    const pending = medicines.filter((medicine) => ["pending", "sent", "active", "upcoming"].includes(String(medicine.status || "").toLowerCase())).length;

    totalCount.textContent = medicines.length;
    takenCount.textContent = taken;
    pendingCount.textContent = pending;
    todayCount.textContent = activeSchedules.length;
}

async function onMedicineActionClick(event) {
    const button = event.target.closest("button[data-id]");
    if (!button) {
        return;
    }

    const id = Number(button.dataset.id);
    const medicine = medicineState.allMedicines.find((item) => item.id === id);
    if (!medicine) {
        return;
    }

    if (button.classList.contains("view-btn")) {
        await showMedicineModal(medicine);
        return;
    }

    if (button.classList.contains("edit-btn")) {
        openEditMedicineModal(medicine);
        return;
    }

    if (button.classList.contains("taken-btn")) {
        await updateMedicineStatus(id, "Taken");
        return;
    }

    if (button.classList.contains("missed-btn")) {
        await updateMedicineStatus(id, "Missed");
        return;
    }

    if (button.classList.contains("delete-btn")) {
        openDeleteMedicineModal(medicine);
    }
}

async function onScheduleActionClick(event) {
    const button = event.target.closest("button[data-medicine-id]");
    if (!button) {
        return;
    }

    const medicineId = Number(button.dataset.medicineId);
    const scheduleId = Number(button.dataset.scheduleId);

    if (button.classList.contains("take-schedule-btn")) {
        await updateMedicineStatus(medicineId, "Taken", scheduleId);
        return;
    }

    if (button.classList.contains("missed-schedule-btn")) {
        await updateMedicineStatus(medicineId, "Missed", scheduleId);
    }
}

function onMedicineDetailActionClick(event) {
    const button = event.target.closest("button[data-schedule-id]");
    if (!button) {
        return;
    }

    const scheduleId = Number(button.dataset.scheduleId);
    const schedule = medicineState.activeMedicine?.schedules?.find((item) => item.id === scheduleId);
    if (!schedule) {
        return;
    }

    if (button.classList.contains("delete-schedule-btn")) {
        openDeleteScheduleModal(schedule);
    }
}

async function showMedicineModal(medicineOrId) {
    const api = window.HealthAI;
    const id = typeof medicineOrId === "object" ? medicineOrId.id : medicineOrId;
    let medicine = typeof medicineOrId === "object" ? medicineOrId : null;

    if (!medicine || !medicine.schedules) {
        medicine = await api.apiGet(`/api/medicines/${id}/`);
    }

    medicineState.activeMedicine = medicine;

    const title = document.getElementById("medicine-detail-title");
    const content = document.getElementById("medicine-detail-content");
    title.textContent = medicine.medicine_name || "Medicine";
    content.innerHTML = buildDetailHtml(medicine);

    bootstrap.Modal.getOrCreateInstance(document.getElementById("medicineDetailModal")).show();
}

function buildDetailHtml(medicine) {
    const api = window.HealthAI;
    const schedules = medicine.schedules || [];
    const logs = medicine.recent_logs || [];

    return `
        <div class="detail-grid">
            <div class="detail-section">
                <h5>Basic information</h5>
                ${detailRow("Medicine", medicine.medicine_name)}
                ${detailRow("Dosage", medicine.dosage)}
                ${detailRow("Strength", medicine.strength)}
                ${detailRow("Frequency", medicine.frequency_display || formatFrequency(medicine.frequency))}
                ${detailRow("Duration", medicine.duration)}
                ${detailRow("Food instruction", medicine.food_instruction)}
                ${detailRow("Status", api.formatStatusText(medicine.status))}
            </div>
            <div class="detail-section">
                <h5>Prescription information</h5>
                ${detailRow("Patient", medicine.patient_name)}
                ${detailRow("Doctor", medicine.doctor_name)}
                ${detailRow("Hospital", medicine.hospital_name)}
                ${detailRow("Prescription date", api.formatDate(medicine.prescription_date))}
                ${detailRow("Review date", api.formatDate(medicine.review_date))}
                ${detailRow("Remaining days", medicine.remaining_days ?? "-")}
            </div>
            <div class="detail-section">
                <h5>Instructions</h5>
                <div class="instruction-box">${api.escapeHtml(medicine.special_instruction || "No special instructions.")}</div>
            </div>
            <div class="detail-section">
                <h5>Reminder schedule</h5>
                ${
                    schedules.length
                        ? schedules.map((item) => `
                            <div class="detail-row align-items-center">
                                <span class="detail-label">
                                    ${api.escapeHtml(api.formatTime(item.reminder_time))}
                                    <span class="ms-2 badge ${api.statusClass(item.status)}">${api.escapeHtml(api.formatStatusText(item.status))}</span>
                                </span>
                                <span class="detail-value">
                                    <button class="btn btn-outline-danger btn-sm delete-schedule-btn" type="button" data-schedule-id="${item.id}">
                                        Delete
                                    </button>
                                </span>
                            </div>
                        `).join("")
                        : `<div class="text-muted">No reminder schedule created.</div>`
                }
            </div>
            <div class="detail-section">
                <h5>Recent logs</h5>
                ${
                    logs.length
                        ? logs.map((item) => `
                            <div class="detail-row">
                                <span class="detail-label">${api.escapeHtml(api.formatDateTime(item.scheduled_datetime))}</span>
                                <span class="detail-value">
                                    <span class="status-pill ${api.statusClass(item.status)}">
                                        <i class="fa-solid fa-circle"></i>
                                        ${api.escapeHtml(api.formatStatusText(item.status))}
                                    </span>
                                </span>
                            </div>
                        `).join("")
                        : `<div class="text-muted">No logs recorded yet.</div>`
                }
            </div>
        </div>
    `;
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

function openEditMedicineModal(medicine) {
    const modal = bootstrap.Modal.getOrCreateInstance(document.getElementById("medicineEditModal"));
    medicineState.activeMedicine = medicine;

    document.getElementById("medicine-edit-id").value = medicine.id;
    document.getElementById("medicine-edit-name").value = medicine.medicine_name || "";
    document.getElementById("medicine-edit-strength").value = medicine.strength || "";
    document.getElementById("medicine-edit-dosage").value = medicine.dosage || "";
    document.getElementById("medicine-edit-quantity").value = medicine.quantity || 1;
    document.getElementById("medicine-edit-frequency").value = formatFrequency(medicine.frequency).replaceAll(" / ", ", ");
    document.getElementById("medicine-edit-duration").value = medicine.duration || "";
    document.getElementById("medicine-edit-food").value = medicine.food_instruction || "After Food";
    document.getElementById("medicine-edit-special").value = medicine.special_instruction || "";
    document.getElementById("medicine-edit-active").checked = Boolean(medicine.is_active);

    modal.show();
}

function openDeleteMedicineModal(medicine) {
    const modal = bootstrap.Modal.getOrCreateInstance(document.getElementById("deleteMedicineModal"));
    document.getElementById("delete-medicine-id").value = medicine.id;
    medicineState.activeMedicine = medicine;
    modal.show();
}

function openDeleteScheduleModal(schedule) {
    const modal = bootstrap.Modal.getOrCreateInstance(document.getElementById("deleteScheduleModal"));
    medicineState.activeSchedule = schedule;
    document.getElementById("delete-schedule-id").value = schedule.id;
    modal.show();
}

async function saveMedicineChanges(event) {
    event.preventDefault();
    const api = window.HealthAI;
    const id = Number(document.getElementById("medicine-edit-id").value);
    const saveBtn = document.getElementById("medicine-save-btn");

    const payload = {
        medicine_name: document.getElementById("medicine-edit-name").value.trim(),
        strength: document.getElementById("medicine-edit-strength").value.trim(),
        dosage: document.getElementById("medicine-edit-dosage").value.trim(),
        quantity: Number(document.getElementById("medicine-edit-quantity").value || 1),
        frequency: document
            .getElementById("medicine-edit-frequency")
            .value.split(",")
            .map((item) => item.trim())
            .filter(Boolean),
        duration: document.getElementById("medicine-edit-duration").value.trim(),
        food_instruction: document.getElementById("medicine-edit-food").value,
        special_instruction: document.getElementById("medicine-edit-special").value.trim(),
        is_active: document.getElementById("medicine-edit-active").checked,
    };

    api.setButtonLoading(saveBtn, true, "Saving");
    try {
        await api.apiPut(`/api/medicines/${id}/`, payload);
        bootstrap.Modal.getOrCreateInstance(document.getElementById("medicineEditModal")).hide();
        api.showToast("Medicine updated successfully.", "success", "Medicines");
        await loadMedicineData();
    } catch (error) {
        api.showToast(error.message || "Unable to update medicine.", "error", "Medicines");
    } finally {
        api.setButtonLoading(saveBtn, false);
    }
}

async function confirmDeleteMedicine() {
    const api = window.HealthAI;
    const id = Number(document.getElementById("delete-medicine-id").value);
    const button = document.getElementById("confirm-delete-medicine-btn");

    api.setButtonLoading(button, true, "Deleting");
    try {
        await api.apiDelete(`/api/medicines/${id}/`);
        bootstrap.Modal.getOrCreateInstance(document.getElementById("deleteMedicineModal")).hide();
        api.showToast("Medicine deleted successfully.", "success", "Medicines");
        await loadMedicineData();
    } catch (error) {
        api.showToast(error.message || "Unable to delete medicine.", "error", "Medicines");
    } finally {
        api.setButtonLoading(button, false);
    }
}

async function confirmDeleteSchedule() {
    const api = window.HealthAI;
    const id = Number(document.getElementById("delete-schedule-id").value);
    const button = document.getElementById("confirm-delete-schedule-btn");

    api.setButtonLoading(button, true, "Deleting");
    try {
        await api.apiDelete(`/api/schedules/${id}/`);
        bootstrap.Modal.getOrCreateInstance(document.getElementById("deleteScheduleModal")).hide();
        api.showToast("Schedule deleted successfully.", "success", "Medicines");
        await loadMedicineData();
        if (medicineState.activeMedicine?.id) {
            await showMedicineModal(medicineState.activeMedicine.id);
        }
    } catch (error) {
        api.showToast(error.message || "Unable to delete schedule.", "error", "Medicines");
    } finally {
        api.setButtonLoading(button, false);
    }
}

async function updateMedicineStatus(medicineId, status, scheduleId = null) {
    const api = window.HealthAI;
    try {
        await api.apiPost("/api/medicine-log/", {
            medicine_id: medicineId,
            schedule_id: scheduleId,
            status,
        });
        api.showToast(`Marked as ${status.toLowerCase()}.`, "success", "Medicines");
        await loadMedicineData();
    } catch (error) {
        api.showToast(error.message || "Unable to update medicine status.", "error", "Medicines");
    }
}

function formatFrequency(value) {
    if (Array.isArray(value)) {
        return value.length ? value.join(" / ") : "-";
    }

    if (typeof value === "string") {
        return value || "-";
    }

    return "-";
}

function isVisibleScheduleItem(item) {
    const status = String(item?.response_status || item?.status || "").toLowerCase();
    return !["taken", "completed", "skipped", "snooze", "missed"].includes(status);
}
