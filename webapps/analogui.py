#!/usr/bin/env python3
import sys
print(sys.path)
import os
import json
import numpy as np
from flask import Response
from analogues import PARAMS, REGIMES, Regime, Field, DEFAULT_DOMAIN, DOMAINS
import dateutil
from sklearn.cluster import MeanShift
import datetime
from collections import OrderedDict

import base64
from flask import (Flask,
                   render_template,
                   url_for,
                   send_from_directory,
                   send_file,
                   redirect,
                   jsonify,
                   request)

# sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
# sys.path.append("/Users/baudouin/git/webdev/clients/api/python")

from analogues import conf
from analogues.fingerprint import FingerPrint
from analogues import maps

application = Flask(__name__)
# application.use_x_sendfile = True


def path(json):
    return conf.data_path("%s_%s.grib" % (json['domain'], json['param'],))


def index_for(param):
    return url_for('index1', param=param)


def index(param='tp', domain=DEFAULT_DOMAIN, level=3):
    f = Field(param, domain)
    options = {'param': param,
               'level': level,
               'wavelet': 'haar',
               'units': f.units.to_json(),
               'domain': domain,
               }

    params = OrderedDict()
    for k, v in sorted(PARAMS.items(), key=lambda x: x[1].title):
        params[k] = v

    domains = OrderedDict()
    for k, v in sorted(DOMAINS.items(), key=lambda x: x[1].title, reverse=True):
        domains[k] = v

    regimes = OrderedDict()
    for k, v in sorted(REGIMES.items(), key=lambda x: x[1].title):
        regimes[k] = v

    methods = OrderedDict()
    # for k, v in sorted(METHODS.items(), key=lambda x: x[1].title):
    for k in range(0, 10):
        methods[str(k)] = str(k)

    args = {'options': json.dumps(options, indent=4),
            'params': params,
            'regimes': regimes,
            'domains': domains,
            'methods': methods,
            }

    args.update(options)

    args['use_ws'] = os.environ.get('ANALOGUE_USE_WS', '1')

    return render_template("index.html", **args)


@application.route('/')
def home():
    return redirect(url_for('index0'))


@application.route('/cache/<path:filename>')
def send_cache_file(filename):
    return send_from_directory(conf.ANALOGUES_CACHE, filename)


@application.route('/query/')
def index0():
    return index()


@application.route('/query/<param>/')
def index1(param):
    return index(param)


@application.route('/query/<param>/<domain>')
def index2(param, domain):
    return index(param, domain)


@application.route('/query/<param>/<domain>/<level>/')
def index3(param, domain, level):
    return index(param, domain, level)


@application.route('/get-field/', methods=['POST'])
def get_field():
    data = request.get_json(force=True)
    print(data)

    date = None
    regime = data.pop('regime', None)
    if regime:
        f = Regime.lookup(regime).field
        date = Regime.lookup(regime).date
    else:
        f = Field(**data)

    date = data.get('date', date)
    if date:
        date = dateutil.parser.parse(date)
        # date = date.replace(hour=12)
        print(date)

    field = f.sample(date=date)
    values = field.array
    # if data.get('date'):
    #     values = field.array
    # else:
    #     values = f.mean_field

    # path = conf.data_path("%s_%s.json" % (data['domain'], data['param'],))

    clim = dict(maximum=f.maximum,
                minimum=f.minimum,
                mean=f.mean,
                mean_field=[a for a in f.mean_field.flatten()],
                maximum_field=[a for a in f.maximum_field.flatten()],
                minimum_field=[a for a in f.minimum_field.flatten()],


                gradient_ns_max=[a for a in f.gradient_ns_max.flatten()],
                gradient_sn_max=[a for a in f.gradient_sn_max.flatten()],
                gradient_we_max=[a for a in f.gradient_we_max.flatten()],
                gradient_ew_max=[a for a in f.gradient_ew_max.flatten()],

                gradient_ns_min=[a for a in f.gradient_ns_min.flatten()],
                gradient_sn_min=[a for a in f.gradient_sn_min.flatten()],
                gradient_we_min=[a for a in f.gradient_we_min.flatten()],
                gradient_ew_min=[a for a in f.gradient_ew_min.flatten()],


                )
    # try:
    #     with open(path) as f:
    #         clim = json.loads(f.read())
    # except:
    #     pass

    # constraints = {}
    # for c in ['max', 'min', 'mean']:
    #     path = conf.data_path("%s_%s.%s.numpy" % (data['domain'], data['param'], c,))
    #     z = np.load(path)
    #     constraints[c] = [a for a in z.flatten()]

    metadata = dict()
    metadata.update(field.metadata)
    metadata.update(f.metadata)

    data = json.dumps({'metadata': metadata,
                       'values': [a for a in values.flatten()],
                       'shape': list(values.shape),
                       'domain': list(field.domain),
                       'grid': list(field.grid),
                       'fielddate': field.date,
                       'clim': clim,
                       'options': {
                           'param': f. param,
                           'units': f.units.to_json(),
                           'domain': f.domain,
                           'dataset': f.dataset,
                           'zindex': f.zindex,
                       },
                       'min': np.min(values),
                       'max': np.max(values)})

    return Response(data, mimetype='application/json')


