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
 **************************************/


function increaseDownloadsNumber() {
    $('span.num-downloads.badge').html(parseInt($('span.num-downloads.badge').html(), 10) + 1)
}

function decreaseDownloadsNumber() {
    $('span.num-downloads.badge').html(parseInt($('span.num-downloads.badge').html(), 10) - 1)
}

function updateProgressBar(filename, percent) {
    filenameParsed = filename.split('.')[0];
    $('.progress-' + filenameParsed).attr('aria-valuenow', percent).css('width', percent + '%');
}

function addInProgress(filename) {
    filenameParsed = filename.split('.')[0];
    increaseDownloadsNumber()
    var downloadManager = $('div.downloads')
    downloadManager.prepend('<div class="row vertical-align row-margin"> <span class="col-md-6">' + filename + '</span> <div class="progress col-md-6"> <div class="progress-bar progress-bar-striped active progress-' + filenameParsed + '"role="progressbar"aria-valuenow="0" aria-valuemin="0" aria-valuemax="100"style="width: 0%"></div> </div> </div> ')
}

function addCompleted(filename) {
    filenameParsed = filename.split('.')[0];
    increaseDownloadsNumber()
    var downloadManager = $('div.downloads')
    downloadManager.append(' <div class="row vertical-align row-margin"> <span class="col-md-6">' + filename + '</span> <div class="col-md-6"> <button type="button" class="btn btn-primary pull-right" style="width: 100%;">Download <span class="glyphicon glyphicon-download-alt"></span></button> </div> </div>')
}
