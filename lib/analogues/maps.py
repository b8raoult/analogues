import tempfile
import os
import json
import numpy as np
import threading
import sys
import hashlib
import xarray as xr
from contextlib import closing

for n in ('LD_LIBRARY_PATH', 'DYLD_LIBRARY_PATH'):
    os.environ[n] = '/opt/ecmwf/magics/lib:/Users/baudouin/build/magics/lib'


# os.environ['MAGPLUS_HOME'] = '/Users/baudouin/build/magics'

sys.path.append('/opt/ecmwf/magics/lib/python2.7/site-packages')

from Magics import macro


LOCK = threading.Lock()

PROJECTIONS = {
    "global": macro.mmap(subpage_upper_right_longitude=180.00,
                         subpage_upper_right_latitude=90.00,
                         subpage_lower_left_latitude=-90.00,
                         subpage_lower_left_longitude=-180.0,
                         subpage_map_projection='cylindrical'),
    "uk": macro.mmap(subpage_upper_right_longitude=1.5,
                     subpage_upper_right_latitude=60.00,
                     subpage_lower_left_latitude=44.5,
                     subpage_lower_left_longitude=-14.0,
                     subpage_map_projection='cylindrical'),
    "france": macro.mmap(subpage_upper_right_longitude=10.5,
                         subpage_upper_right_latitude=52.5,
                         subpage_lower_left_latitude=37.0,
                         subpage_lower_left_longitude=-5.0,
                         subpage_map_projection='cylindrical'),
}


ONOFF = {False: 'off',
         True: 'on'}


def identity(x):
    return x


def as_plottable(field, position=0, metadata=None, preproc=None):

    # print('as_plottable', preproc)

    if isinstance(field, str):
        grib = macro.mgrib(grib_input_file_name=field,
                           grib_file_address_mode='byte_offset',
                           grib_field_position=position)
        return grib, None, metadata, 'path'

    if hasattr(field, 'path') and hasattr(field, 'offset') and hasattr(field, 'area'):
        grib = macro.mgrib(grib_input_file_name=field.path,
                           grib_file_address_mode='byte_offset',
                           grib_field_position=int(field.offset))
        return grib, field.area, metadata, 'gridfield'

    if isinstance(field, xr.DataArray):
        if metadata is None:
            metadata = {}
            grib = {}
            for k, v in field.attrs.items():
                if k.startswith('GRIB_'):
                    grib[k[5:]] = str(v)
                else:
                    metadata[k] = str(v)

            # Only key GRIB
            if grib:
                metadata = grib

        n, w, s, e = float(field.latitude[0]), float(field.longitude[0]), float(field.latitude[-1]), float(field.longitude[-1])
        ns = float(field.latitude[1]) - float(field.latitude[0])
        ew = float(field.longitude[1]) - float(field.longitude[0])

        grib = macro.minput(input_field=field.values,
                            input_field_initial_latitude=n,
                            input_field_latitude_step=ns,
                            input_field_initial_longitude=w,
                            input_field_longitude_step=ew,
                            input_metadata=metadata,)
        return grib, (n, w, s, e), metadata, 'xarray'

    if hasattr(field, 'array'):
        ew, ns = field.grid
        n, w, s, e = field.area
        if metadata is None:
            metadata = field.metadata

        if preproc:
            f = preproc
        else:
            f = identity

        grib = macro.minput(input_field=f(field.array),
                            input_field_initial_latitude=float(n),
                            input_field_latitude_step=-float(ns),
                            input_field_initial_longitude=float(w),
                            input_field_longitude_step=float(ew),
                            input_metadata=metadata,)
        return grib, (n, w, s, e), metadata, 'bespoke'

    if isinstance(field, np.ndarray):
        class F:
            def __init__(self, f):
                self.array = f
                self.grid = metadata['grid']
                self.area = metadata['area']

        return as_plottable(F(field), metadata=metadata, preproc=preproc)

    if isinstance(field, list):
        if isinstance(position, list):
            return [as_plottable(f, p, metadata) for (f, p) in zip(field, position)]
        else:
            return [as_plottable(f, 0, metadata) for f in field]

    raise ValueError("Cannot plot %s" % (type(field), ))


