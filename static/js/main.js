/*****************************************************
*  MAIN.JS
*  (C) 2012 - Brent Gustafson - brentgustafson.com
******************************************************/

$(function() {
    stackBlurImage("bg", "canvas", 11, false);
    
    setTimeout(function () {
        stackBlurImage("bg", "canvas", 11, false);
    }, 10);
    
    $(window).resize(function() {
        stackBlurImage("bg", "canvas", 11, false);
    });
});