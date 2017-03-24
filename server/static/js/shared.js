/**
 * Created by EvanKing on 12/28/16.
 */

//necessary so that all js files can access same socket object
namespace = '/bot';
socket = io.connect(location.protocol + '//' + document.domain + ':' + location.port + namespace);


//new connection received
socket.on('connection', function (msg) {
    $('li.notifications').append('<a class="conn-' + msg.user + '">' + 'New connection from: ' + msg.user + '</a>');
    $('.conn-' + msg.user).fadeOut(5000);
    getBotList()
});

//TODO: consolidate
//repetitive code: will remove later
socket.on('disconnect', function (msg) {
    $('li.notifications').append('<a class="disconn-' + msg.user + '">' + 'Lost connection to: ' + msg.user + '</a>');
    $('.disconn-' + msg.user).fadeOut(5000);
    getBotList()
    $.removeCookie('bot', {path: '/'});
    if ($('#bot > option').length == 1 || $("#bot").val() == msg.user) {
        location.reload();
    }
});

//success message received from server
socket.on('success', function (msg) {
    if (msg.type == 'download') {
        increaseeDownloadsNumber()
        getDownloading()
    }
    terminal.echo(stdoutStyle(msg.message))
});

/*************************************
 Downloads dropdown code begins here *
 *************************************/

function updateDownloadsNumber(data) {
    var num = data.length;
    if (parseInt($('span.num-downloads.badge').html(), 10) != num) {
        $('span.num-downloads.badge').html(num)
    }
}

function increaseeDownloadsNumber() {
    $('span.num-downloads.badge').html(parseInt($('span.num-downloads.badge').html(), 10) + 1)
}

function updateProgressBar(filename, percent) {
    filenameParsed = filename.split('.')[0];
    $('.progress-' + filenameParsed).attr('aria-valuenow', percent).css('width', percent + '%');
}

function addInProgress(filename, percent, path, user) {
    filenameParsed = filename.split('.')[0];
    var downloadManager = $('div.downloads')
    downloadManager.prepend('<div class="row vertical-align row-margin"> <span class="col-md-6">' + filename + '</span> <div class="progress col-md-6"> <div class="progress-bar progress-bar-striped active progress-' + filenameParsed + '"role="progressbar"aria-valuenow="' + percent + '" aria-valuemin="0" aria-valuemax="100"style="width:' + percent + '%"></div> </div>  <a onclick="deleteFile(\'' + path + '\', \'' + user + '\')" class="col-md-2"><span class="glyphicon glyphicon-remove pull-right"></span></a></div>')
}

function addCompleted(filename, path, user) {
    filenameParsed = filename.split('.')[0];
    var downloadManager = $('div.downloads')
    downloadManager.append(' <div class="row vertical-align row-margin"> <span class="col-md-6">' + filename + '</span> <div class="col-md-8"> <a href="/downloader?bot=' + user + '&file=' + path + '" download="' + filename + '" class="btn btn-primary pull-right" style="width: 100%;">Download <span class="glyphicon glyphicon-download-alt"></span></a> </div>  <a onclick="deleteFile(\'' + path + '\', \'' + user + '\')" class="col-md-1"><span class="glyphicon glyphicon-remove pull-right" style="color: #a4a7ac"></span></a></div>')
}

function populateDownloadsDropdown(data) {

    //no current download files
    if (data.length == 0) {
        var downloadManager = $('div.downloads')
        downloadManager.append(' <div class="row vertical-align row-margin"> <span class="col-md-6">No files.</span><div class="col-md-6">')
        return;
    }

    data.forEach(function (file) {
        var pathParts = file['filename'].split("/")
        var filename = pathParts[pathParts.length - 1]
        var user = file['user']
        var downloadPercent = Math.floor((file['downloaded'] / file['size']) * 100)

        //download complete
        if (downloadPercent == 100) {
            addCompleted(filename, file['filename'], user)
        } else {
            addInProgress(filename, downloadPercent, file['filename'], user)
        }
    });
}

// get currently downloading files from server
function getDownloading() {
    $.get("/downloader", function (data, status) {
        $('div.downloads').empty()
        updateDownloadsNumber(data)
        populateDownloadsDropdown(data)
    });
}

function deleteFile(file, user) {
    $.ajax({
        type: "DELETE",
        url: "/downloader?file=" + file + "&bot=" + user + " ",
        success: function (data) {
            getDownloading()
            console.log(data)
        }
    });
}

