(function($) {

    'use strict';

    function download(dataurl, filename) {
        var a = document.createElement("a");
        a.href = dataurl;
        a.setAttribute("download", filename);
        a.click();
        return false;
    }

    $.download = download;

    $.noWebsocket = function(args) {

        var o = $.extend({
            url: null,
            imageSelector: null,
            indicatorSelector: '#websock',
            cssOpen: 'no-websock-open',
            cssClosed: 'no-websock-closed',
        }, args);

        var WS = {

            sendJSON: function(data) {
                var self = this;

                $.ajax({
                    url: o.url,
                    type: 'post',
                    dataType: 'json',
                    contentType: "application/json; charset=utf-8",
                    data: JSON.stringify(data),
                }).done(function(result) {

                    // console.log(result)
                    var img = new Image;
                    img.src = result.url;
                    img.onload = function() {
                        $(o.imageSelector)[0].getContext('2d').drawImage(img, 0, 0);
                    };
                    // $(o.imageSelector)[0].src = result.url;
                    $(o.indicatorSelector).removeClass(o.cssClosed).addClass(o.cssOpen);

                }).fail(function() {
                    $(o.indicatorSelector).removeClass(o.cssOpen).addClass(o.cssClosed);
                });
            },

            getPDF: function(data, name) {
                var self = this;

                $.ajax({
                    url: o.url,
                    type: 'post',
                    dataType: 'json',
                    contentType: "application/json; charset=utf-8",
                    data: JSON.stringify(data),
                }).done(function(result) {
                    download(result.url, name);
                }).fail(function() {
                    $(o.indicatorSelector).removeClass(o.cssOpen).addClass(o.cssClosed);
                });
            }

        }

        return WS;

    }

}(jQuery));
