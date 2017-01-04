/**
 * Created by EvanKing on 12/28/16.
 */

//necessary so that all js files can access same socket object
namespace = '/bot';
socket = io.connect(location.protocol + '//' + document.domain + ':' + location.port + namespace);

//new bot selected
$(function () {
    $('#bot').change(function () {
        var value = $(this).val();
        $.ajax({
            type: "POST",
            url: "/choose",
            data: {
                bot: value
            },
            success: function (data) {
                location.reload();
            }
        });
    });
});


//new connection received
socket.on('connection', function (msg) {
    $('.col-md-3').append('<p class="conn-' + msg.user + '">' + 'New connection from: ' + msg.user + '</p>');
    $('.conn-' + msg.user).fadeOut(5000);
    $("#bot").append('<option value="' + msg.user + '">' + msg.user + '</option>')
});

//TODO: consolidate
//repetitive code: will remove later
socket.on('disconnect', function (msg) {
    $('.col-md-3').append('<p class="disconn-' + msg.user + '">' + 'Lost connection to: ' + msg.user + '</p>');
    $('.disconn-' + msg.user).fadeOut(5000);
    $("#bot option[value='" + msg.user + "']").remove();
    if ($('#bot > option').length == 1 || $("#bot").val() == msg.user) {
        $.removeCookie('bot', {path: '/'});
        location.reload();
    }
});

function getCookie(name) {
    var value = "; " + document.cookie;
    var parts = value.split("; " + name + "=");
    if (parts.length >= 2) return parts.pop().split(";").shift();
}

/*************************************
 Downloads dropdown code begins here *
 *************************************/

function updateDownloadsNumber(data) {
    var num = data.length;
    if (parseInt($('span.num-downloads.badge').html(), 10) != num) {
        console.log("here")
        $('span.num-downloads.badge').html(num)
    }
}

function decreaseDownloadsNumber() {
    $('span.num-downloads.badge').html(parseInt($('span.num-downloads.badge').html(), 10) - 1)
}

function updateProgressBar(filename, percent) {
    filenameParsed = filename.split('.')[0];
    $('.progress-' + filenameParsed).attr('aria-valuenow', percent).css('width', percent + '%');
}

function addInProgress(filename, percent, path) {
    filenameParsed = filename.split('.')[0];
    var downloadManager = $('div.downloads')
    downloadManager.prepend('<div class="row vertical-align row-margin"> <span class="col-md-6">' + filename + '</span> <div class="progress col-md-6"> <div class="progress-bar progress-bar-striped active progress-' + filenameParsed + '"role="progressbar"aria-valuenow="' + percent + '" aria-valuemin="0" aria-valuemax="100"style="width:' + percent + '%"></div> </div>  <a onclick="deleteFile(\'' + path +' \')" class="col-md-2"><span class="glyphicon glyphicon-remove pull-right"></span></a></div>')
}

function addCompleted(filename, path) {
    filenameParsed = filename.split('.')[0];
    var downloadManager = $('div.downloads')
    downloadManager.append(' <div class="row vertical-align row-margin"> <span class="col-md-6">' + filename + '</span> <div class="col-md-8"> <a href="/downloader?file=' + path + '" download="' + filename + '" class="btn btn-primary pull-right" style="width: 100%;">Download <span class="glyphicon glyphicon-download-alt"></span></a> </div>  <a onclick="deleteFile(\'' + path +' \')" class="col-md-1"><span class="glyphicon glyphicon-remove pull-right" style="color: #a4a7ac"></span></a></div>')
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
            addCompleted(filename, file['filename'])
        } else {
            addInProgress(filename, downloadPercent, file['filename'])
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

function deleteFile(file) {
    $.ajax({
        type: "DELETE",
        url: "/downloader?file="+file,
        success: function (data) {
            console.log(data)
        }
    });
}

getDownloading()
setInterval(function () {
    getDownloading();
}, 1000);

