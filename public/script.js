document.addEventListener("DOMContentLoaded", () => {
    const params = new URLSearchParams(window.location.search);

    if (params.get("signup") === "success") {
        const panel = document.querySelector(".login-panel");

        if (panel) {
            const message = document.createElement("p");
            message.className = "status-message";
            message.textContent =
                "Account created successfully! Please log in.";

            panel.appendChild(message);
        }
    }
});