@application.route('/map-pdf-url/', methods=['POST'])
def map_pdf_url():
    data = request.get_json(force=True)
    img = base64.b64encode(maps.plot_from_data(data, format='pdf')).decode("utf-8", "ignore")
    return jsonify(url="data:application/pdf;base64," + img)


def draw_canvas(tmp, size, values, width, height, minimum, maximum):
    import cairo

    def xy2i(x, y):
        return x + y * width

    surface = cairo.PDFSurface(tmp, width * size, height * size)
    ctx = cairo.Context(surface)
    ratio = 1 if minimum == maximum else 1.0 / (maximum - minimum)

    for y in range(0, 32):
        for x in range(0, 32):
            k = xy2i(x, y)
            v = 1.0 - (values[k] - minimum) * ratio
            ctx.set_source_rgb(v, v, v)
            ctx.rectangle(x * size, y * size, size + 1, size + 1)
            ctx.fill()
    ctx.show_page()


@application.route('/canvas-pdf-url/', methods=['POST'])
def canvas_pdf_url():
    import tempfile

    data = request.get_json(force=True)
    fd, tmp = tempfile.mkstemp('.pdf')
    os.close(fd)
    # tmp = '/tmp/canvas.pdf'

    size = 10

    draw_canvas(tmp, size, **data)

    with open(tmp, 'rb') as f:
        pdf = f.read()

    os.unlink(tmp)

    img = base64.b64encode(pdf).decode("utf-8", "ignore")
    return jsonify(url="data:application/pdf;base64," + img)


@application.route('/backup-web-socket/', methods=['POST'])
def backup_web_socket():
    data = request.get_json(force=True)
    img = base64.b64encode(maps.plot_from_data(data)).decode("utf-8", "ignore")
    return jsonify(url="data:image/png;base64," + img)


@application.route('/plot-field/<date>/<param>/<domain>/<dataset>')
def plot_field(date, param, domain, dataset):

    f = Field(param, domain, dataset)

    path, position = f.grib_path_offset(date=date)
    print("GRIB", path, position)

    if request.args.get('depth'):
        import pywt
        from grib import GribFile

        depth = int(request.args.get('depth')) + 1

        grib = GribFile(path).at_offset(position)
        coeffs = pywt.wavedec2(grib.array, 'haar')
        for n in range(1, depth):
            coeffs[-n] = tuple([np.zeros_like(v) for v in coeffs[-n]])

        field = pywt.waverec2(coeffs, 'haar')

        output = maps.cached_plot(field,
                                  conf.ANALOGUES_CACHE,
                                  key='%s-%s-%s' % (os.path.basename(path), position, depth),
                                  contour=f.metadata.get('contour'),
                                  metadata=grib.metadata,
                                  format=request.args.get('format', 'png'),
                                  area=f.area)

    else:
        output = maps.cached_plot(path,
                                  conf.ANALOGUES_CACHE,
                                  position=position,
                                  contour=f.metadata.get('contour'),
                                  format=request.args.get('format', 'png'),
                                  area=f.area)

    return send_from_directory(conf.ANALOGUES_CACHE, os.path.basename(output))


