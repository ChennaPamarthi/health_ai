const uploadState = {
    selectedFile: null,
    documents: [],
    latestUpload: null,
};

document.addEventListener("DOMContentLoaded", () => {
    const api = window.HealthAI;
    const dropZone = document.getElementById("drop-zone");
    const fileInput = document.getElementById("file-input");
    const preview = document.getElementById("preview-content");
    const uploadButton = document.getElementById("upload-btn");
    const refreshDocumentsBtn = document.getElementById("refresh-documents-btn");
    const confirmDeleteDocumentBtn = document.getElementById("confirm-delete-document-btn");

    if (!dropZone || !fileInput || !preview || !uploadButton) {
        return;
    }

    dropZone.addEventListener("click", () => fileInput.click());

    fileInput.addEventListener("change", function () {
        if (this.files && this.files.length) {
            loadFile(this.files[0]);
        }
    });

    dropZone.addEventListener("dragover", (event) => {
        event.preventDefault();
        dropZone.classList.add("drag-over");
    });

    dropZone.addEventListener("dragleave", () => {
        dropZone.classList.remove("drag-over");
    });

    dropZone.addEventListener("drop", (event) => {
        event.preventDefault();
        dropZone.classList.remove("drag-over");

        if (event.dataTransfer.files && event.dataTransfer.files.length) {
            loadFile(event.dataTransfer.files[0]);
        }
    });

    uploadButton.addEventListener("click", () => {
        if (!uploadState.selectedFile) {
            return;
        }
        uploadPrescription();
    });

    document.getElementById("new-upload-btn")?.addEventListener("click", () => {
        resetUploadState();
    });

    refreshDocumentsBtn?.addEventListener("click", loadDocuments);
    confirmDeleteDocumentBtn?.addEventListener("click", confirmDeleteDocument);

    loadDocuments();
});

function loadFile(file) {
    const api = window.HealthAI;
    const allowed = ["application/pdf", "image/png", "image/jpeg"];
    const allowedExtensions = [".pdf", ".png", ".jpg", ".jpeg"];
    const fileName = (file.name || "").toLowerCase();
    const hasAllowedExtension = allowedExtensions.some((extension) => fileName.endsWith(extension));

    if (!allowed.includes(file.type) && !hasAllowedExtension) {
        api.showToast("Only PDF, JPG, and PNG files are allowed.", "error", "Upload");
        return;
    }

    const uploadButton = document.getElementById("upload-btn");
    uploadState.selectedFile = file;
    uploadButton.disabled = false;
    renderPreview(file);
}

function renderPreview(file) {
    const api = window.HealthAI;
    const preview = document.getElementById("preview-content");
    const size = (file.size / 1024 / 1024).toFixed(2);

    if (file.type === "application/pdf") {
        preview.innerHTML = `
            <div class="preview-file animate-fade-up">
                <div class="file-pill">
                    <i class="fa-solid fa-file-pdf"></i>
                    PDF document
                </div>
                <h5 class="mt-3 mb-2">${api.escapeHtml(file.name)}</h5>
                <div class="preview-meta">
                    <p><strong>Type:</strong> PDF</p>
                    <p class="mb-0"><strong>Size:</strong> ${size} MB</p>
                </div>
            </div>
        `;
        return;
    }

    const reader = new FileReader();
    reader.onload = (event) => {
        preview.innerHTML = `
            <div class="preview-file animate-fade-up">
                <img src="${event.target.result}" alt="Preview" class="preview-image">
                <div class="preview-meta mt-3">
                    <p><strong>Name:</strong> ${api.escapeHtml(file.name)}</p>
                    <p><strong>Type:</strong> Image</p>
                    <p class="mb-0"><strong>Size:</strong> ${size} MB</p>
                </div>
            </div>
        `;
    };
    reader.readAsDataURL(file);
}

async function loadDocuments() {
    const api = window.HealthAI;
    const container = document.getElementById("document-list");

    if (!container) {
        return;
    }

    api.renderSkeleton(container, 3, 2);
    try {
        const documents = await api.apiGet("/api/documents/");
        uploadState.documents = Array.isArray(documents) ? documents : [];
        renderDocumentList();
    } catch (error) {
        api.renderEmptyState(
            container,
            "fa-solid fa-folder-open",
            "Unable to load documents",
            error.message || "Existing uploads could not be loaded."
        );
    }
}

function renderDocumentList() {
    const api = window.HealthAI;
    const container = document.getElementById("document-list");
    const documents = uploadState.documents || [];

    if (!documents.length) {
        api.renderEmptyState(
            container,
            "fa-solid fa-file-circle-plus",
            "No uploaded documents",
            "Uploaded files will appear here so you can review or delete them."
        );
        return;
    }

    container.innerHTML = documents.map((item) => `
        <div class="reminder-card animate-fade-up mb-3">
            <div class="d-flex justify-content-between align-items-start gap-3 flex-wrap">
                <div>
                    <div class="reminder-title">${api.escapeHtml(item.title || item.file?.split("/").pop() || "Uploaded file")}</div>
                    <div class="reminder-meta">${api.escapeHtml(item.document_type || "Document")} • ${api.escapeHtml(api.formatDateTime(item.uploaded_at))}</div>
                    <div class="d-flex flex-wrap gap-2 mt-2">
                        <span class="badge bg-primary rounded-pill">${api.escapeHtml(api.formatStatusText(item.status || "Uploaded"))}</span>
                        ${item.needs_review ? '<span class="badge bg-warning text-dark rounded-pill">Needs review</span>' : ""}
                    </div>
                </div>
                <div class="d-flex gap-2">
                    <button class="btn btn-outline-danger btn-sm delete-document-btn" type="button" data-id="${item.id}">
                        <i class="fa-regular fa-trash-can me-1"></i>Delete
                    </button>
                </div>
            </div>
        </div>
    `).join("");

    container.querySelectorAll(".delete-document-btn").forEach((button) => {
        button.addEventListener("click", () => openDeleteDocumentModal(Number(button.dataset.id)));
    });
}

function openDeleteDocumentModal(id) {
    document.getElementById("delete-document-id").value = id;
    bootstrap.Modal.getOrCreateInstance(document.getElementById("deleteDocumentModal")).show();
}

