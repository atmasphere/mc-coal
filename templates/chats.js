$('#live_events').append(
    {%- filter escapejs -%}
    {%- include "_chats.html" -%}
    {%- endfilter -%}
);
{% if next_uri %}
    $('.infinite_scroll').data('url', "{{ next_uri }}");
    $(window).scroll();
{% else %}
    $('.infinite_scroll').remove();
{% endif %}