def make_contour(contour, legend):

    if isinstance(contour, list):
        return [make_contour(c, legend) for c in contour]

    if contour is not None:
        if isinstance(contour, str):
            return macro.mcont(contour_automatic_setting='ecmwf',
                               legend=legend,
                               contour_style_name=contour,)
        else:
            d = dict(**contour)
            d['legend'] = legend
            return macro.mcont(**d)
    else:
        return macro.mcont(contour_automatic_setting='ecmwf', legend=legend,)


def plot_to_file(field,
                 file,
                 size=10.,
                 projection=None,
                 contour=None,
                 grid=True,
                 title=True,
                 title_text='Title',
                 width=400,
                 ratio=1.0,
                 area=None,
                 metadata=None,
                 text_format='(automatic)',
                 position=0,
                 format=None,
                 preproc=None,
                 legend=False,
                 boxes=[]):

    plottable = as_plottable(field, position, metadata, preproc)
    if isinstance(plottable, list):
        _, in_file_area, metadata, what = plottable[0]
        grib = [g[0] for g in plottable]
    else:
        grib, in_file_area, metadata, what = plottable

    # print("XXXX PLOT", what, "metadata =>", metadata,
    #       "contour => ", contour,
    #       "area =>", area)

    if projection is None:
        if area is None:
            area = in_file_area

        if area:
            n, w, s, e = area
            projection = macro.mmap(subpage_upper_right_longitude=float(e),
                                    subpage_upper_right_latitude=float(n),
                                    subpage_lower_left_latitude=float(s),
                                    subpage_lower_left_longitude=float(w),
                                    subpage_map_projection='cylindrical')
        else:
            projection = macro.mmap(subpage_map_projection='cylindrical')

    if isinstance(projection, str):
        projection = PROJECTIONS[projection]

    contour = make_contour(contour, legend)

    if isinstance(grib, list) and not isinstance(contour, list):
        contour = [contour] * len(grib)

    base, ext = os.path.splitext(file)
    if format is None:
        format = ext[1:]
    output = macro.output(output_formats=[format],
                          output_name_first_page_number='off',
                          page_x_length=float(size),
                          page_y_length=float(size) * ratio,
                          super_page_x_length=float(size),
                          super_page_y_length=float(size) * ratio,
                          subpage_x_length=float(size),
                          subpage_y_length=float(size) * ratio,
                          subpage_x_position=0.,
                          subpage_y_position=0.,
                          output_width=width,
                          page_frame='on',
                          page_id_line='off',
                          output_name=base)

    foreground = macro.mcoast(map_grid=ONOFF[grid],
                              map_label='off')

    background = macro.mcoast(map_grid=ONOFF[grid],
                              map_grid_colour='tan',
                              map_label='off',
                              map_coastline_land_shade='on',
                              map_coastline_land_shade_colour='cream',
                              map_coastline_colour='tan')
    data = []
    data.append(background)

    if isinstance(grib, list):
        for g, c in zip(grib, contour):
            data.append(g)
            data.append(c)
    else:
        data.append(grib)
        data.append(contour)

    data.append(foreground)

    bb = float(len(boxes) + 1)
    for i, b in enumerate(boxes):
        inc = 0.1
        n, w, s, e = b
        a = np.ones(((e - w + inc) / inc - 2, ((n - s + inc) / inc) - 2))
        a = np.pad(a, 1, 'constant', constant_values=0)

        b = macro.minput(input_field=a,
                         input_field_initial_latitude=float(n),
                         input_field_latitude_step=-float(inc),
                         input_field_initial_longitude=float(w),
                         input_field_longitude_step=float(inc),
                         input_metadata={})
        data.append(b)
        # print a.shape

        d = "rgba(1,0,0,%g)" % (i / bb)

        c = macro.mcont(contour="off",
                        contour_shade="on",
                        contour_shade_method="area_fill",
                        contour_shade_max_level_colour=d,
                        contour_shade_min_level_colour=d,)

        data.append(c)

    if title:
        data.append(macro.mtext())

    if legend:
        width = 1000
        height = 200
        width_cm = float(width) / 40.
        height_cm = float(height) / 40.
        output = macro.output(output_formats=[format],
                              output_name_first_page_number='off',
                              # output_cairo_transparent_background='on',
                              output_width=width,
                              super_page_x_length=width_cm,
                              super_page_y_length=height_cm,
                              output_name=base,
                              subpage_frame=False,
                              page_frame=False,
                              page_id_line=False)

        leg = macro.mlegend(
            legend_title="on",
            legend_title_font_size=1.1,
            legend_display_type="continuous",
            legend_title_text=title_text,
            legend_text_colour="charcoal",
            legend_box_mode="positional",
            legend_text_format=text_format,
            legend_box_x_position=0.00,
            legend_box_y_position=0.00,
            legend_box_x_length=width_cm,
            legend_box_y_length=height_cm,
            legend_box_blanking="on",
            legend_text_font_size="15%",
            legend_border=False,
            legend_border_colour="rgb(0.18,0.18,0.62)"
        )

        with LOCK:
            # print(output, data[1], data[2], leg)
            macro.plot(output, data[1], data[2], leg)
        return

    data.append(macro.page())

    # print(output, projection, data)

    with LOCK:
        macro.plot(output, projection, data)