async function confirmDeleteDocument() {
    const api = window.HealthAI;
    const id = Number(document.getElementById("delete-document-id").value);
    const button = document.getElementById("confirm-delete-document-btn");

    api.setButtonLoading(button, true, "Deleting");
    try {
        await api.apiDelete(`/api/documents/${id}/`);
        bootstrap.Modal.getOrCreateInstance(document.getElementById("deleteDocumentModal")).hide();
        api.showToast("Document deleted successfully.", "success", "Upload");
        await loadDocuments();
    } catch (error) {
        api.showToast(error.message || "Unable to delete document.", "error", "Upload");
    } finally {
        api.setButtonLoading(button, false);
    }
}

function uploadPrescription() {
    const api = window.HealthAI;
    const uploadButton = document.getElementById("upload-btn");
    const progressSection = document.getElementById("progress-section");
    const progressBar = document.getElementById("upload-progress");
    const spinner = document.getElementById("upload-spinner");
    const helperText = document.getElementById("upload-helper");
    const statusCard = document.getElementById("status-card");
    const statusList = document.getElementById("status-list");
    const resultCard = document.getElementById("result-card");
    const documentType = document.getElementById("document-type");
    const documentTitle = document.getElementById("document-title");
    const documentDescription = document.getElementById("document-description");

    if (!uploadState.selectedFile) {
        return;
    }

    uploadButton.disabled = true;
    spinner.classList.remove("d-none");
    progressSection.style.display = "block";
    statusCard.style.display = "block";
    resultCard.style.display = "none";
    statusList.innerHTML = "";
    helperText.textContent = "Uploading and extracting text...";

    const formData = new FormData();
    formData.append("file", uploadState.selectedFile);
    formData.append("document_type", documentType?.value || "Other");
    formData.append("title", documentTitle?.value || "");
    formData.append("description", documentDescription?.value || "");

    const xhr = new XMLHttpRequest();
    xhr.open("POST", "/api/documents/upload/", true);
    xhr.setRequestHeader("X-CSRFToken", api.getCsrfToken());

    xhr.upload.onprogress = (event) => {
        if (!event.lengthComputable) {
            return;
        }

        const percent = Math.round((event.loaded / event.total) * 100);
        progressBar.style.width = `${percent}%`;
        progressBar.textContent = `${percent}%`;
    };

    xhr.onload = () => {
        spinner.classList.add("d-none");
        helperText.textContent = "Processing complete";

        let response = {};
        try {
            response = JSON.parse(xhr.responseText || "{}");
        } catch (error) {
            response = {};
        }

        if (xhr.status === 201) {
            renderUploadResult(response);
            api.showToast("Document processed successfully.", "success", "Upload");
            loadDocuments();
            return;
        }

        statusList.innerHTML = `
            <li class="text-danger">
                ${api.escapeHtml(response.message || "Upload failed.")}
            </li>
        `;
        uploadButton.disabled = false;
        api.showToast(response.message || "Upload failed.", "error", "Upload");
    };

    xhr.onerror = () => {
        spinner.classList.add("d-none");
        helperText.textContent = "Network error";
        statusList.innerHTML = `<li class="text-danger">Network error while uploading.</li>`;
        uploadButton.disabled = false;
        api.showToast("Network error while uploading.", "error", "Upload");
    };

    xhr.send(formData);
}

