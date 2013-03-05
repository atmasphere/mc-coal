/*****************************************************
*  MAIN.JS
*  (C) 2012 - Brent Gustafson - brentgustafson.com
******************************************************/

$(function() {
    stackBlurImage("spire", "canvas", 11, false);
    
    $(window).resize(function() {
        stackBlurImage("spire", "canvas", 11, false);
    });
});