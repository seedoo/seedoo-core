    $(document).on('click', '#protocollo_accordion .protocollo_accordion_toggle', function() {
         //Expand or collapse this panel
      $("#protocollo_accordion .protocollo_accordion_toggle").removeClass("accordion-selected");
      $(this).next().slideToggle('fast');
      $(this).addClass("accordion-selected");

      //Hide the other panels
      // $(".accordion-content").not($(this).next()).slideUp('fast');


    });