function renderUploadResult(data) {
    const api = window.HealthAI;
    const resultCard = document.getElementById("result-card");
    const summary = document.getElementById("summary-cards");
    const timeline = document.getElementById("timeline");
    const documentInfo = document.getElementById("document-info");
    const prescriptionInfo = document.getElementById("prescription-info");
    const medicineTable = document.getElementById("medicine-table");
    const aiResult = document.getElementById("ai-result");
    const resultStatus = document.getElementById("result-status");
    const statusList = document.getElementById("status-list");
    const savePrescriptionBtn = document.getElementById("save-prescription-btn");
    const saveAppointmentBtn = document.getElementById("save-appointment-btn");
    const saveReportBtn = document.getElementById("save-report-btn");
    const viewResultBtn = document.getElementById("view-medicines-btn");

    resultCard.style.display = "block";
    uploadState.latestUpload = data;
    resultStatus.textContent = api.formatStatusText(data.status || "Completed");
    statusList.innerHTML = `
        <li>File uploaded successfully.</li>
        <li>Document extraction completed.</li>
        <li>Backend records updated.</li>
    `;

    const workflow = data.workflow_result || {};
    const draftPayload = data.editable_payload || data.structured_payload || {};
    const workflowType = workflow.type || data.document_type || draftPayload.document_type || "";
    const medicines = Array.isArray(workflow.medicines) && workflow.medicines.length
        ? workflow.medicines
        : (Array.isArray(draftPayload.medicines) ? draftPayload.medicines : []);
    const isPrescriptionDraft = !workflow.prescription && workflowType === "Prescription";
    const isAppointmentDraft = !workflow.appointment && workflowType === "Appointment" && hasAppointmentDraftValues(draftPayload);
    const isReportDraft = !workflow.report && ["Health Report", "Blood Report", "MRI", "ECG", "X-Ray", "Other"].includes(workflowType) && hasReportDraftValues(draftPayload);

    if (savePrescriptionBtn) {
        savePrescriptionBtn.classList.toggle("d-none", !isPrescriptionDraft);
    }
    if (saveAppointmentBtn) {
        saveAppointmentBtn.classList.toggle("d-none", !isAppointmentDraft);
    }
    if (saveReportBtn) {
        saveReportBtn.classList.toggle("d-none", !isReportDraft);
    }
    if (viewResultBtn) {
        const hasCreatedRecord = Boolean(workflow.prescription || workflow.appointment || workflow.report);
        viewResultBtn.classList.toggle("d-none", !hasCreatedRecord);
        if (hasCreatedRecord) {
            configureResultAction(viewResultBtn, workflow, data);
        }
    }

    summary.innerHTML = `
        <div class="col-md-3">
            <div class="summary-box">
                <i class="fa-solid fa-file-medical fa-2x text-primary"></i>
                <h3>${api.escapeHtml(data.document_id ?? "-")}</h3>
                <p>Document ID</p>
            </div>
        </div>
        <div class="col-md-3">
            <div class="summary-box">
                <i class="fa-solid fa-file-waveform fa-2x text-success"></i>
                <h3>${api.escapeHtml(data.document_type || workflowType || "-")}</h3>
                <p>Document Type</p>
            </div>
        </div>
        <div class="col-md-3">
            <div class="summary-box">
                <i class="fa-solid fa-pills fa-2x text-warning"></i>
                <h3>${api.escapeHtml(data.medicine_count ?? medicines.length ?? 0)}</h3>
                <p>Medicines</p>
            </div>
        </div>
        <div class="col-md-3">
            <div class="summary-box">
                <i class="fa-solid fa-clock fa-2x text-success"></i>
                <h3>${api.escapeHtml(data.processing_time ?? "-")}</h3>
                <p>Seconds</p>
            </div>
        </div>
        <div class="col-md-3">
            <div class="summary-box">
                <i class="fa-solid fa-file-waveform fa-2x text-info"></i>
                <h3>${api.escapeHtml(workflowType || "-")}</h3>
                <p>Workflow</p>
            </div>
        </div>
    `;

    timeline.innerHTML = `
        <div class="timeline-item"><i class="fa-solid fa-check success-icon"></i>Document uploaded</div>
        <div class="timeline-item"><i class="fa-solid fa-check success-icon"></i>Document extraction completed</div>
        <div class="timeline-item"><i class="fa-solid fa-check success-icon"></i>Backend workflow completed</div>
    `;

    documentInfo.innerHTML = `
        <div class="detail-row">
            <span class="detail-label">File name</span>
            <span class="detail-value">${api.escapeHtml(data.document?.file ? data.document.file.split("/").pop() : uploadState.selectedFile?.name || "-")}</span>
        </div>
        <div class="detail-row">
            <span class="detail-label">Status</span>
            <span class="detail-value">${api.escapeHtml(api.formatStatusText(data.status || "-"))}</span>
        </div>
        <div class="detail-row">
            <span class="detail-label">Patient</span>
            <span class="detail-value">${api.escapeHtml(data.document?.patient_name || "-")}</span>
        </div>
        <div class="detail-row">
            <span class="detail-label">Uploaded at</span>
            <span class="detail-value">${api.escapeHtml(api.formatDateTime(data.document?.uploaded_at))}</span>
        </div>
        <div class="detail-row">
            <span class="detail-label">Confidence</span>
            <span class="detail-value">${api.escapeHtml(data.classification_confidence ?? data.structured_payload?.ocr_confidence ?? data.vision_confidence ?? 0)}</span>
        </div>
    `;

    if (workflow.prescription) {
        prescriptionInfo.innerHTML = renderPrescriptionDetails(workflow.prescription);
        medicineTable.innerHTML = renderMedicinesTable(medicines);
    } else if (isPrescriptionDraft) {
        prescriptionInfo.innerHTML = renderPrescriptionDraftDetails(data);
        medicineTable.innerHTML = renderEditableMedicinesTable(medicines);
        bindDraftMedicineControls();
    } else if (workflow.appointment) {
        prescriptionInfo.innerHTML = renderAppointmentDetails(workflow.appointment);
        medicineTable.innerHTML = renderAppointmentResultState();
    } else if (isAppointmentDraft) {
        prescriptionInfo.innerHTML = renderAppointmentDraftDetails(draftPayload);
        medicineTable.innerHTML = renderAppointmentResultState(true);
    } else if (workflow.report) {
        prescriptionInfo.innerHTML = renderReportDetails(workflow.report);
        medicineTable.innerHTML = renderReportResultState();
    } else if (isReportDraft) {
        prescriptionInfo.innerHTML = renderReportDraftDetails(draftPayload);
        medicineTable.innerHTML = renderReportResultState(true);
    } else {
        prescriptionInfo.innerHTML = `
            <div class="empty-state">
                <i class="fa-solid fa-circle-info"></i>
                <h5 class="mb-2">No structured data returned</h5>
                <p class="mb-0">The backend completed document extraction, but no workflow payload was created.</p>
            </div>
        `;
        medicineTable.innerHTML = `
            <div class="empty-state">
                <i class="fa-solid fa-table-cells-large"></i>
                <h5 class="mb-2">No extraction available</h5>
                <p class="mb-0">Try another document or adjust the document type.</p>
            </div>
        `;
    }

    aiResult.value = JSON.stringify(data.structured_payload || {}, null, 2);
}

function configureResultAction(button, workflow, data) {
    if (!button) {
        return;
    }

    const type = workflow.type || data.document_type || data.structured_payload?.document_type || "";
    if (type === "Appointment") {
        button.href = "/appointments/";
        button.textContent = "View appointments";
        return;
    }
    if (["Health Report", "Blood Report", "MRI", "ECG", "X-Ray", "Other"].includes(type)) {
        button.href = "/reports/";
        button.textContent = "View reports";
        return;
    }
    button.href = "/medicines/";
    button.textContent = "View medicines";
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

function normalizePrescriptionLine(value) {
    return String(value || "")
        .replaceAll("Moming", "Morning")
        .replaceAll("moming", "morning")
        .replaceAll("Tot:", "T:")
        .replaceAll("Tott:", "T:")
        .replace(/\s+/g, " ")
        .trim()
        .replace(/^[-: ]+|[-: ]+$/g, "");
}

function frequencyFromDosage(dosage) {
    const text = String(dosage || "").toLowerCase().replaceAll("moming", "morning");
    const markers = [
        ["morning", "Morning"],
        ["morn", "Morning"],
        ["afternoon", "Afternoon"],
        ["aft", "Afternoon"],
        ["evening", "Evening"],
        ["eve", "Evening"],
        ["night", "Night"],
    ];
    return markers.reduce((items, [marker, label]) => {
        const pattern = new RegExp(`\\b${marker}\\b`, "i");
        if (pattern.test(text) && !items.includes(label)) {
            items.push(label);
        }
        return items;
    }, []);
}

function foodInstructionFromText(value) {
    const text = String(value || "").toLowerCase();
    if (text.includes("before food")) {
        return "Before Food";
    }
    if (text.includes("after food")) {
        return "After Food";
    }
    if (text.includes("with food")) {
        return "With Food";
    }
    return "";
}

function parseMedicineRowFromText(rowText) {
    const row = normalizePrescriptionLine(rowText).replace(/^\d+\)\s*/, "");
    const nameMatch = row.match(/((?:(?:TAB|CAP|SYP|SYR|INJ)\.?\s*)?[A-Z0-9][A-Z0-9 .&/-]*?)(?=\s+\d+(?:\/\d+)?\s*(?:Morning|Moming|Morn|Aft|Afternoon|Eve|Evening|Night)\b)/i);
    const durationMatch = row.match(/\d+\s*(?:Days?|Weeks?|Months?)\s*(?:\([^)]*\))?/i);

    if (!nameMatch || !durationMatch) {
        return null;
    }

    const name = normalizePrescriptionLine(nameMatch[1]);
    const dosage = normalizePrescriptionLine(row.slice(nameMatch.index + nameMatch[0].length, durationMatch.index));
    const duration = normalizePrescriptionLine(durationMatch[0]);
    const trailingInstruction = normalizePrescriptionLine(row.slice(durationMatch.index + durationMatch[0].length));

    if (!name || !dosage) {
        return null;
    }

    return {
        medicine_name: name,
        dosage,
        quantity: 1,
        frequency: frequencyFromDosage(dosage),
        food_instruction: foodInstructionFromText(`${dosage} ${duration} ${trailingInstruction}`),
        duration,
        strength: "",
        special_instruction: "",
    };
}

