/**
 * Created by EvanKing on 1/1/17.
 */

terminalFontSize = 14;
terminalMargin = 2;

//sets the terminal text color and font-size
function textStyle(message) {
    return "[[;#90b1e5;black]" + message + "]";
}

//handle terminal text zoom in/out on hotkey commands
hotkeys('command+=, command+-', function (event, handler) {
    switch (handler.key) {
        case "command+=":
            terminalMargin += .15;
            terminalFontSize += .2;
            break;
        case "command+-":
            terminalMargin -= .15;
            terminalFontSize -= .2;
            break;
    }
    $('#terminalFont').text('.terminal-output, .cmd {font-size:' + terminalFontSize + 'px;}');
    $('#terminalMargin').text('.terminal div {margin-bottom:' + terminalMargin + 'px;}');
});

socket.on('response', function (msg) {
    //error returned from bot
    if (msg.user === getCookie('bot')) {
        console.log(msg);
        if (msg.printout != '') {
            // TODO: change text color?
            terminal.echo(textStyle(msg.printout));
        }
        if (msg.errout != '') {
            // TODO: change text color?
            terminal.error(msg.errout);
        }
        if (msg.stderr != '') {
            terminal.error(msg.stderr);
        }
        if (msg.stdout != "Server generated event" && msg.stdout != '') {
            terminal.echo(textStyle(msg.stdout));
        }
    }
});

//success message received from server
socket.on('success', function (msg) {
    terminal.echo(textStyle(msg.message))
});


//upload a file to the server
$(function () {
    $('#upload-file').change(function () {
        //no bot selected
        if ('{{connected}}' == '') {
            terminal.error('No bot selected.');
            return;
        }
        var form_data = new FormData($('#upload-file')[0]);
        $.ajax({
            type: 'POST',
            url: '/uploader',
            data: form_data,
            contentType: false,
            cache: false,
            processData: false,
            success: function (data) {
                if (JSON.parse(data).success) {
                    terminal.echo(textStyle("File upload in progress..."))
                } else {
                    terminal.error(textStyle("File upload failed"))
                }
            },
        });
    });
});

//launch payload
$(function () {
    $("#send_payload").click(function (e) {

        //no bot selected
        if ($.cookie("bot") == null){
            terminal.error("No bot selected");
            return;
        }

        var value = $('#payload').val();
        if (value != 'Select payload..') {
            $.ajax({
                type: "POST",
                url: "/payload",
                data: {
                    payload: value
                },
                success: function (data) {
                    console.log(data)
                }
            });
        }
    });
});

$(document).ready(function () {
    $('head').append('<style id="terminalFont" type="text/css">.terminal-output, .cmd {font-size:' + terminalFontSize + 'px;}</style>');
    $('head').append('<style id="terminalMargin" type="text/css">.terminal div {margin-bottom:' + terminalMargin + 'px;}</style>');
});
