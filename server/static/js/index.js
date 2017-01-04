/**
 * Created by EvanKing on 1/1/17.
 */

terminalFontSize = 14;
terminalMargin = 2;

//sets the terminal text color and font-size
function textStyle(message) {
    return "[[;#90b1e5;black]" + message + "]";
    //return message;
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
        if ($.cookie("bot") == null) {
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


/******************************************
 Payload dictionary functions begins here *
 ******************************************/

var payloadsList = null;

// get current payload information
function getPayloads() {
    $.get("/payload", function (data, status) {
        saveData(data)
        populateDictionary(data)
    });
}

function populateDictionary(data, search) {
    search = search || null;
    var payloadManager = $('div.payloads')
    payloadManager.empty();
    for (var payload in data) {
        if (data.hasOwnProperty(payload)) {

            var payloadData = data[payload]
            var description = payloadData['description']
            var name = payloadData['name']
            var variables = payloadData['vars']
            var parsedName = /[^/]*$/.exec(name)[0].split(" ")[0] + getRandomArbitrary(0, 10000);

            console.log(name)
            console.log(search)
            if (search == null || (name != null && name.toLowerCase().includes(search.toLowerCase()))) { //|| (description != null && description.toLowerCase().includes(search.toLowerCase()))) {

                var variablesList = $('<ul class="list-unstyled"></ul>')

                for (var variable in variables) {
                    if (variables.hasOwnProperty(variable)) {
                        var variableItem = $('<li><div><inline><h5>' + variable + ': <span>' + variables[variable] + '</span></h5></inline></div></li>');
                        variableItem.appendTo(variablesList);
                    }
                }

                variablesList.prepend('<h4>Parameters: </h4>')

                var panelBodyDiv = $('<div class="panel-body"> </div>')
                var panelBodyContent = $('</div><div><h4>Description: </h4><p>' + description + '</p>')

                panelBodyDiv.append(variablesList)
                panelBodyDiv.append(panelBodyContent)

                var collapse = $(' <div id="collapse-' + parsedName + '" class="panel-collapse collapse"></div>')
                collapse.append(panelBodyDiv)

                var collapseOuter = $(' <div class="panel panel-default"><div class="panel-heading"><h4 class="panel-title"><a data-toggle="collapse" data-parent="#accordion" href="#collapse-' + parsedName + '">' + name + '</a></h4></div></div>')
                collapseOuter.append(collapse)

                payloadManager.append(collapseOuter)
            }
        }
    }
}

function saveData(data){
    payloadsList = data;
}

// Returns a random number between min (inclusive) and max (exclusive)
function getRandomArbitrary(min, max) {
    return Math.floor(Math.random() * (max - min) + min);
}


function generateSearchBar() {
    // Listening for keyboard input on the search field.
    $('input.search-payload').on('input', function (e) {
        var value = this.value.trim();
        populateDictionary(payloadsList, value)
    });

}
getPayloads()
generateSearchBar()

/******************************************
 On Document ready            *
 ******************************************/

$(document).ready(function () {
    $('head').append('<style id="terminalFont" type="text/css">.terminal-output, .cmd {font-size:' + terminalFontSize + 'px;}</style>');
    $('head').append('<style id="terminalMargin" type="text/css">.terminal div {margin-bottom:' + terminalMargin + 'px;}</style>');
    $.ajax({
        type: 'POST',
        url: '/log',
        data: null,
        contentType: false,
        cache: false,
        processData: false,
        success: function (data){
            for (var index in data){
                var entry = data[index];
                if (entry[0] == 0){
                    terminal.echo(textStyle(entry[1]));
                } else if (entry[0] == 1){
                    terminal.error(entry[1]);
                }
            }
        }
    });
});