function parseMedicinesFromText(text) {
    const source = String(text || "");
    const rowMatches = [...source.matchAll(/(?:^|\n)\s*\d+\)\s*/g)];
    return rowMatches.map((match, index) => {
        const next = rowMatches[index + 1];
        const rowStart = match.index;
        const rowEnd = next ? next.index : source.length;
        const rowText = source
            .slice(rowStart, rowEnd)
            .split(/\n\s*(?:Advice\s+Given|Follow\s*Up|Charts|Signature)\b/i)[0];
        return parseMedicineRowFromText(rowText);
    }).filter(Boolean);
}

function hasDraftMedicineValues() {
    return [...document.querySelectorAll(".draft-medicine-field[data-field='medicine_name']")]
        .some((field) => field.value.trim());
}

function syncMedicinesFromText() {
    const aiResult = document.getElementById("ai-result");
    const medicineTable = document.getElementById("medicine-table");
    if (!aiResult || !medicineTable || hasDraftMedicineValues()) {
        return;
    }

    const medicines = parseMedicinesFromText(aiResult.value);
    if (!medicines.length) {
        return;
    }

    medicineTable.innerHTML = renderEditableMedicinesTable(medicines);
    bindDraftMedicineControls();
}

function renderPrescriptionDraftDetails(data) {
    const api = window.HealthAI;
    const draft = data.editable_payload || data.structured_payload || {};
    return `
        <input type="hidden" id="draft-document-id" value="${api.escapeHtml(data.document_id ?? "")}">
        <div class="detail-row">
            <span class="detail-label">Document type</span>
            <span class="detail-value">${api.escapeHtml(data.document_type || draft.document_type || "-")}</span>
        </div>
        <div class="detail-row">
            <label class="detail-label" for="draft-doctor-name">Doctor</label>
            <input type="text" class="form-control form-control-sm" id="draft-doctor-name" value="${api.escapeHtml(draft.doctor_name || "")}">
        </div>
        <div class="detail-row">
            <label class="detail-label" for="draft-hospital-name">Hospital</label>
            <input type="text" class="form-control form-control-sm" id="draft-hospital-name" value="${api.escapeHtml(draft.hospital_name || "")}">
        </div>
        <div class="detail-row">
            <label class="detail-label" for="draft-diagnosis">Diagnosis</label>
            <input type="text" class="form-control form-control-sm" id="draft-diagnosis" value="${api.escapeHtml(draft.diagnosis || "")}">
        </div>
        <div class="detail-row">
            <label class="detail-label" for="draft-prescription-date">Prescription date</label>
            <input type="date" class="form-control form-control-sm" id="draft-prescription-date" value="${api.escapeHtml(draft.prescription_date || "")}">
        </div>
        <div class="detail-row">
            <label class="detail-label" for="draft-review-date">Review date</label>
            <input type="date" class="form-control form-control-sm" id="draft-review-date" value="${api.escapeHtml(draft.review_date || "")}">
        </div>
        <div class="detail-row">
            <label class="detail-label" for="draft-notes">Notes</label>
            <textarea class="form-control form-control-sm" id="draft-notes" rows="3">${api.escapeHtml(draft.notes || "")}</textarea>
        </div>
    `;
}

function renderPrescriptionDetails(prescription) {
    const api = window.HealthAI;
    return `
        <div class="detail-row">
            <span class="detail-label">Doctor</span>
            <span class="detail-value">${api.escapeHtml(prescription.doctor_name || "-")}</span>
        </div>
        <div class="detail-row">
            <span class="detail-label">Hospital</span>
            <span class="detail-value">${api.escapeHtml(prescription.hospital_name || "-")}</span>
        </div>
        <div class="detail-row">
            <span class="detail-label">Diagnosis</span>
            <span class="detail-value">${api.escapeHtml(prescription.diagnosis || "-")}</span>
        </div>
        <div class="detail-row">
            <span class="detail-label">Prescription date</span>
            <span class="detail-value">${api.escapeHtml(api.formatDate(prescription.prescription_date))}</span>
        </div>
        <div class="detail-row">
            <span class="detail-label">Review date</span>
            <span class="detail-value">${api.escapeHtml(api.formatDate(prescription.review_date))}</span>
        </div>
        <div class="detail-row">
            <span class="detail-label">Notes</span>
            <span class="detail-value">${api.escapeHtml(prescription.notes || "-")}</span>
        </div>
    `;
}

