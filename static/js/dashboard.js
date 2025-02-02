$(document).ready(function () {
    $("#command-select").select2({
        placeholder: "Select Command",
        width: "100%",
    });

    $("#command-select").change(function () {
        var selectedCommand = $(this).val();
        $(".command-btn").removeClass("active");
        $(".command-btn").each(function () {
            if ($(this).data("command") === selectedCommand) {
                $(this).addClass("active");
            }
        });
        if (selectedCommand.includes(">") || selectedCommand.includes("<")) {
            $("#interface-selection").slideDown();
            $("#run-btn").prop("disabled", true);
        } else {
            $("#interface-selection").slideUp();
            $("#run-btn").prop("disabled", false);
        }
    });

    $("#command-select").on("select2:open", function () {
        setTimeout(function () {
            $(".select2-results__group").each(function () {
                const $group = $(this);
                $group.addClass("collapsed");
                $group.nextUntil(".select2-results__group").hide();
            });

            $(".select2-results__group")
                .off("click")
                .on("click", function () {
                    const $group = $(this);
                    $group.toggleClass("collapsed");
                    $group
                        .nextUntil(".select2-results__group")
                        .slideToggle(200);
                });
        }, 0);
    });
    $(".command-btn").on("click", function () {
        $(".command-btn").removeClass("active");
        $(this).addClass("active");
        $("#command-select").val($(this).data("command")).trigger("change");
    });
});
