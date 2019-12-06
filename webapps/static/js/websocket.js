(function($) {

    'use strict';

    var URL = window.URL || window.webkitURL;
    var urlObject;


    $.createWebsocket = function(args) {

        var o = $.extend({
            url: 'wss://' + document.domain + '/analogws',
            onopen: $.noop,
            onclose: $.noop,
            onerror: $.noop,
            onmessage: $.noop,
            imageSelector: null,
            indicatorSelector: '#websock',
            cssOpen: 'websock-open',
            cssClosed: 'websock-closed',
            reconnectTimeout: 1000,
        }, args);

        var WS = {
            socket: null,
            backlog: null,

            connect: function() {
                var self = this;

                self.socket = new window.WebSocket(o.url);

                self.socket.onopen = function(ev) {
                    $(o.indicatorSelector).removeClass(o.cssClosed).addClass(o.cssOpen);
                    console.log("WS OPEN");
                    o.onopen(ev);

                    if (self.backlog) {
                        self.socket.send(self.backlog);
                        self.backlog = null;
                    }
                };

                self.socket.onclose = function(ev) {
                    $(o.indicatorSelector).removeClass(o.cssOpen).addClass(o.cssClosed);
                    console.log("WS CLOSE");

                    o.onclose(ev);

                    setTimeout(function() {
                        self.connect();
                    }, o.reconnectTimeout);

                };

                self.socket.onmessage = function(ev) {
                    o.onmessage(ev);

                    if (o.imageSelector) {

                        if (urlObject) {
                            URL.revokeObjectURL(urlObject);
                        }
                        urlObject = URL.createObjectURL(new Blob([ev.data]));

                        var img = new Image;
                        img.src = urlObject;
                        img.onload = function() {
                            $(o.imageSelector)[0].getContext('2d').drawImage(img, 0, 0);
                        };

                        // $(o.imageSelector)[0].src = urlObject;
                    }
                };

                self.socket.onerror = function(ev) {
                    $(o.indicatorSelector).removeClass(o.cssOpen).addClass(o.cssClosed);
                    console.log("WS ERROR");
                    self.socket.close();
                };

            },

            send: function(data) {
                var self = this;
                if (self.socket.readyState === self.socket.OPEN) {
                    self.socket.send(data);
                } else {
                    self.backlog = data;
                }
            },

            sendJSON: function(data) {
                var self = this;
                self.send(JSON.stringify(data));
            }


        }

        WS.connect();

        return WS;

    }

}(jQuery));
