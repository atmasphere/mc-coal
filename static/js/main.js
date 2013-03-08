/*****************************************************
*  MAIN.JS
*  (C) 2012 - Brent Gustafson - brentgustafson.com
******************************************************/

var bg, bgh, bgw;

function resize_bg() {
    bgw = bg.width();
    offsetw = bgw - $(window).width();
    bg.css("left", offsetw/2*-1);
}

$(function() {
    bg = $("#bg");
    resize_bg();
    
    $(window).resize(function () {
        resize_bg();
    });
    
});