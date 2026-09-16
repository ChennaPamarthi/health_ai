document.addEventListener("DOMContentLoaded", () => {
    document.getElementById("theme-toggle-settings")?.addEventListener("click", () => {
        document.getElementById("theme-toggle")?.click();
    });

    document.getElementById("workspace-refresh")?.addEventListener("click", () => {
        window.location.reload();
    });

    initWorkoutSettings();
    document.getElementById("save-workout-settings")?.addEventListener("click", saveWorkoutSettings);
});

function initWorkoutSettings() {
    const enabled = localStorage.getItem("healthai-dashboard-workout") === "true";
    const goalMinutes = localStorage.getItem("healthai-workout-goal-minutes") || "30";

    const toggle = document.getElementById("workout-widget-toggle");
    const goalInput = document.getElementById("workout-goal-minutes");

    if (toggle) {
        toggle.checked = enabled;
    }

    if (goalInput) {
        goalInput.value = goalMinutes;
    }
}

function saveWorkoutSettings() {
    const api = window.HealthAI;
    const toggle = document.getElementById("workout-widget-toggle");
    const goalInput = document.getElementById("workout-goal-minutes");
    const goalMinutes = Math.max(Number(goalInput?.value || 30), 5);

    localStorage.setItem("healthai-dashboard-workout", toggle?.checked ? "true" : "false");
    localStorage.setItem("healthai-workout-goal-minutes", String(goalMinutes));

    if (goalInput) {
        goalInput.value = String(goalMinutes);
    }

    api.showToast("Workout settings saved.", "success", "Settings");
}
