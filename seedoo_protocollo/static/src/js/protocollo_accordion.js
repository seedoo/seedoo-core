    $(document).on('click', '#protocollo-accordion .protocollo-accordion-toggle', function() {
         //Expand or collapse this panel
      $("#protocollo-accordion .protocollo-accordion-toggle").removeClass("accordion-selected");
      $(this).next().slideToggle('fast');
      $(this).addClass("accordion-selected");

      //Hide the other panels
      // $(".accordion-content").not($(this).next()).slideUp('fast');


    });
