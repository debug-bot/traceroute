$(document).ready(function () {
    $("#command-select").select2({
        placeholder: "Select Command",
        width: "100%",
    });

    $("#command-select").change(function () {
        var selectedCommand = $(this).val();
        if (selectedCommand.includes(">") || selectedCommand.includes("<")) {
            $("#interface-selection").slideDown();
        } else {
            $("#interface-selection").slideUp();
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
});