function renderAppointmentDetails(appointment) {
    const api = window.HealthAI;
    return `
        <div class="detail-row">
            <span class="detail-label">Doctor</span>
            <span class="detail-value">${api.escapeHtml(appointment.doctor_name || "-")}</span>
        </div>
        <div class="detail-row">
            <span class="detail-label">Hospital</span>
            <span class="detail-value">${api.escapeHtml(appointment.hospital_name || "-")}</span>
        </div>
        <div class="detail-row">
            <span class="detail-label">Department</span>
            <span class="detail-value">${api.escapeHtml(appointment.department || "-")}</span>
        </div>
        <div class="detail-row">
            <span class="detail-label">Appointment date</span>
            <span class="detail-value">${api.escapeHtml(api.formatDate(appointment.appointment_date))}</span>
        </div>
        <div class="detail-row">
            <span class="detail-label">Appointment time</span>
            <span class="detail-value">${api.escapeHtml(api.formatTime(appointment.appointment_time))}</span>
        </div>
        <div class="detail-row">
            <span class="detail-label">Purpose</span>
            <span class="detail-value">${api.escapeHtml(appointment.purpose || "-")}</span>
        </div>
        <div class="detail-row">
            <span class="detail-label">Notes</span>
            <span class="detail-value">${api.escapeHtml(appointment.notes || "-")}</span>
        </div>
    `;
}

function renderAppointmentDraftDetails(draft) {
    const api = window.HealthAI;
    return `
        <input type="hidden" id="draft-document-id" value="${api.escapeHtml(draft.document_id ?? "")}">
        <div class="detail-row">
            <span class="detail-label">Document type</span>
            <span class="detail-value">${api.escapeHtml(draft.document_type || "Appointment")}</span>
        </div>
        <div class="detail-row">
            <label class="detail-label" for="draft-appointment-doctor">Doctor</label>
            <input type="text" class="form-control form-control-sm" id="draft-appointment-doctor" value="${api.escapeHtml(draft.doctor_name || "")}">
        </div>
        <div class="detail-row">
            <label class="detail-label" for="draft-appointment-hospital">Hospital</label>
            <input type="text" class="form-control form-control-sm" id="draft-appointment-hospital" value="${api.escapeHtml(draft.hospital_name || "")}">
        </div>
        <div class="detail-row">
            <label class="detail-label" for="draft-appointment-department">Department</label>
            <input type="text" class="form-control form-control-sm" id="draft-appointment-department" value="${api.escapeHtml(draft.department || "")}">
        </div>
        <div class="detail-row">
            <label class="detail-label" for="draft-appointment-date">Appointment date</label>
            <input type="date" class="form-control form-control-sm" id="draft-appointment-date" value="${api.escapeHtml(draft.appointment_date || "")}">
        </div>
        <div class="detail-row">
            <label class="detail-label" for="draft-appointment-time">Appointment time</label>
            <input type="time" class="form-control form-control-sm" id="draft-appointment-time" value="${api.escapeHtml(draft.appointment_time || "")}">
        </div>
        <div class="detail-row">
            <label class="detail-label" for="draft-appointment-purpose">Purpose</label>
            <textarea class="form-control form-control-sm" id="draft-appointment-purpose" rows="3">${api.escapeHtml(draft.purpose || "")}</textarea>
        </div>
        <div class="detail-row">
            <label class="detail-label" for="draft-appointment-notes">Notes</label>
            <textarea class="form-control form-control-sm" id="draft-appointment-notes" rows="3">${api.escapeHtml(draft.notes || "")}</textarea>
        </div>
    `;
}

function renderReportDetails(report) {
    const api = window.HealthAI;
    return `
        <div class="detail-row">
            <span class="detail-label">Report type</span>
            <span class="detail-value">${api.escapeHtml(report.report_type_display || report.report_type || "-")}</span>
        </div>
        <div class="detail-row">
            <span class="detail-label">Title</span>
            <span class="detail-value">${api.escapeHtml(report.report_title || "-")}</span>
        </div>
        <div class="detail-row">
            <span class="detail-label">Summary</span>
            <span class="detail-value">${api.escapeHtml(report.summary || report.report_summary || "-")}</span>
        </div>
        <div class="detail-row">
            <span class="detail-label">Findings</span>
            <span class="detail-value">${api.escapeHtml(report.findings || "-")}</span>
        </div>
        <div class="detail-row">
            <span class="detail-label">Recommendations</span>
            <span class="detail-value">${api.escapeHtml(report.recommendations || "-")}</span>
        </div>
        <div class="detail-row">
            <span class="detail-label">Report date</span>
            <span class="detail-value">${api.escapeHtml(api.formatDate(report.report_date))}</span>
        </div>
        <div class="detail-row">
            <span class="detail-label">Notes</span>
            <span class="detail-value">${api.escapeHtml(report.notes || "-")}</span>
        </div>
    `;
}

function renderReportDraftDetails(draft) {
    const api = window.HealthAI;
    const reportType = draft.report_type || draft.document_type || "Other";
    return `
        <input type="hidden" id="draft-document-id" value="${api.escapeHtml(draft.document_id ?? "")}">
        <div class="detail-row">
            <label class="detail-label" for="draft-report-type">Report type</label>
            <select class="form-select form-select-sm" id="draft-report-type">
                ${["Blood Report", "MRI", "ECG", "X-Ray", "Other"].map((type) => `
                    <option value="${api.escapeHtml(type)}" ${type === reportType ? "selected" : ""}>${api.escapeHtml(type)}</option>
                `).join("")}
            </select>
        </div>
        <div class="detail-row">
            <label class="detail-label" for="draft-report-title">Title</label>
            <input type="text" class="form-control form-control-sm" id="draft-report-title" value="${api.escapeHtml(draft.report_title || "")}">
        </div>
        <div class="detail-row">
            <label class="detail-label" for="draft-report-summary">Summary</label>
            <textarea class="form-control form-control-sm" id="draft-report-summary" rows="3">${api.escapeHtml(draft.summary || draft.report_summary || "")}</textarea>
        </div>
        <div class="detail-row">
            <label class="detail-label" for="draft-report-findings">Findings</label>
            <textarea class="form-control form-control-sm" id="draft-report-findings" rows="3">${api.escapeHtml(draft.findings || "")}</textarea>
        </div>
        <div class="detail-row">
            <label class="detail-label" for="draft-report-recommendations">Recommendations</label>
            <textarea class="form-control form-control-sm" id="draft-report-recommendations" rows="3">${api.escapeHtml(draft.recommendations || "")}</textarea>
        </div>
        <div class="detail-row">
            <label class="detail-label" for="draft-report-date">Report date</label>
            <input type="date" class="form-control form-control-sm" id="draft-report-date" value="${api.escapeHtml(draft.report_date || "")}">
        </div>
        <div class="detail-row">
            <label class="detail-label" for="draft-report-notes">Notes</label>
            <textarea class="form-control form-control-sm" id="draft-report-notes" rows="3">${api.escapeHtml(draft.notes || "")}</textarea>
        </div>
    `;
}

