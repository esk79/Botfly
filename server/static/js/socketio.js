/**
 * Created by EvanKing on 12/28/16.
 */

//necessary so that all js files can access same socket object
namespace = '/bot';
socket = io.connect(location.protocol + '//' + document.domain + ':' + location.port + namespace);
