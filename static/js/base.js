$(document).ready(function () {
    const modeToggle = $("#mode-toggle");

    function applyMode(mode) {
        if (mode === "dark") {
            $("body").addClass("bg-dark text-white dark-mode");
            $(".mode-container")
                .removeClass("bg-light")
                .addClass("bg-dark text-white border");
            $(".mode-navbar")
                .removeClass("bg-light navbar-light")
                .addClass("bg-dark navbar-dark");
            localStorage.setItem("theme", "dark");
        } else {
            $("body").removeClass("bg-dark text-white dark-mode");
            $(".mode-container")
                .removeClass("bg-dark text-white")
                .addClass("bg-light");
            $(".mode-navbar")
                .removeClass("bg-dark navbar-dark")
                .addClass("bg-light navbar-light");
            localStorage.setItem("theme", "light");
        }
    }

    const savedTheme = localStorage.getItem("theme") || "light";
    if (savedTheme === "dark") {
        modeToggle.prop("checked", true);
        applyMode("dark");
    }

    modeToggle.on("change", function () {
        const mode = $(this).is(":checked") ? "dark" : "light";
        applyMode(mode);
    });
});