function hasAppointmentDraftValues(draft) {
    return ["doctor_name", "hospital_name", "department", "appointment_date", "appointment_time", "purpose", "notes"]
        .some((field) => String(draft?.[field] || "").trim());
}

function hasReportDraftValues(draft) {
    return ["report_title", "summary", "report_summary", "findings", "recommendations", "report_date", "notes"]
        .some((field) => String(draft?.[field] || "").trim());
}

function renderAppointmentResultState(isDraft = false) {
    const title = isDraft ? "Ready to create appointment" : "This upload was processed as an appointment.";
    const description = isDraft
        ? "Review the extracted visit details and create the appointment record."
        : "The appointment record was saved and can be reviewed from Appointments.";
    return `
        <div class="empty-state">
            <i class="fa-solid fa-calendar-check"></i>
            <h5 class="mb-2">${title}</h5>
            <p class="mb-0">${description}</p>
        </div>
    `;
}

function renderReportResultState(isDraft = false) {
    const title = isDraft ? "Ready to create report" : "Report created";
    const description = isDraft
        ? "Review the extracted report details and create the report record."
        : "The report record was saved and can be reviewed from Reports.";
    return `
        <div class="empty-state">
            <i class="fa-solid fa-file-waveform"></i>
            <h5 class="mb-2">${title}</h5>
            <p class="mb-0">${description}</p>
        </div>
    `;
}

function collectAppointmentDraft() {
    return {
        document_id: Number(document.getElementById("draft-document-id")?.value || 0) || null,
        doctor_name: document.getElementById("draft-appointment-doctor")?.value.trim() || "",
        hospital_name: document.getElementById("draft-appointment-hospital")?.value.trim() || "",
        department: document.getElementById("draft-appointment-department")?.value.trim() || "",
        appointment_date: document.getElementById("draft-appointment-date")?.value || null,
        appointment_time: document.getElementById("draft-appointment-time")?.value || null,
        purpose: document.getElementById("draft-appointment-purpose")?.value.trim() || "",
        notes: document.getElementById("draft-appointment-notes")?.value.trim() || "",
    };
}

function collectReportDraft() {
    return {
        document_id: Number(document.getElementById("draft-document-id")?.value || 0) || null,
        report_type: document.getElementById("draft-report-type")?.value || "Other",
        report_title: document.getElementById("draft-report-title")?.value.trim() || "",
        summary: document.getElementById("draft-report-summary")?.value.trim() || "",
        findings: document.getElementById("draft-report-findings")?.value.trim() || "",
        recommendations: document.getElementById("draft-report-recommendations")?.value.trim() || "",
        report_date: document.getElementById("draft-report-date")?.value || null,
        notes: document.getElementById("draft-report-notes")?.value.trim() || "",
    };
}

async function saveAppointmentDraft() {
    const api = window.HealthAI;
    const button = document.getElementById("save-appointment-btn");
    const payload = collectAppointmentDraft();

    if (!payload.doctor_name && !payload.purpose) {
        api.showToast("Add appointment details before creating the record.", "error", "Upload");
        return;
    }

    api.setButtonLoading(button, true, "Creating");
    try {
        const response = await api.apiPost("/api/appointments/manual/", payload);
        api.showToast("Appointment created successfully.", "success", "Upload");
        renderCreatedAppointmentResult(response);
    } catch (error) {
        api.showToast(error.message || "Unable to create appointment.", "error", "Upload");
    } finally {
        api.setButtonLoading(button, false);
    }
}

async function saveReportDraft() {
    const api = window.HealthAI;
    const button = document.getElementById("save-report-btn");
    const payload = collectReportDraft();

    if (!payload.document_id) {
        api.showToast("The report needs a linked document before creation.", "error", "Upload");
        return;
    }

    api.setButtonLoading(button, true, "Creating");
    try {
        const response = await api.apiPost("/api/reports/manual/", payload);
        api.showToast("Report created successfully.", "success", "Upload");
        renderCreatedReportResult(response);
    } catch (error) {
        api.showToast(error.message || "Unable to create report.", "error", "Upload");
    } finally {
        api.setButtonLoading(button, false);
    }
}

function renderCreatedAppointmentResult(response) {
    const api = window.HealthAI;
    const prescriptionInfo = document.getElementById("prescription-info");
    const medicineTable = document.getElementById("medicine-table");
    const saveAppointmentBtn = document.getElementById("save-appointment-btn");
    const viewResultBtn = document.getElementById("view-medicines-btn");
    if (saveAppointmentBtn) {
        saveAppointmentBtn.classList.add("d-none");
    }
    if (viewResultBtn) {
        viewResultBtn.classList.remove("d-none");
        viewResultBtn.href = "/appointments/";
        viewResultBtn.textContent = "View appointments";
    }
    if (prescriptionInfo) {
        prescriptionInfo.innerHTML = `
            <div class="detail-row">
                <span class="detail-label">Appointment</span>
                <span class="detail-value">Created successfully</span>
            </div>
            <div class="detail-row">
                <span class="detail-label">Doctor</span>
                <span class="detail-value">${api.escapeHtml(response.appointment?.doctor_name || "-")}</span>
            </div>
        `;
    }
    if (medicineTable) {
        medicineTable.innerHTML = renderAppointmentResultState();
    }
}

