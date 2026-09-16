(function () {
    const HealthAI = {};

    function getCookie(name) {
        const value = `; ${document.cookie}`;
        const parts = value.split(`; ${name}=`);
        if (parts.length === 2) {
            return parts.pop().split(";").shift();
        }
        return "";
    }

    function getCsrfToken() {
        const meta = document.querySelector('meta[name="csrf-token"]');
        return meta?.content || getCookie("csrftoken") || "";
    }

    function escapeHtml(value) {
        if (value === null || value === undefined) {
            return "";
        }

        return String(value)
            .replaceAll("&", "&amp;")
            .replaceAll("<", "&lt;")
            .replaceAll(">", "&gt;")
            .replaceAll('"', "&quot;")
            .replaceAll("'", "&#39;");
    }

    function formatDate(value, options = {}) {
        if (!value) {
            return "-";
        }

        const date = new Date(value);
        if (Number.isNaN(date.getTime())) {
            return String(value);
        }

        return new Intl.DateTimeFormat("en-IN", {
            day: "2-digit",
            month: "short",
            year: "numeric",
            ...options,
        }).format(date);
    }

    function formatDateTime(value) {
        if (!value) {
            return "-";
        }

        const date = new Date(value);
        if (Number.isNaN(date.getTime())) {
            return String(value);
        }

        return new Intl.DateTimeFormat("en-IN", {
            day: "2-digit",
            month: "short",
            year: "numeric",
            hour: "2-digit",
            minute: "2-digit",
        }).format(date);
    }

    function formatTime(value) {
        if (!value) {
            return "-";
        }

        const date = new Date(`1970-01-01T${value}`);
        if (Number.isNaN(date.getTime())) {
            return String(value);
        }

        return new Intl.DateTimeFormat("en-IN", {
            hour: "2-digit",
            minute: "2-digit",
        }).format(date);
    }

    function statusClass(status) {
        const value = String(status || "").toLowerCase();
        if (["taken", "completed", "active", "upcoming"].includes(value)) {
            return "status-active";
        }
        if (["pending", "sent"].includes(value)) {
            return "status-pending";
        }
        if (["missed", "failed", "cancelled"].includes(value)) {
            return "status-missed";
        }
        if (value === "paused") {
            return "status-paused";
        }
        return "status-active";
    }

    function showToast(message, type = "success", title = "Health AI") {
        const container = document.getElementById("toast-container") || document.body;
        const toast = document.createElement("div");
        const bsType = type === "error" ? "danger" : type;
        const headerClass = bsType === "danger" ? "text-bg-danger" : `text-bg-${bsType}`;

        toast.className = "toast align-items-center border-0";
        toast.setAttribute("role", "alert");
        toast.setAttribute("aria-live", "assertive");
        toast.setAttribute("aria-atomic", "true");
        toast.innerHTML = `
            <div class="d-flex ${headerClass} rounded-3">
                <div class="toast-body">
                    <strong class="me-2">${escapeHtml(title)}</strong>
                    <span>${escapeHtml(message)}</span>
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
            </div>
        `;

        container.appendChild(toast);
        const instance = bootstrap.Toast.getOrCreateInstance(toast, {
            delay: 3200,
        });
        instance.show();
        toast.addEventListener("hidden.bs.toast", () => toast.remove());
    }

    async function request(url, options = {}) {
        const {
            method = "GET",
            data,
            headers = {},
            isForm = false,
        } = options;

        const config = {
            method,
            credentials: "same-origin",
            headers: {
                Accept: "application/json",
                ...headers,
            },
        };

        if (method !== "GET" && method !== "HEAD") {
            config.headers["X-CSRFToken"] = getCsrfToken();
        }

        if (data !== undefined) {
            if (isForm || data instanceof FormData) {
                config.body = data;
            } else {
                config.headers["Content-Type"] = "application/json";
                config.body = JSON.stringify(data);
            }
        }

        const response = await fetch(url, config);
        const contentType = response.headers.get("content-type") || "";
        let payload = null;

        if (contentType.includes("application/json")) {
            payload = await response.json();
        } else if (response.status !== 204) {
            payload = await response.text();
        }

        if (!response.ok) {
            const message = payload?.message || payload?.detail || "Request failed.";
            const error = new Error(message);
            error.response = response;
            error.payload = payload;
            throw error;
        }

        return payload;
    }

    function renderEmptyState(container, icon, title, description, actionHtml = "") {
        if (!container) {
            return;
        }

        container.innerHTML = `
            <div class="empty-state animate-fade-up">
                <i class="${escapeHtml(icon)}"></i>
                <h5 class="mb-2">${escapeHtml(title)}</h5>
                <p class="mb-3">${escapeHtml(description)}</p>
                ${actionHtml}
            </div>
        `;
    }

    function renderSkeleton(container, rows = 4, columns = 4) {
        if (!container) {
            return;
        }

        let html = "";
        for (let row = 0; row < rows; row += 1) {
            html += `<div class="d-flex gap-3 mb-3">`;
            for (let column = 0; column < columns; column += 1) {
                html += `<div class="skeleton flex-grow-1" style="height:${column === 0 ? "18px" : "16px"}"></div>`;
            }
            html += `</div>`;
        }
        container.innerHTML = html;
    }

    function formatStatusText(value) {
        if (!value) {
            return "-";
        }

        return String(value)
            .replaceAll("_", " ")
            .replace(/\b\w/g, (char) => char.toUpperCase());
    }

    async function apiGet(url) {
        return request(url, { method: "GET" });
    }

    async function apiPost(url, data, isForm = false) {
        return request(url, {
            method: "POST",
            data,
            isForm,
        });
    }

    async function apiPut(url, data, isForm = false) {
        return request(url, {
            method: "PUT",
            data,
            isForm,
        });
    }

    async function apiDelete(url) {
        return request(url, { method: "DELETE" });
    }

    function setButtonLoading(button, isLoading, label) {
        if (!button) {
            return;
        }

        if (isLoading) {
            if (!button.dataset.originalHtml) {
                button.dataset.originalHtml = button.innerHTML;
            }
            button.disabled = true;
            button.innerHTML = `<span class="spinner-border spinner-border-sm me-2"></span>${escapeHtml(label || "Loading")}`;
        } else {
            button.disabled = false;
            if (button.dataset.originalHtml) {
                button.innerHTML = button.dataset.originalHtml;
                delete button.dataset.originalHtml;
            }
        }
    }

    function initTheme() {
        const theme = localStorage.getItem("healthai-theme");
        if (theme === "dark") {
            document.body.classList.add("dark-mode");
        }
    }

    function initThemeToggle() {
        const toggle = document.getElementById("theme-toggle");
        if (!toggle) {
            return;
        }

        const syncIcon = () => {
            const icon = toggle.querySelector("i");
            if (!icon) {
                return;
            }
            icon.className = document.body.classList.contains("dark-mode")
                ? "fa-solid fa-sun"
                : "fa-solid fa-moon";
        };

        syncIcon();

        toggle.addEventListener("click", () => {
            document.body.classList.toggle("dark-mode");
            localStorage.setItem(
                "healthai-theme",
                document.body.classList.contains("dark-mode") ? "dark" : "light"
            );
            syncIcon();
        });
    }

    function initSidebar() {
        const menuButton = document.getElementById("menu-toggle");
        const sidebar = document.getElementById("sidebar");

        if (menuButton && sidebar) {
            menuButton.addEventListener("click", () => {
                sidebar.classList.toggle("show");
            });
        }

        document.querySelectorAll(".sidebar-menu a").forEach((link) => {
            const href = link.getAttribute("href");
            const current = window.location.pathname.replace(/\/+$/, "/");
            if (href === current || href === window.location.pathname) {
                link.classList.add("active");
            }
        });
    }

    window.HealthAI = {
        getCookie,
        getCsrfToken,
        escapeHtml,
        formatDate,
        formatDateTime,
        formatTime,
        formatStatusText,
        statusClass,
        showToast,
        renderEmptyState,
        renderSkeleton,
        setButtonLoading,
        apiGet,
        apiPost,
        apiPut,
        apiDelete,
    };

    document.addEventListener("DOMContentLoaded", () => {
        initTheme();
        initThemeToggle();
        initSidebar();
    });
})();