@application.route('/plot-field/<date>/<param>/<domain>/<dataset>/<param2>')
def plot_field2(date, param, domain, dataset, param2):
    f1 = Field(param, domain, dataset)
    f2 = Field(param2, domain, dataset)

    if f1.zindex > f2.zindex:
        f1, f2 = f2, f1

    path1, position1 = f1.grib_path_offset(date=date)
    path2, position2 = f2.grib_path_offset(date=date)

    png = maps.cached_plot([path1, path2],
                           conf.ANALOGUES_CACHE,
                           position=[position1, position2],
                           contour=[f1.metadata.get('contour'),
                                    f2.metadata.get('contour')],
                           format=request.args.get('format', 'png'),
                           area=f1.area)

    return send_from_directory(conf.ANALOGUES_CACHE, os.path.basename(png))

    return redirect(url_for('send_cache_file',
                            filename=os.path.basename(png)))


CACHE = {}


def field_to_grib_field(f, data):
    key = (f.param, f.domain, f.dataset)
    field = CACHE.get(key)
    if field is None:
        field = f.sample(date=None)
        CACHE[key] = field

    field.set_array(np.reshape(np.array(data['values']), tuple(data['shape'])))
    return field


def best_match_1(f, data, date_clustering):

    field = field_to_grib_field(f, data)

    p = FingerPrint(field.array, 3)

    matches = f.matches(p,
                        extremes=data.get('extremes', False),
                        use_l2=data.get('use_l2', False),
                        limit=data.get('limit', 100),
                        field=field.array,
                        method=data.get('method'))

    filtered_matches = matches
    if date_clustering:
        julian = [a.timestamp() for a, _ in matches]
        julian = np.array(julian).reshape(-1, 1)
        # Cluster by 2 days
        clusters = MeanShift(bandwidth=date_clustering * 24 * 3600).fit(julian).labels_
        seen = set()
        filtered_matches = []
        for entry, c in zip(matches, clusters):
            if c not in seen:
                filtered_matches.append(entry)
                seen.add(c)

    # filtered_matches = matches  # For now
    dates = [{'date': a.isoformat(),
              'url': url_for('plot_field',
                             date=a.isoformat(),
                             param=f.param,
                             domain=f.domain,
                             dataset=f.dataset),
              'distance': b} for a, b in filtered_matches]

    return jsonify(counter=data.get("counter", 0),
                   fingerprint=p.as_json(),
                   matches=dates[:12])


def best_match_2(f1, f2, data1, data2, weigths, date_clustering):

    print('============', f1, f2)
    assert f1.param != f2.param

    field1 = field_to_grib_field(f1, data1)
    field2 = field_to_grib_field(f2, data2)

    p1 = FingerPrint(field1.array, 3)
    p2 = FingerPrint(field2.array, 3)

    matches = f1.matches2(f2, p1, p2, weigths,
                          extremes=data1.get('extremes', False),
                          use_l2=data1.get('use_l2', False),
                          limit=data1.get('limit', 100),
                          field1=field1.array,
                          field2=field2.array)

    filtered_matches = matches
    if date_clustering:
        julian = [a.timestamp() for a, _ in matches]
        julian = np.array(julian).reshape(-1, 1)
        # Cluster by 2 days
        clusters = MeanShift(bandwidth=date_clustering * 24 * 3600).fit(julian).labels_
        seen = set()
        filtered_matches = []
        for entry, c in zip(matches, clusters):
            if c not in seen:
                filtered_matches.append(entry)
                seen.add(c)

    dates = [{'date': a.isoformat(),
              'url': url_for('plot_field2',
                             date=a.isoformat(),
                             param=f1.param,
                             domain=f1.domain,
                             dataset=f1.dataset,
                             param2=f2.param),
              'distance': b} for a, b in filtered_matches]

    return jsonify(counter=data1.get("counter", 0),
                   fingerprint=p1.as_json(),
                   matches=dates)


@application.route('/best-match/', methods=['POST'])
def best_match():
    data = request.get_json(force=True)
    date_clustering = data.get('date_clustering', 4)

    if 'field2' in data:
        data2 = data['field2']
        weigths = data['weights']
        return best_match_2(Field(**data), Field(**data2), data, data2, weigths, date_clustering)
    else:
        return best_match_1(Field(**data), data, date_clustering)


if __name__ == "__main__":
    application.run(debug=True, threaded=True, processes=1)