function renderCreatedReportResult(response) {
    const api = window.HealthAI;
    const prescriptionInfo = document.getElementById("prescription-info");
    const medicineTable = document.getElementById("medicine-table");
    const saveReportBtn = document.getElementById("save-report-btn");
    const viewResultBtn = document.getElementById("view-medicines-btn");
    if (saveReportBtn) {
        saveReportBtn.classList.add("d-none");
    }
    if (viewResultBtn) {
        viewResultBtn.classList.remove("d-none");
        viewResultBtn.href = "/reports/";
        viewResultBtn.textContent = "View reports";
    }
    if (prescriptionInfo) {
        prescriptionInfo.innerHTML = `
            <div class="detail-row">
                <span class="detail-label">Report</span>
                <span class="detail-value">Created successfully</span>
            </div>
            <div class="detail-row">
                <span class="detail-label">Title</span>
                <span class="detail-value">${api.escapeHtml(response.report?.report_title || "-")}</span>
            </div>
        `;
    }
    if (medicineTable) {
        medicineTable.innerHTML = renderReportResultState();
    }
}

function renderCreatedPrescriptionResult(response) {
    const api = window.HealthAI;
    const prescriptionInfo = document.getElementById("prescription-info");
    const medicineTable = document.getElementById("medicine-table");
    const savePrescriptionBtn = document.getElementById("save-prescription-btn");
    const saveAppointmentBtn = document.getElementById("save-appointment-btn");
    const saveReportBtn = document.getElementById("save-report-btn");
    const viewResultBtn = document.getElementById("view-medicines-btn");
    if (savePrescriptionBtn) {
        savePrescriptionBtn.classList.add("d-none");
    }
    if (saveAppointmentBtn) {
        saveAppointmentBtn.classList.add("d-none");
    }
    if (saveReportBtn) {
        saveReportBtn.classList.add("d-none");
    }
    if (viewResultBtn) {
        viewResultBtn.classList.remove("d-none");
        viewResultBtn.href = "/medicines/";
        viewResultBtn.textContent = "View medicines";
    }
    if (prescriptionInfo) {
        prescriptionInfo.innerHTML = `
            <div class="detail-row">
                <span class="detail-label">Prescription</span>
                <span class="detail-value">Created successfully</span>
            </div>
            <div class="detail-row">
                <span class="detail-label">Medicines</span>
                <span class="detail-value">${api.escapeHtml(response.medicine_count ?? 0)}</span>
            </div>
        `;
    }
    if (medicineTable) {
        medicineTable.innerHTML = `
            <div class="empty-state">
                <i class="fa-solid fa-circle-check"></i>
                <h5 class="mb-2">Prescription saved</h5>
                <p class="mb-0">Your medicines and schedules have been created. You can now view them in the Medicines page.</p>
            </div>
        `;
    }
}

function renderEditableMedicinesTable(medicines) {
    const api = window.HealthAI;
    if (!medicines.length) {
        return `
            <div class="table-responsive medicine-table">
                <table class="table table-hover align-middle">
                    <thead>
                        <tr>
                            <th>Medicine</th>
                            <th>Dosage</th>
                            <th>Frequency</th>
                            <th>Duration</th>
                            <th>Strength</th>
                            <th>Action</th>
                        </tr>
                    </thead>
                    <tbody id="draft-medicine-body">
                        ${renderDraftMedicineRow({}, 0)}
                    </tbody>
                </table>
            </div>
            <div class="d-flex justify-content-between align-items-center mt-2">
                <div class="text-muted">No medicines were extracted. Add them manually.</div>
                <button class="btn btn-outline-primary btn-sm" type="button" id="add-draft-medicine-btn">
                    <i class="fa-solid fa-plus me-1"></i>Add medicine
                </button>
            </div>
        `;
    }

    return `
        <div class="table-responsive medicine-table">
            <table class="table table-hover align-middle">
                <thead>
                    <tr>
                        <th>Medicine</th>
                        <th>Dosage</th>
                        <th>Frequency</th>
                        <th>Duration</th>
                        <th>Strength</th>
                        <th>Action</th>
                    </tr>
                </thead>
                <tbody id="draft-medicine-body">
                    ${medicines.map((item, index) => renderDraftMedicineRow(item, index)).join("")}
                </tbody>
            </table>
        </div>
        <div class="d-flex justify-content-end mt-2">
            <button class="btn btn-outline-primary btn-sm" type="button" id="add-draft-medicine-btn">
                <i class="fa-solid fa-plus me-1"></i>Add medicine
            </button>
        </div>
    `;
}

function renderDraftMedicineRow(item, index) {
    const api = window.HealthAI;
    const frequencyValue = Array.isArray(item.frequency) ? item.frequency.join(", ") : (item.frequency || "");
    return `
        <tr class="draft-medicine-row" data-medicine-index="${index}">
            <td><input class="form-control form-control-sm draft-medicine-field" data-index="${index}" data-field="medicine_name" value="${api.escapeHtml(item.medicine_name || "")}"></td>
            <td><input class="form-control form-control-sm draft-medicine-field" data-index="${index}" data-field="dosage" value="${api.escapeHtml(item.dosage || "")}"></td>
            <td><input class="form-control form-control-sm draft-medicine-field" data-index="${index}" data-field="frequency" value="${api.escapeHtml(frequencyValue)}"></td>
            <td><input class="form-control form-control-sm draft-medicine-field" data-index="${index}" data-field="duration" value="${api.escapeHtml(item.duration || "")}"></td>
            <td><input class="form-control form-control-sm draft-medicine-field" data-index="${index}" data-field="strength" value="${api.escapeHtml(item.strength || "")}"></td>
            <td>
                <button class="btn btn-outline-danger btn-sm remove-draft-medicine-btn" type="button" data-index="${index}" title="Remove medicine">
                    <i class="fa-regular fa-trash-can"></i>
                </button>
            </td>
        </tr>
        <tr class="draft-medicine-row" data-medicine-index="${index}">
            <td colspan="6">
                <div class="row g-2">
                    <div class="col-md-4">
                        <label class="form-label mb-1">Food instruction</label>
                        <input class="form-control form-control-sm draft-medicine-field" data-index="${index}" data-field="food_instruction" value="${api.escapeHtml(item.food_instruction || "")}">
                    </div>
                    <div class="col-md-4">
                        <label class="form-label mb-1">Quantity</label>
                        <input type="number" min="1" class="form-control form-control-sm draft-medicine-field" data-index="${index}" data-field="quantity" value="${api.escapeHtml(item.quantity || 1)}">
                    </div>
                    <div class="col-md-4">
                        <label class="form-label mb-1">Special instruction</label>
                        <input class="form-control form-control-sm draft-medicine-field" data-index="${index}" data-field="special_instruction" value="${api.escapeHtml(item.special_instruction || "")}">
                    </div>
                </div>
            </td>
        </tr>
    `;
}

