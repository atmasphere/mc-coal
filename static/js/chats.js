var chats = {
    username: null,
    soundEnabled: true,

    init: function() {
        chats.username = $('meta[name="username"]').attr('content');
        chats.initChannel();
        chats.initSound();
    },

    initChannel: function() {
        var token = $('meta[name="channel-token"]').attr('content');
        var channel = new goog.appengine.Channel(token);
        var socket = channel.open();
        socket.onopen = chats.socketOpened;
        socket.onmessage = chats.socketMessage;
        socket.onerror = chats.socketError;
        socket.onclose = chats.socketClosed;
    },

    socketOpened: function() {},

    socketMessage: function(message) {
        var data = jQuery.parseJSON(message.data);
        chats.playSound(data.event);

        var eventDiv = $('.event_template')
            .first()
            .clone()
            .addClass(data.event + '_event')
            .addClass(data.username == chats.username ? 'you' : '');

        eventDiv.find('.avatar').css('background-image', 'url(https://minotar.net/helm/' + data.username + '/20)');
        eventDiv.find('.name').text(data.username);
        eventDiv.find('.online .data').html(data.date + '&nbsp;&nbsp;' + data.time);

        var chatDiv = eventDiv.find('.chat');
        switch (data.event) {
            case 'chat':
                chatDiv.text(data.chat);
                break;
            case 'login':
                chatDiv.text('Logged in');
                break;
            case 'logout':
                chatDiv.text('Logged out');
                break;
        }

        eventDiv.prependTo('#live_events').slideDown('fast');
    },

    socketError: function(error) {},

    socketClosed: function() {
        chats.playSound('brokenSocket');
        $('.live_updates_status').show();
    },

    initSound: function() {
        if ($.cookie('sound') == 'off') {
            chats.soundEnabled = false;
        }
        $('.sound_state').click(chats.toggleSoundState);
        chats.showSoundState();
    },

    sounds: {
        login: new buzz.sound('/sounds/door_open', { formats: [ 'ogg', 'mp3' ] }),
        logout: new buzz.sound('/sounds/chestclosed', { formats: [ 'ogg', 'mp3' ] }),
        chat: new buzz.sound('/sounds/bass', { formats: [ 'ogg', 'mp3' ] }),
        death: new buzz.sound('/sounds/hurt', { formats: [ 'ogg', 'mp3' ] }),
        soundOn: new buzz.sound('/sounds/click', { formats: [ 'ogg', 'mp3' ] }),
        brokenSocket: new buzz.sound('/sounds/break', { formats: [ 'ogg', 'mp3' ] })
    },

    playSound: function(eventType) {
        if (chats.soundEnabled) {
            chats.sounds[eventType].play();
        }
    },

    toggleSoundState: function() {
        chats.soundEnabled = !chats.soundEnabled;
        if (chats.soundEnabled) {
            chats.playSound('soundOn');
        }
        $.cookie('sound', chats.soundEnabled ? 'on' : 'off', { expires: 3650, path: '/' });
        chats.showSoundState();
    },

    showSoundState: function() {
        $('.sound_state').text(
            chats.soundEnabled ? 'ON' : 'OFF'
        );
    }
};

$(function() {
    chats.init();
});
