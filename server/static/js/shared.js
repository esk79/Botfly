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


$("#cart").on("click", function () {
    $(".shopping-cart").fadeToggle("fast");
});