function bindDraftMedicineControls() {
    const addButton = document.getElementById("add-draft-medicine-btn");
    if (addButton) {
        addButton.onclick = appendDraftMedicineRow;
    }
    document.querySelectorAll(".remove-draft-medicine-btn").forEach((button) => {
        button.onclick = () => removeDraftMedicineRow(Number(button.dataset.index));
    });
}

function appendDraftMedicineRow() {
    const tbody = document.getElementById("draft-medicine-body");
    if (!tbody) {
        return;
    }

    const indexes = [...tbody.querySelectorAll(".draft-medicine-field[data-index]")]
        .map((field) => Number(field.dataset.index))
        .filter((value) => Number.isFinite(value));
    const nextIndex = indexes.length ? Math.max(...indexes) + 1 : 0;
    tbody.insertAdjacentHTML("beforeend", renderDraftMedicineRow({}, nextIndex));
    bindDraftMedicineControls();
}

function removeDraftMedicineRow(index) {
    const rows = document.querySelectorAll(`.draft-medicine-row[data-medicine-index="${index}"]`);
    rows.forEach((row) => row.remove());

    const tbody = document.getElementById("draft-medicine-body");
    if (tbody && !tbody.querySelector(".draft-medicine-row")) {
        tbody.insertAdjacentHTML("beforeend", renderDraftMedicineRow({}, 0));
        bindDraftMedicineControls();
    }
}

function collectPrescriptionDraft() {
    const medicineMap = [...document.querySelectorAll(".draft-medicine-field[data-index]")].reduce((acc, field) => {
        const index = Number(field.dataset.index);
        if (!Number.isFinite(index)) {
            return acc;
        }
        if (!acc[index]) {
            acc[index] = {};
        }
        const key = field.dataset.field;
        if (key === "frequency") {
            acc[index][key] = field.value.split(",").map((item) => item.trim()).filter(Boolean);
        } else if (key === "quantity") {
            acc[index][key] = Number(field.value || 1);
        } else {
            acc[index][key] = field.value;
        }
        return acc;
    }, {});
    const medicines = Object.values(medicineMap).filter((item) => (
        item &&
        ["medicine_name", "strength", "dosage", "duration"].some((field) => String(item[field] || "").trim())
    ));

    return {
        document_id: Number(document.getElementById("draft-document-id")?.value || 0) || null,
        doctor_name: document.getElementById("draft-doctor-name")?.value.trim() || "",
        hospital_name: document.getElementById("draft-hospital-name")?.value.trim() || "",
        diagnosis: document.getElementById("draft-diagnosis")?.value.trim() || "",
        prescription_date: document.getElementById("draft-prescription-date")?.value || null,
        review_date: document.getElementById("draft-review-date")?.value || null,
        notes: document.getElementById("draft-notes")?.value.trim() || "",
        medicines,
    };
}

async function savePrescriptionDraft() {
    const api = window.HealthAI;
    const button = document.getElementById("save-prescription-btn");
    const payload = collectPrescriptionDraft();

    if (!payload.medicines.length) {
        api.showToast("Add at least one medicine before creating the prescription.", "error", "Upload");
        return;
    }

    api.setButtonLoading(button, true, "Creating");
    try {
        const response = await api.apiPost("/api/prescriptions/manual/", payload);
        api.showToast("Prescription created successfully.", "success", "Upload");
        renderCreatedPrescriptionResult(response);
    } catch (error) {
        api.showToast(error.message || "Unable to create prescription.", "error", "Upload");
    } finally {
        api.setButtonLoading(button, false);
    }
}

function renderCreatedPrescriptionResult(response) {
    const api = window.HealthAI;
    const prescriptionInfo = document.getElementById("prescription-info");
    const medicineTable = document.getElementById("medicine-table");
    const savePrescriptionBtn = document.getElementById("save-prescription-btn");
    if (savePrescriptionBtn) {
        savePrescriptionBtn.classList.add("d-none");
    }
    if (prescriptionInfo) {
        prescriptionInfo.innerHTML = `
            <div class="detail-row">
                <span class="detail-label">Prescription</span>
                <span class="detail-value">Created successfully</span>
            </div>
            <div class="detail-row">
                <span class="detail-label">Medicines</span>
                <span class="detail-value">${api.escapeHtml(response.medicine_count ?? 0)}</span>
            </div>
        `;
    }
    if (medicineTable) {
        medicineTable.innerHTML = `
            <div class="empty-state">
                <i class="fa-solid fa-circle-check"></i>
                <h5 class="mb-2">Prescription saved</h5>
                <p class="mb-0">Your medicines and schedules have been created. You can now view them in the Medicines page.</p>
            </div>
        `;
    }
}

function renderMedicinesTable(medicines) {
    const api = window.HealthAI;

    if (!medicines.length) {
        return `
            <div class="empty-state">
                <i class="fa-solid fa-pills"></i>
                <h5 class="mb-2">No medicines extracted</h5>
                <p class="mb-0">The AI processed the document but did not return structured medicines.</p>
            </div>
        `;
    }

    return `
        <div class="table-responsive medicine-table">
            <table class="table table-hover align-middle">
                <thead>
                    <tr>
                        <th>Medicine</th>
                        <th>Dosage</th>
                        <th>Frequency</th>
                        <th>Duration</th>
                    </tr>
                </thead>
                <tbody>
                    ${medicines.map((item) => `
                        <tr>
                            <td>${api.escapeHtml(item.medicine_name || "-")}</td>
                            <td>${api.escapeHtml(item.dosage || "-")}</td>
                            <td>${api.escapeHtml((item.frequency || []).join(", ") || "-")}</td>
                            <td>${api.escapeHtml(item.duration || "-")}</td>
                        </tr>
                    `).join("")}
                </tbody>
            </table>
        </div>
    `;
}

function resetUploadState() {
    window.location.reload();
}

document.addEventListener("DOMContentLoaded", () => {
    document.getElementById("save-prescription-btn")?.addEventListener("click", savePrescriptionDraft);
});
