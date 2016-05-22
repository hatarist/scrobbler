$(window).load(function() {
  $('.carousel .item').each(function(){
    var next = $(this).next();
    if (!next.length) {
      next = $(this).siblings(':first');
    }
    next.children(':first-child').clone().appendTo($(this));
    
    next=next.next();
    if (!next.length) {
      next = $(this).siblings(':first');
    }
      
    next.children(':first-child').clone().appendTo($(this));
  });

  $(".alert-info").fadeTo(2000, 500).slideUp(500, function(){
    $(".alert-info").alert('close');
  });
});