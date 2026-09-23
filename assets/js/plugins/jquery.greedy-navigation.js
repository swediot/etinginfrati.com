/*
* Greedy Navigation
*
* http://codepen.io/lukejacksonn/pen/PwmwWV
*
* All or nothing: when the links do not all fit, every link except the site
* title moves to the dropdown, so the button never sits next to a partial menu.
*
* The site only loads assets/js/main.min.js, so a change here has to be
* copied into that file as well.
*
*/

var $nav = $('#site-nav');
var $btn = $('#site-nav button');
var $vlinks = $('#site-nav .visible-links');
var $hlinks = $('#site-nav .hidden-links');

function updateNav() {

  // Put every link back in the nav to measure the full list
  $hlinks.children().appendTo($vlinks);

  // The full list is overflowing the nav
  if($vlinks.width() > $nav.width()) {

    // Move every item but the site title to the hidden list
    $vlinks.children().slice(1).appendTo($hlinks);

    // Show the dropdown btn
    $btn.removeClass('hidden');

  // The full list fits
  } else {

    // Hide the dropdown btn and close the dropdown
    $btn.addClass('hidden').removeClass('close');
    $hlinks.addClass('hidden');
  }

  // Keep counter updated
  $btn.attr("count", $hlinks.children().length);

}

// Window listeners

$(window).resize(function() {
  updateNav();
});

$btn.on('click', function() {
  $hlinks.toggleClass('hidden');
  $(this).toggleClass('close');
});

updateNav();