function checkUpdateDownloads() {
    if ($("li.dropdown").hasClass('open')) {
        //dropdown is opened
        setInterval(function () {
            getDownloading();
        }, 1000);
    }
}


/*************************************
           Bot List sidebar          *
 *************************************/


function toggleSidebar() {
    $("#menu-toggle").click(function (e) {
        e.preventDefault();
        $("#wrapper").toggleClass("active");
        getBotList()
    });
}

// get current bot list
function getBotList() {
    $.get("/bots", function (data, status) {
        addToBotSideBar(data)
    });
}

function addToBotSideBar(data) {

    //get table body objects from DOM
    var onlineTableBody = $('tbody.online')
    var offlineTableBody = $('tbody.offline')

    var onlineTable = $('tbody.online')
    var offlineTable = $('tbody.offline')

    onlineTable.empty()
    offlineTable.empty()
    onlineTableBody.empty()
    offlineTableBody.empty()

    updateConnectionStatus()

    var onlineHeader = $('<h3>Online</h3>')
    var offlineHeader = $('<h3>Offline</h3>')

    var addedOnlineHeader = false
    var addedOfflineHeader = false

    //iterate over all bots
    for (var bot in data) {
        if (data.hasOwnProperty(bot)) {

            var botName = bot
            var botData = data[bot]
            var lastOnline = createDateString(botData['lastonline'])
            var state;
            if (botData['state'] != "") {
                state = botData['state']

            } else {
                state = "NA"
            }
            var arch = botData['arch']
            var online = botData['online']


            if (online && !addedOnlineHeader) {
                onlineTable.prepend(onlineHeader)
                addedOnlineHeader = true
            }
            if (!online && !addedOfflineHeader) {
                offlineTable.prepend(offlineHeader)
                addedOfflineHeader = true
            }

            var tableRow;

            if (online) {
                tableRow = $('<tr><td><h4>' + botName + '</h4></td><td align="center"><div  class="btn btn-warning btn-xs button-center">' + arch + '</div></td><td align="center"><div class="btn btn-danger btn-xs button-center">' + state + '</div></td></tr>')
                onlineTableBody.append(tableRow)
            } else {
                tableRow = $('<tr><td><h4>' + botName + '</h4></td><td align="center"><div  class="btn btn-success btn-xs button-center">' + lastOnline + '</div></td><td align="center"><div class="btn btn-danger btn-xs button-center">' + state + '</div></td></tr>')
                offlineTableBody.append(tableRow)
            }
            handleBotSelection()
        }
    }

}

function updateConnectionStatus() {
    var connectionStatus = $('ul.connection-status')
    connectionStatus.empty()

    var status;
    if ($.cookie("bot") == null) {
        status = $('<div class="alert alert-danger" role="alert"><a>Connected: None</a></div>')
    } else {
        status = $('<div class="alert alert-success" role="alert"><a>Connected: ' + $.cookie("bot") + '</a></div>')
    }
    connectionStatus.append(status)
}

function createDateString(rawDate) {
    var dayOfWeek = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
    var lastOnline = new Date(rawDate * 1000);
    var now = new Date(Date.now());
    var timeDiff = now.getTime() - lastOnline.getTime();
    var diffDays = Math.floor(timeDiff / (1000 * 3600 * 24));

    if (diffDays == 0) {
        return "Today"
    }
    if (diffDays == -1) {
        return "Yesterday"
    }
    if (diffDays >= -6) {
        return dayOfWeek[lastOnline.getDay()]
    }

    return lastOnline.toDateString();
}

function handleBotSelection() {
    $('tbody.online').find('tr').click(function () {
        var bot = $(this).find('td:first').text();
        botSelected(bot)
    });
}

//new bot selected
function botSelected(bot) {
    if (bot != $.cookie("bot")) {
        $.ajax({
            type: "POST",
            url: "/choose",
            data: {
                bot: bot
            },
            success: function (data, status) {
                if (status == 'success') {
                    //updateConnectionStatus()
                    //log()
                    //should not need to reload!! The above should work fine but doesn't
                    location.reload();
                } else {
                    console.log("Bot selection error")
                }
            }
        });
    }
};


/*************************************
 Document on ready          *
 *************************************/

$(document).ready(function () {
    getDownloading()
    getBotList()
    toggleSidebar()
    setInterval(function () {
        checkUpdateDownloads();
    }, 1000);
});

