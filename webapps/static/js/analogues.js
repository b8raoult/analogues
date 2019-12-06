$(function() {

    var SIZE = 32;
    var SIZE2 = SIZE * SIZE;

    var ctx = document.getElementById('canvas').getContext("2d");
    var lastX, lastY;
    var CANVAS = $("#canvas");

    var WIDTH = canvas.width;
    var HEIGHT = canvas.height;

    var DW = WIDTH / SIZE;
    var DH = HEIGHT / SIZE;
    var RADIUS = 3.0;
    var PRESSURE = 4.0;

    var WEIGHTS = [0.5, 0.5];

    var FIELD = {
        min: 0,
        max: 255
    };

    var USE_L2;
    var FIELD2;
    var SHOW_W;

    var REQS = 0;
    var over_ok = false;

    var mousePressed = false;

    var UPDATE_MAP_COUNTER = 0;
    var LAST_UPDATE_MAP_COUNTER_RECEIVED = 0;

    var VALUES = new Array(SIZE * SIZE);
    var MINIMUM = new Array(SIZE * SIZE);
    var MAXIMUM = new Array(SIZE * SIZE);

    var timeout = null;
    var constaintsTimeout = null;
    var MASK = false;
    var MASK_THRESHOLD = null;
    var FINGERPRINT;
    var BITMASK;

    var CONSTAINTS = false;

    var MATCHES = {};

    var DATE_CLUSTERING = 4;

    var METHOD;


    var WS;

    if (USE_WS) {
        WS = $.createWebsocket({
            imageSelector: '#map',
        });
    } else {
        WS = $.noWebsocket({
            imageSelector: '#map',
            url: BACKUP_WEB_SOCKET_URL,
        });
    }


    for (var i = 0; i < VALUES.length; i++) {
        VALUES[i] = 127;
    }

    function xy2i(x, y) {
        return Math.floor(x / DW) + Math.floor(y / DH) * SIZE;
    }

    function ij2k(i, j) {
        return i * SIZE + j;
    }

    function clear() {
        $('#message').hide();
    }

    function get_ratio() {
        var mn = FIELD.min;
        var mx = FIELD.max;

        if (mn === mx) {
            return 1.0;
        } else {
            return 255.0 / (mx - mn);
        }
    }

    function fail(e) {

        var text = "?";

        if (e && e.responseJSON) {
            text = e.responseJSON.traceback.join("\n");
        } else {
            if (e.responseText) {
                text = e.responseText;
            } else {
                text = e.statusText;
            }
        }

        $('#message').show().text(text);
        console.log(e);
    }

    function _update_map() {
        var data = $.extend({
                values: FIELD.values,
                metadata: FIELD.metadata,
                shape: FIELD.shape,
                fielddate: FIELD.fielddate,
                counter: ++UPDATE_MAP_COUNTER,
                zindex: FIELD.options.zindex
            },
            FIELD.options);



        if (FIELD2) {
            data['field2'] = {
                values: FIELD2.values,
                metadata: FIELD2.metadata,
                shape: FIELD2.shape,
                fielddate: FIELD2.fielddate,
                zindex: FIELD2.options.zindex
            };
            data['weights'] = WEIGHTS;
        }


        WS.sendJSON(data);
    }

    function download_pdf() {
        var data = $.extend({
                values: FIELD.values,
                metadata: FIELD.metadata,
                shape: FIELD.shape,
                fielddate: FIELD.fielddate,
                counter: ++UPDATE_MAP_COUNTER,
                zindex: FIELD.options.zindex
            },
            FIELD.options);



        if (FIELD2) {
            data['field2'] = {
                values: FIELD2.values,
                metadata: FIELD2.metadata,
                shape: FIELD2.shape,
                fielddate: FIELD2.fielddate,
                zindex: FIELD2.options.zindex
            };
            data['weights'] = WEIGHTS;
        }

        var WS = $.noWebsocket({
            url: MAP_PDF_URL,
        })

        WS.getPDF(data, 'map.pdf');
    }

    function download_json() {
        var data = $.extend({
                values: FIELD.values,
                metadata: FIELD.metadata,
                shape: FIELD.shape,
                fielddate: FIELD.fielddate,
                counter: ++UPDATE_MAP_COUNTER,
                zindex: FIELD.options.zindex
            },
            FIELD.options);



        if (FIELD2) {
            data['field2'] = {
                values: FIELD2.values,
                metadata: FIELD2.metadata,
                shape: FIELD2.shape,
                fielddate: FIELD2.fielddate,
                zindex: FIELD2.options.zindex
            };
            // data['weights'] = WEIGHTS;
        }

        data = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(data));
        $.download(data, 'map.json')
    }

    function download_canvas() {

        var data = {
            width: SIZE,
            height: SIZE,
            values: VALUES,
            minimum: FIELD.min,
            maximum: FIELD.max,
        };

        var WS = $.noWebsocket({
            url: CANVAS_PDF_URL,
        })

        console.log(data);

        WS.getPDF(data, 'canvas.pdf');
    }

    function fingerprint_bits(sel, bits, other, mask) {
        var n = Math.sqrt(bits.length);
        var b = 0;
        sel.empty();
        for (var i = 0; i < n; i++) {
            var div = $("<div>").appendTo(sel);
            for (var j = 0; j < n; j++) {

                var c = "no-other";

                if (other) {
                    c = other[b] === bits[b] ? "match" : "no-match";
                }

                if (mask && mask[b]) {
                    c = "masked";
                }

                $("<span>").text(bits[b]).appendTo(div).addClass(c);
                b++;
            }
        }
    }

    function fingerprint_value(sel, value) {
        sel.text(value);
    }


    function update_bits(date) {


        fingerprint_bits($("#query-bits"), FINGERPRINT.bits, MATCHES[date].fingerprint.bits, BITMASK);
        fingerprint_value($("#query-value"), FINGERPRINT.value, MATCHES[date].fingerprint.value);
        if (BITMASK) {
            $("#mask-bits").show();
            fingerprint_bits($("#mask-bits"), BITMASK);
        } else {
            $("#mask-bits").hide();
        }

        fingerprint_bits($("#result-bits"), MATCHES[date].fingerprint.bits, FINGERPRINT.bits, BITMASK);
        fingerprint_value($("#result-value"), MATCHES[date].fingerprint.value, FINGERPRINT.value);
    }



    function update_minimum_maximum() {

        if (CONSTAINTS) {
            for (var i = 0; i < MAXIMUM.length; i++) {
                MAXIMUM[i] = FIELD.clim.maximum_field[i];
            }

            for (var i = 0; i < MINIMUM.length; i++) {
                MINIMUM[i] = FIELD.clim.minimum_field[i];;
            }
        } else {

            for (var i = 0; i < MAXIMUM.length; i++) {
                MAXIMUM[i] = FIELD.max;
            }

            for (var i = 0; i < MINIMUM.length; i++) {
                MINIMUM[i] = FIELD.min;
            }
        }

        console.log(MINIMUM);
        console.log(MAXIMUM);

    }


    function constaints() {
        CONSTAINTS = $(this).is(':checked');

        if (CONSTAINTS) {
            check_constrains();
        } else {
            if (constaintsTimeout) {
                clearTimeout(constaintsTimeout);
            }
            constaintsTimeout = null;
        }
    }

    function use_l2() {
        USE_L2 = $(this).is(':checked');
        update();

    }


    function show_w() {
        SHOW_W = $(this).is(':checked');
        update();

    }


    function _update_best(limit, rerun) {

        if (!limit) {
            if (FIELD2) {
                limit = 1000;
            } else {
                limit = 100;
            }
        }

        var data = {
            values: FIELD.values,
            metadata: FIELD.metadata,
            shape: FIELD.shape,
            fielddate: FIELD.fielddate,
            counter: ++UPDATE_MAP_COUNTER,
            use_l2: USE_L2,
            date_clustering: DATE_CLUSTERING,
            method: METHOD,
            limit: limit,
        };
        // console.log(FIELD.options);

        if (FIELD2) {
            data['field2'] = $.extend({
                values: FIELD2.values,
                metadata: FIELD2.metadata,
                shape: FIELD2.shape,
                fielddate: FIELD2.fielddate,
            }, FIELD2.options);
            data['weights'] = WEIGHTS;

            console.log(FIELD2.options);
        }


        if (!rerun) {
            clear();
            $(".closest-img").attr('src', AJAX_LOADER);
            $(".closest-label").text('-');
        }

        $.ajax({
            url: BEST_MATCH_URL,
            type: 'post',
            dataType: 'json',
            contentType: "application/json; charset=utf-8",
            data: JSON.stringify($.extend(data, FIELD.options)),
        }).done(function(result) {

            if (result.counter != UPDATE_MAP_COUNTER) {
                return;
            }

            // $(".closest-img").attr('src',
            //     'data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7');


            // if (result.counter == REQS) {

            var $images = $(".closest-img");
            var $labels = $(".closest-label");

            var extra = '';
            if(SHOW_W) {
                extra = '?depth=3';
            }

            $.each(result.matches, function(i, v) {

                $($images[i]).attr('src', v.url + extra).data('date', v.date).data('url', v.url);
                // $($labels[i]).text(v.date + ' ' + v.distance);
                $($labels[i]).text(v.date.replace('T', ' '));

            });
            // }

            if (result.matches.length < $images.length) {
                _update_best(limit * 2, true);
            }

        }).fail(fail);

    }

    function download_closest() {

        $(".closest-img").each(function(i) {
            var e = $(this);
            var v = {
                'url': e.data('url'),
                'date': e.data('date')
            };

            var extra = '';
            if(SHOW_W) {
                extra = '&depth=3';
            }

            setTimeout(function() {
                console.log(i, v.url, v.date);
                $.download(v.url + '?format=pdf' + extra, '' + i + '-' + v.date + '.pdf');
            }, (i+1) * 2000);

            if(i == 0) {
                 setTimeout(function() {
                    console.log(i, v.url, v.date);
                    $.download(v.url + '?format=grib', OPTIONS.param + '-' + v.date + '.grib');
                }, 1000);
            }

        });

    }

    var update_map = $.throttle(_update_map, 500);
    var update_best = $.debounce(_update_best, 2000);

    function rescale() {
        var mn = null;
        var mx = null;
        $.each(VALUES, function(_, v) {

            if (mn === null || v < mn) {
                mn = v;
            }

            if (mx === null || v > mx) {
                mx = v;
            }
        });

        if (mn === mx) {
            for (var i = 0; i < VALUES.length; i++) {
                VALUES[i] = mn;
            }
        } else {
            var min = FIELD.min;
            var max = FIELD.max;
            for (var i = 0; i < VALUES.length; i++) {
                VALUES[i] = (max - min) * (VALUES[i] - mn) / (mx - mn) + min;
            }
        }
    }

    function _low(centerY, centerX) {

        centerX = centerX === undefined ? SIZE / 2.0 : centerX;
        centerY = centerY === undefined ? SIZE / 2.0 : centerY;

        console.log('x:', centerX, 'y:', centerY);

        for (var i = 0; i < SIZE; i++) {
            for (var j = 0; j < SIZE; j++) {


                var k = i * SIZE + j;
                var x = i - centerX;
                var y = j - centerY;
                VALUES[k] = 1 - Math.exp(-Math.sqrt(x * x + y * y) / SIZE);
            }
        }

        rescale();

    }

    function high(event, centerX, centerY) {
        _low(centerX, centerY);
        for (var i = 0; i < VALUES.length; i++) {
            VALUES[i] = invert(VALUES[i]);
        }
        check_constrains();
        update();
    }

    function low(event, centerX, centerY) {
        _low(centerX, centerY);
        check_constrains();
        update();
    }


    function _trough() {

        var centerX = 0;
        var centerY = SIZE / 2.0;

        for (var i = 0; i < SIZE; i++) {
            for (var j = 0; j < SIZE; j++) {


                var k = i * SIZE + j;
                var x = i - centerX;
                var y = j - centerY;
                VALUES[k] = 1 - Math.exp(-Math.sqrt(x * x + y * y) / SIZE);
            }
        }

        rescale();

    }

    function trough() {
        _trough();
        check_constrains();
        update();
    }

    function ridge() {
        _trough();

        var val = new Array(VALUES.length);
        for (var i = 0; i < VALUES.length; i++) {
            val[i] = VALUES[i];
        }

        for (var i = 0; i < SIZE; i++) {
            for (var j = 0; j < SIZE; j++) {
                var k = i * SIZE + j;
                var l = (SIZE - i - 1) * SIZE + j;
                VALUES[l] = invert(val[k]);
            }
        }
        check_constrains();
        update();
    }

    function min() {
        var x = FIELD.min;
        console.log('set-min', x);
        for (var i = 0; i < VALUES.length; i++) {
            VALUES[i] = x;
        }
        check_constrains();
        update();
    }

    function max() {
        var x = FIELD.max;
        for (var i = 0; i < VALUES.length; i++) {
            VALUES[i] = x;
        }
        check_constrains();
        update();
    }

    function median() {
        var x = (FIELD.max + FIELD.min) / 2.0;
        for (var i = 0; i < VALUES.length; i++) {
            VALUES[i] = x;
        }
        check_constrains();
        update();
    }

    function constant() {
        console.log('constant', CURR);
        for (var i = 0; i < VALUES.length; i++) {
            VALUES[i] = CURR;
        }
        check_constrains();
        update();
    }

    function invert(x) {
        return (FIELD.max - FIELD.min) - (x - FIELD.min) + FIELD.min;
    }

    function inverse() {
        for (var i = 0; i < VALUES.length; i++) {
            VALUES[i] = invert(VALUES[i]);
        }
        check_constrains();
        update();
    }

    function two_fields() {

        if (FIELD2) {
            FIELD2 = null;
            $('#locked')[0].src = "data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7";
            update();
        } else {

            FIELD2 = $.extend({}, FIELD);
            var map = $('#map')[0];
            var url = map.toDataURL("image/png");
            $('#locked')[0].src = url;
            if (OPTIONS.param === 'msl') {
                init({
                    'param': 'tp'
                });
            } else {
                init({
                    'param': 'msl'
                });
            }

        }

    }


    function update(throttle) {

        var imgPixels = ctx.getImageData(0, 0, canvas.width, canvas.height);

        var min = FIELD.min;
        var ratio = get_ratio();
        MASK_THRESHOLD = null;

        for (var y = 0; y < imgPixels.height; y++) {
            for (var x = 0; x < imgPixels.width; x++) {
                var i = (y * 4) * imgPixels.width + x * 4;

                var k = xy2i(x, y);
                var val = VALUES[k];
                var v = 255 - (val - min) * ratio;

                imgPixels.data[i] = v;
                imgPixels.data[i + 1] = v;
                imgPixels.data[i + 2] = v;
                imgPixels.data[i + 3] = 255;

                // if (val >= MAXIMUM[k]) {
                //     // Red
                //     imgPixels.data[i] = 255;
                //     imgPixels.data[i + 1] = 100;
                //     imgPixels.data[i + 2] = 100;

                // }

                // if (val <= MINIMUM[k]) {
                //     // Blue
                //     imgPixels.data[i] = 200;
                //     imgPixels.data[i + 1] = 200;
                //     imgPixels.data[i + 2] = 255;
                // }

                if (MASK) {
                    if (v === 255) {
                        imgPixels.data[i] = 127;
                        imgPixels.data[i + 1] = 255;
                        imgPixels.data[i + 2] = 127;

                        if (MASK_THRESHOLD === null) {
                            MASK_THRESHOLD = val;
                        } else {
                            if (val > MASK_THRESHOLD) {
                                MASK_THRESHOLD = val;
                            }
                        }
                    }
                }
            }
        }

        ctx.putImageData(imgPixels, 0, 0, 0, 0, imgPixels.width, imgPixels.height);


        FIELD.counter = ++REQS;

        if (throttle) {
            update_map();
            update_best();
        } else {
            _update_map();
            _update_best();
        }
    }

    function reset_menu(menu) {
        menu.empty();
        $("<option>").text("-").appendTo(menu);
    }



    function stop() {
        if (timeout) {
            clearInterval(timeout);
            timeout = null;
        }
    }

    function apply_changes(dU) {


        if (CONSTAINTS) {


            for (let i = 0; i < SIZE2; i++) {

                if (isNaN(dU[i])) {
                    console.error('Nan in DU', i, dU[i]);
                    return;
                }

                if (!isFinite(dU[i])) {
                    console.error('Infinite in dU', i, dU[i]);
                    return;
                }
            }

            let x = $.apply_constraints(VALUES, dU,
                FIELD.clim.minimum_field,
                FIELD.clim.maximum_field,
                FIELD.min,
                FIELD.max);

            for (let i = 0; i < SIZE2; i++) {

                if (isNaN(x[i])) {
                    console.error('Nan in X', i, x[i]);
                    return;
                }

                if (!isFinite(x[i])) {
                    console.error('Infinite in X', i, x[i]);
                    return;
                }
            }

            const epsilon = Math.max(Math.abs(FIELD.min),
                Math.abs(FIELD.max)) / 100000.0;

            let changes = 0;
            for (let i = 0; i < SIZE2; i++) {
                if (Math.abs(x[i]) > epsilon) {
                    changes++;
                }
                VALUES[i] += x[i];
            }

            return changes;
            // console.table(VALUES);

        } else {
            for (let i = 0; i < SIZE2; i++) {
                VALUES[i] += dU[i];
            }
        }

        return 0;
    }

    function check_constrains() {
        var zero = Array.from(VALUES, () => 0);
        if (apply_changes(zero)) {
            update(true);
            constaintsTimeout = setTimeout(check_constrains, 100);
            return true;
        }
        return false;
        // update();
    }

    function constaints_once() {
        console.log('constaints_once');
        var save = CONSTAINTS;
        CONSTAINTS = true;
        var zero = Array.from(VALUES, () => 0);
        if (apply_changes(zero)) {
            update(true);
        }
        CONSTAINTS = save;
    }

    function defaultTool() {

        var self = {

            activate: function() {},
            deactivate: function() {},

            update: function(x, y, delta) {

                delta *= 1 / get_ratio();

                stop();

                var kj = Math.floor(x / DW);
                var ki = Math.floor(y / DH);
                var SIGMA2 = RADIUS * RADIUS;

                function doit() {


                    let dU = Array.from(VALUES, () => 0);

                    for (var i = 0; i < SIZE; i++) {
                        for (var j = 0; j < SIZE; j++) {

                            var d = (ki - i) * (ki - i) + (kj - j) * (kj - j);

                            d = PRESSURE * Math.exp(-d / SIGMA2);

                            var k = i * SIZE + j;
                            dU[k] = d * delta;


                        }
                    }

                    apply_changes(dU);



                    update(true);
                }

                doit();

                timeout = setInterval(doit, 100);
            },

            mouseDown: function(e, x, y) {
                if (e.metaKey) {
                    var centerX = x / CANVAS.width() * 32;
                    var centerY = y / CANVAS.height() * 32;
                    if (e.shiftKey) {
                        low(e, centerX, centerY);
                    } else {
                        high(e, centerX, centerY);
                    }
                    return;
                }

                self.update(x, y, e.shiftKey ? -1 : 1);
                mousePressed = true;
            },

            mouseMove: function(e, x, y) {
                if (mousePressed) {
                    stop();
                    self.update(x, y, e.shiftKey ? -1 : 1);
                }
            },

            mouseUp: function(e, x, y) {
                mousePressed = false;
                stop();
            },

            mouseLeave: function(e, x, y) {
                mousePressed = false;
                stop();
            }
        };

        return self;
    }

    function levelingTool() {

        var self = {

            state: 1,

            activate: function() {
                self.radius = RADIUS;
                $("#radius-slider").slider('value', self.state);
            },

            deactivate: function() {
                self.state = RADIUS;
                $("#radius-slider").slider('value', self.radius);
            },

            update: function(x, y) {

                let dU = Array.from(VALUES, () => 0);


                stop();

                var kj = Math.floor(x / DW);
                var ki = Math.floor(y / DH);
                var SIGMA2 = RADIUS * RADIUS;

                function doit() {

                    for (var i = 0; i < SIZE; i++) {
                        for (var j = 0; j < SIZE; j++) {

                            var d = (ki - i) * (ki - i) + (kj - j) * (kj - j);

                            d = Math.exp(-d / SIGMA2);

                            var k = i * SIZE + j;
                            dU[k] = d * (CURR - VALUES[k]);

                        }
                    }

                    apply_changes(dU);

                    update(true);
                }

                doit();

                timeout = setInterval(doit, 100);
            },

            mouseDown: function(e, x, y) {

                if (e.altKey) {
                    var kj = Math.floor(x / DW);
                    var ki = Math.floor(y / DH);
                    CURR = VALUES[ki * SIZE + kj];

                    $("#value").val(to_unit(CURR));
                } else {
                    mousePressed = true;
                    stop();
                    self.update(x, y);
                }
            },

            mouseMove: function(e, x, y) {
                if (mousePressed) {
                    stop();
                    self.update(x, y);
                }
            },

            mouseUp: function(e, x, y) {
                mousePressed = false;
                stop();
            },

            mouseLeave: function(e, x, y) {
                mousePressed = false;
                stop();
            }
        };

        return self;
    }

    function rectTool() {

        var self = {

            state: 1,

            activate: function() {
                // self.radius = RADIUS;
                // $("#radius-slider").slider('value', self.state);
            },

            deactivate: function() {
                // self.state = RADIUS;
                // $("#radius-slider").slider('value', self.radius);
                self.save = null;
            },

            update: function(x, y) {

                if (self.active) {

                    if (self.last_x < self.first_x) {
                        var x = self.last_x;
                        self.last_x = self.first_x;
                        self.first_x = x;
                    }

                    if (self.last_y < self.first_y) {
                        var y = self.last_y;
                        self.last_y = self.first_y;
                        self.first_y = y;
                    }


                    var bj = Math.floor(self.first_x / DW);
                    var bi = Math.floor(self.first_y / DH);

                    var ej = Math.floor(self.last_x / DW);
                    var ei = Math.floor(self.last_y / DH);

                    var eps = 1e-7; // needed for magics

                    for (var i = 0; i < SIZE; i++) {
                        for (var j = 0; j < SIZE; j++) {

                            if (i >= bi && i <= ei && j >= bj && j <= ej) {
                                var k = i * SIZE + j;
                                VALUES[k] = CURR + eps;
                                eps -= eps;
                            }
                        }
                    }

                    update();
                }

            },

            mouseDown: function(e, x, y) {

                if (e.altKey) {
                    var kj = Math.floor(x / DW);
                    var ki = Math.floor(y / DH);
                    CURR = VALUES[ki * SIZE + kj];

                    $("#value").val(to_unit(CURR));
                } else {
                    mousePressed = true;
                    self.first_x = x;
                    self.first_y = y;

                    self.last_x = x;
                    self.last_y = y;
                    self.save = ctx.getImageData(0, 0, canvas.width, canvas.height);
                    self.active = true;

                }
            },

            mouseMove: function(e, x, y) {
                if (mousePressed) {

                    ctx.putImageData(self.save, 0, 0);

                    self.last_x = x;
                    self.last_y = y;

                    ctx.beginPath();

                    ctx.rect(self.first_x,
                        self.first_y,
                        self.last_x - self.first_x,
                        self.last_y - self.first_y);


                    ctx.strokeStyle = 'red';
                    ctx.lineWidth = 2;
                    ctx.stroke();
                }


            },

            mouseUp: function(e, x, y) {
                mousePressed = false;

                ctx.putImageData(self.save, 0, 0);
                self.update();

                self.active = false;
            },

            mouseLeave: function(e, x, y) {
                // mousePressed = false;
            }
        };

        return self;
    }


    var TOOLS = {
        "Default": defaultTool(),
        "Leveling": levelingTool(),
        "Contour (rect)": rectTool(),
    };

    var TOOL;


    $("#tools").change(function() {
        localStorage.setItem("mining-tool", $("#tools").val());
        TOOL.deactivate();
        TOOL = TOOLS[$("#tools").val()];
        TOOL.activate();
    });

    $("#regimes").change(function() {
        var x = $(this).val();
        init({
            'regime': x
        });
    });

    $('#params').change(function() {
        var x = $(this).val();
        init({
            'param': x
        });

    });

    $('#domains').change(function() {
        var x = $(this).val();
        init({
            'domain': x
        });

    });

    $("#methods").change(function() {
        METHOD = $(this).val();
        update();
    });


    $('#canvas').mousedown(function(e) {
        var x = e.pageX - $(this).offset().left;
        var y = e.pageY - $(this).offset().top;
        TOOL.mouseDown(e, x, y);
    });

    $('#canvas').mousemove(function(e) {

        var x = e.pageX - $(this).offset().left;
        var y = e.pageY - $(this).offset().top;
        TOOL.mouseMove(e, x, y);
    });

    $('#canvas').mouseup(function(e) {
        var x = e.pageX - $(this).offset().left;
        var y = e.pageY - $(this).offset().top;
        TOOL.mouseUp(e, x, y);
    });

    $('#canvas').mouseleave(function(e) {
        var x = e.pageX - $(this).offset().left;
        var y = e.pageY - $(this).offset().top;
        TOOL.mouseLeave(e, x, y);
    });


    $('#body').mouseup(function() {
        mousePressed = false;
    });


    $('#map').mousedown(function(e) {
        var x = (e.pageX - $(this).offset().left) / $(this).width() * WIDTH;
        var y = (e.pageY - $(this).offset().top) / $(this).height() * HEIGHT;
        TOOL.mouseDown(e, x, y);
    });

    $('#map').mousemove(function(e) {

        var x = (e.pageX - $(this).offset().left) / $(this).width() * WIDTH;
        var y = (e.pageY - $(this).offset().top) / $(this).height() * HEIGHT;
        TOOL.mouseMove(e, x, y);

    });

    $('#map').mouseup(function(e) {
        var x = (e.pageX - $(this).offset().left) / $(this).width() * WIDTH;
        var y = (e.pageY - $(this).offset().top) / $(this).height() * HEIGHT;
        TOOL.mouseUp(e, x, y);
    });

    $('#map').mouseleave(function(e) {
        var x = (e.pageX - $(this).offset().left) / $(this).width() * WIDTH;
        var y = (e.pageY - $(this).offset().top) / $(this).height() * HEIGHT;
        TOOL.mouseLeave(e, x, y);
    });

    $('#map').on('dragstart', function(event) {
        event.preventDefault();
    });

    $("#pressure-slider").slider({
        min: 1,
        max: 20,
        value: PRESSURE,
        change: function(event, ui) {
            PRESSURE = ui.value;
        }
    });

    $("#radius-slider").slider({
        min: 1,
        max: SIZE / 2,
        value: RADIUS,
        change: function(event, ui) {
            RADIUS = ui.value;
            console.log("RADIUS", RADIUS);
        }
    });

    $("#weigths-slider").slider({
        min: 0,
        max: 100,
        value: 50,
        change: function(event, ui) {
            console.log('WEIGHTS');
            var x = ui.value / 100.0;
            WEIGHTS = [x, 1.0 - x];
            console.log(WEIGHTS);
            // RADIUS = ui.value;
            // console.log("RADIUS", RADIUS);
            // if (FIELD2) {
            _update_best();
            // }
        }
    });

    $("#date-clustering").text(DATE_CLUSTERING);

    $("#date-clustering-slider").slider({
        min: 0,
        max: 365,
        value: DATE_CLUSTERING,
        change: function(event, ui) {
            DATE_CLUSTERING = ui.value;
            $("#date-clustering").text(DATE_CLUSTERING);

            update();
            // RADIUS = ui.value;
            // console.log("RADIUS", RADIUS);
        },
        slide: function(event, ui) {
            $("#date-clustering").text(ui.value);
        }
    });


    function to_unit(x) {
        return Math.round((x + OPTIONS.units.offset) * OPTIONS.units.scale * 100) / 100.0;
    }

    function from_unit(x) {
        return x / OPTIONS.units.scale - OPTIONS.units.offset;
    }

    function init(args) {

        $("#map").attr("src", AJAX_LOADER);
        $("#clim").text("=");

        data = $.extend(OPTIONS, args || {});
        console.log("===>", data);


        clear();


        $.ajax({
            url: GET_FIELD_URL,
            type: 'post',
            dataType: 'json',
            data: JSON.stringify(data)
        }).done(function(result) {

            OPTIONS = $.extend({}, result.options);
            $(".unit").html(OPTIONS.units.unit);

            FIELD = result;

            VALUES = FIELD.values;
            CURR = (FIELD.min + FIELD.max) / 2.0;

            $("#min-value").val(to_unit(FIELD.min));
            $("#max-value").val(to_unit(FIELD.max));
            $("#value").val(to_unit(CURR));

            $("#clim-min").text(to_unit(FIELD.clim.minimum));
            $("#clim-max").text(to_unit(FIELD.clim.maximum));
            $("#clim-mean").text(to_unit(FIELD.clim.mean));
            $("#params").val(OPTIONS.param);
            $("#domains").val(OPTIONS.domain);


            update_minimum_maximum();
            check_constrains();
            update();
            $("#query-date").html(result.fielddate);


        }).fail(fail);
    }

    function _sample_date() {
        var x = $(this).val();
        if (x.length >= 8) {
            init({
                'date': x
            });
        }
    }

    sample_date = $.throttle(_sample_date, 1000);


    $("#min-value").on('input', function() {
        var x = from_unit(parseFloat($(this).val()));
        console.log(x);
        if (!isNaN(x)) {
            FIELD.min = x;
            if (CURR < x) {
                CURR = x;
                $("#value").val(to_unit(CURR));
            }
            update_minimum_maximum();
            rescale();
            update();
        }
    });

    $("#max-value").on('input', function() {
        var x = from_unit(parseFloat($(this).val()));
        console.log(x);
        if (!isNaN(x)) {
            FIELD.max = x;
            if (CURR > x) {
                CURR = x;
                $("#value").val(to_unit(CURR));
            }
            update_minimum_maximum();
            rescale();
            update();
        }
    });

    function _update_min_max() {
        if (CURR > FIELD.max) {
            FIELD.max = CURR;
            $("#max-value").val(to_unit(CURR));
            // rescale();
            update_minimum_maximum();
            update();
        }
        if (CURR < FIELD.min) {
            FIELD.min = CURR;
            $("#min-value").val(to_unit(CURR));

            // rescale();
            update_minimum_maximum();
            update();
        }
    }

    var update_min_max = $.debounce(_update_min_max, 1000);

    $("#value").on('input', function() {
        var x = from_unit(parseFloat($(this).val()));
        console.log(x);
        if (!isNaN(x)) {
            CURR = x;
            update_min_max();
        }
    });


    $("#low").click(low);
    $("#high").click(high);
    $("#ridge").click(ridge);
    $("#trough").click(trough);
    $("#min").click(min);
    $("#max").click(max);
    $("#median").click(median);
    $("#inverse").click(inverse);
    $("#constant").click(constant);


    $("#map-td").click(download_pdf);
    $("#map-json").click(download_json);

    $("#canvas-td").click(download_canvas);
    $("#closest-td").click(download_closest);
    $("#constraints-td").click(constaints_once);

    // $("#analysis").click(analysis);

    $("#user-date").on('input', sample_date);



    $("#constaints").change(constaints);
    $("#use-l2").change(use_l2);
    $("#show-w").change(show_w);

    $("#two-fields").click(two_fields);


    $(".closest-img").click(function() {
        var date = $(this).data('date');
        init({
            'date': date
        });
    })



    var first;

    $.each(TOOLS, function(name, f) {
        if (!first) {
            first = name;
        }
        $("<option>").appendTo("#tools").text(name);
    });

    var f = localStorage.getItem("mining-tool") || first;
    var t = TOOLS[f] ? TOOLS[f] : TOOLS[first];
    TOOL = TOOLS[f];
    TOOL.activate();

    $('#tools').val(f);



    init(true);


    // document.addEventListener('paste', function(e) {
    //     console.log('paste', e);
    //     // https://codepen.io/netsi1964/pen/IoJbg
    // });

});
