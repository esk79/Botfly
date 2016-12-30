/**
 * Created by EvanKing on 12/28/16.
 */


var filemanager = $('.filemanager'),
    breadcrumbs = $('.breadcrumbs'),
    fileList = filemanager.find('.data');


function generateFileFolderObject(response, search) {
    //get dictionary portion of response
    response = response[1]

    scannedFiles = []
    scannedFolders = []
    for (var path in response) {
        if (response.hasOwnProperty(path)) {
            var isFolder = response[path][0];
            var size = response[path][2]
            var pathParts = path.split("/")
            var name = pathParts[pathParts.length - 1]

            if (search == null || name.toLowerCase().includes(search.toLowerCase())) {
                if (isFolder) {
                    scannedFolders.push({"name": name, "type": "folder", "path": path, "items": null})
                }
                else {
                    scannedFiles.push({"name": name, "type": "file", "path": path, "size": size})
                }
            }

        }
    }
    return [scannedFiles, scannedFolders]
}


function generateFileFolderIcons(response, search) {
    fileList.empty();
    search = search || null;

    formattedObjects = generateFileFolderObject(response, search)
    scannedFiles = formattedObjects[0]
    scannedFolders = formattedObjects[1]
    // Empty the old result and make the new one

    if (!scannedFolders.length && !scannedFiles.length) {
        filemanager.find('.nothingfound').show();
    }
    else {
        filemanager.find('.nothingfound').hide();
    }

    if (scannedFolders.length) {

        scannedFolders.forEach(function (f) {
            var name = escapeHTML(f.name),
                icon = '<span class="icon folder"></span>';
            var folder = $('<li class="folders"><a onclick="getLS(\'' + f.path + '\')" title="' + f.path + '" class="folders">' + icon + '<span class="name">' + name + '</span> </a></li>');
            folder.appendTo(fileList);
        });

    }

    if (scannedFiles.length) {

        scannedFiles.forEach(function (f) {

            var fileSize = bytesToSize(f.size),
                name = escapeHTML(f.name),
                fileType = name.split('.'),
                icon = '<span class="icon file"></span>';

            fileType = fileType[fileType.length - 1];

            icon = '<span class="icon file f-' + fileType + '">.' + fileType + '</span>';

            var file = $('<li class="files"><a onclick="downloadFile(\'' + f.path + '\')" title="' + f.path + '" class="files">' + icon + '<span class="name">' + name + '</span> <span class="details">' + fileSize + '</span></a></li>');
            file.appendTo(fileList);
        });

    }
}

function generateBreadcrumbsIcon(response) {
    // Generate the breadcrumbs
    breadcrumbsUrls = generateBreadcrumbsPath(response[0])

    var url = '';


    fileList.addClass('animated');
    url += '<a onclick="getLS(\'/\')"><span class="bread folderName">/</span></a>';

    breadcrumbsUrls.forEach(function (path, i) {

        var name = path.split('/');


        if (i !== breadcrumbsUrls.length - 1) {
            url += '<a onclick="getLS(\'' + path + '\')"><span class="bread folderName">' + name[name.length - 1] + '</span></a> <span class="arrow">→</span> ';
        }
        else {
            url += '<span class="folderName">' + name[name.length - 1] + '</span>';
        }

    });


    breadcrumbs.text('').append(url);


    // Show the generated elements

    fileList.animate({'display': 'inline-block'});
}

function generateSearchBar(response) {
    // Hiding and showing the search box
    filemanager.find('.search').click(function () {

        var search = $(this);

        search.find('span').hide();
        search.find('input[type=search]').show().focus();

    });

    // Listening for keyboard input on the search field.
    // We are using the "input" event which detects cut and paste
    // in addition to keyboard input.
    filemanager.find('input').on('input', function (e) {
        var value = this.value.trim();
        console.log(value)
        generateFileFolderIcons(response, value)
    });
    //}).on('keyup', function (e) {
    //
    //    // Clicking 'ESC' button triggers focusout and cancels the search
    //    var search = $(this);
    //    if (e.keyCode == 27) {
    //        search.trigger('focusout');
    //    }
    //
    //}).focusout(function (e) {
    //
    //    // Cancel the search
    //    var search = $(this);
    //    if (!search.val().trim().length) {
    //        search.hide();
    //        search.parent().find('span').show();
    //    }
    //
    //});

}


//render finder with server response
function renderFinder(response) {
    var value = $('.div.search.input-group')
    console.log(value)
    generateFileFolderIcons(response);
    generateBreadcrumbsIcon(response);
    generateSearchBar(response);
}

// This function escapes special html characters in names
function escapeHTML(text) {
    return text.replace(/\&/g, '&amp;').replace(/\</g, '&lt;').replace(/\>/g, '&gt;');
}

// Convert file sizes from bytes to human readable units
function bytesToSize(bytes) {
    var sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
    if (bytes == 0) return '0 Bytes';
    var i = parseInt(Math.floor(Math.log(bytes) / Math.log(1024)));
    return Math.round(bytes / Math.pow(1024, i), 2) + ' ' + sizes[i];
}

// Splits a file path and turns it into clickable breadcrumbs
function generateBreadcrumbsPath(nextDir) {
    var path = nextDir.split('/').slice(0);
    for (var i = 1; i < path.length; i++) {
        path[i] = path[i - 1] + '/' + path[i];
    }
    return path;
}

//post call to server to get LS info from bot
function getLS(path) {
    $.ajax({
        type: "POST",
        url: "/ls",
        data: {
            file: path
        },
        success: function (data) {
            console.log(data)
        }
    });
}

function _base64ToArrayBuffer(base64) {
    var binary_string = window.atob(base64);
    var len = binary_string.length;
    var bytes = new Uint8Array(len);
    for (var i = 0; i < len; i++) {
        bytes[i] = binary_string.charCodeAt(i);
    }
    return bytes.buffer;
}

// download file from connected bot
function downloadFile(filename) {
    $.ajax({
        type: "POST",
        url: "/downloader",
        data: {
            file: filename
        },
        success: function (data) {
            var blob = new Blob([_base64ToArrayBuffer(data)]);
            var link = document.createElement('a');
            link.href = window.URL.createObjectURL(blob);
            var pathParts = filename.split("/");
            link.download = pathParts[pathParts.length - 1];
            link.click();
        }
    });
}

$(document).ready(function () {
    if ($.cookie("bot") == '' || $.cookie("bot") == null) {
        console.log("select a bot");
    } else {
        //handle response emitted by server
        var not_received = true;
        socket.on('finder', function (msg) {
            if (msg.user === getCookie('bot')) {
                not_received = false;
                if (msg.special.hasOwnProperty('ls')) {
                    filemanager.prepend('<div class="search input-group"><input type="search" class="form-control" placeholder="Find a file..."> </div>')
                    var response = JSON.parse(msg.special['ls']);
                    renderFinder(response);
                }
            }
        });

        var receive_loop = function () {
            if (not_received) {
                getLS('.');
                setTimeout(receive_loop, 500);
            }
        };
        setTimeout(receive_loop, 100);
    }
});