def cached_plot(field, cache, format='png', key=None, **kwargs):

    if key is None:
        key = dict(field=field, kwargs=kwargs)
        key = json.dumps(key, sort_keys=True)
        key = hashlib.md5(key.encode('utf-8')).hexdigest()

    result = os.path.join(cache, key + '.' + format)
    if not os.path.exists(result):

        if format == 'grib':
            from grib import GribFile
            offset = kwargs['position']
            length = GribFile(field).at_offset(offset).totalLength
            with open(field, 'rb') as f:
                f.seek(offset)
                try:
                    with open(result, 'wb') as g:
                        g.write(f.read(length))
                except Exception:
                    if os.path.exists(result):
                        os.path.unlink(result)
                    raise

        else:
            plot_to_file(field, result, **kwargs)

    return result


def plot_open(field, cache=None, **kwargs):

    if cache:
        return open(cached_plot(field, cache, **kwargs))

    fd, tmp = tempfile.mkstemp('.' + kwargs.get("format", "png"))
    os.close(fd)

    print(tmp, field)
    plot_to_file(field, tmp, **kwargs)

    f = open(tmp, 'rb')

    os.unlink(tmp)

    return f


def plot(field, save=None, **kwargs):

    if save:
        plot_to_file(field, save, **kwargs)

    from IPython.display import Image

    fd, tmp = tempfile.mkstemp('.' + kwargs.get("format", "png"))
    os.close(fd)

    plot_to_file(field, tmp, **kwargs)
    img = Image(tmp)

    os.unlink(tmp)

    return img


def plot_from_data(data, format='png'):

    class Plottable:

        def __init__(self, values, shape, metadata, **kwargs):
            self.array = np.reshape(np.array(values), tuple(shape))
            self.area = metadata.pop('area')
            self.grid = metadata.pop('grid')
            self.metadata = metadata

    field = Plottable(**data)
    contour = data.get("metadata", {}).get("contour")

    if 'field2' in data:
        data2 = data['field2']
        field = [field, Plottable(**data2)]
        contour = [contour, data2.get("metadata", {}).get("contour")]

        if data.get('zindex', 0) > data2.get('zindex', 0):
            field = [field[1], field[0]]
            contour = [contour[1], contour[0]]

    with closing(plot_open(field, contour=contour, format=format)) as f:
        return f.read()


if __name__ == '__main__':
    from collections import namedtuple
    import resource
    size = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    print('size', size / 1024, 'mb')

    for n in range(0, 20):

        Field = namedtuple('Field', ['array',
                                     'area',
                                     'first_latitude',
                                     'latitude_increment',
                                     'first_longitude',
                                     'longitude_increment',
                                     'metadata'])
        field = Field(np.random.rand(32, 32) * 10.0 + 273.15,
                      [60.0, -14.0, 44.5, 1.5],
                      60.0,
                      1.5,
                      -14.0,
                      1.5,
                      dict(level=2,
                           marsClass='ei',
                           marsStream='oper',
                           marsType='an',
                           paramId=167,
                           typeOfLevel='surface',
                           units='K'))

        plot_to_file(field, 'test.png')
        newsize = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        print('increment', (newsize - size) / 1024, 'mb')
        size = newsize
        print('size', size / 1024, 'mb')
