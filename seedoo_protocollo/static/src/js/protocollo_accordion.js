$(document).on('click', '#protocollo-accordion .protocollo-accordion-toggle', function () {

    //Close "Anteprima Panel" if is closing "Documento Panel"
    if ($(this).parent().attr("id") == "documento-container") {
        if ($(this).next().css("display") == "block") {
            $("#anteprima-container").css("display", "none")
        }
        else {
            $("#anteprima-container").css("display", "block")
        }

    }

    $("#protocollo-accordion .protocollo-accordion-toggle").removeClass("accordion-selected");
    $(this).next().slideToggle('fast');
    $(this).addClass("accordion-selected");
    //Hide the other panels
    // $(".accordion-content").not($(this).next()).slideUp('fast');
});


