--- psql -U cdsuser analogues < analogues/database.sql


-- DROP TABLE file;
-- DROP TABLE fingerprint;
-- DROP TABLE domain;
-- DROP TABLE dataset;
-- DROP TABLE param;

-- create or replace function hamming_distance(bigint, bigint)
-- returns int
-- as '/home/cds/pghammer/hamming_distance.so', 'hamming_distance'
-- LANGUAGE C STRICT;


-- CREATE TABLE IF NOT EXISTS domain (
--     name  VARCHAR(7) UNIQUE NOT NULL CHECK (name <> ''),
--     north real NOT NULL,
--     west  real NOT NULL,
--     south real NOT NULL,
--     east  real NOT NULL
-- );

-- INSERT INTO domain (name, north, west, south, east)
-- VALUES ('uk', 60, -14, 44.5, 1.5)
-- ON CONFLICT DO NOTHING;

-- SELECT * FROM domain;


-- -----------------------------------------------------
-- CREATE TABLE IF NOT EXISTS dataset (
--     name  VARCHAR(7) UNIQUE NOT NULL CHECK (name <> ''),
--     mars  VARCHAR(255)
-- );

-- INSERT INTO dataset (name, mars)
-- VALUES ('era5', 'class=ea,dataset=reanalysis')
-- ON CONFLICT DO NOTHING;

-- SELECT * FROM dataset;

-- -----------------------------------------------------

-- CREATE TABLE IF NOT EXISTS param (
--     name    VARCHAR(7) UNIQUE NOT NULL CHECK (name <> ''),
--     paramId INTEGER,
--     level   INTEGER,
--     title   VARCHAR(255),
--     mars    VARCHAR(255),
--     contour JSON,
--     scale   REAL,
--     offset_ REAL,
--     units   VARCHAR(80)
-- );



-----------------------------------------------------
CREATE TABLE IF NOT EXISTS alpha (
  param   VARCHAR(255),
  domain  VARCHAR(255),
  dataset VARCHAR(255),
  alpha   REAL,
  minimum REAL,
  maximum REAL,
  mean    REAL,
  CONSTRAINT alpha_inx UNIQUE (param, domain, dataset)
);


-- --- ALTER TABLE param  ADD COLUMN contour JSON;

-- INSERT INTO param (name, mars, paramId, level, title, contour)
-- VALUES ('tp', 'param=tp,levtype=sfc', 228, 0,
--         'Total precipitations', '"sh_blured_f05t300lst"')
-- ON CONFLICT DO NOTHING;

-- INSERT INTO param (name, mars, paramId, level, title)
-- VALUES ('2t', 'param=2t,levtype=sfc', 167, 0, 'Surface air temperature')
-- ON CONFLICT DO NOTHING;

-- INSERT INTO param (name, mars, paramId, level, title)
-- VALUES ('msl', 'param=msl,levtype=sfc', 151, 0, 'Mean sea level pressure')
-- ON CONFLICT DO NOTHING;

-- INSERT INTO param (name, mars, paramId, level, title, contour)
-- VALUES ('sd', 'param=sd,levtype=sfc', 141, 0, 'Snow depth',

-- '{"contour": "off", "contour_hilo": "off", "contour_label": "off", "contour_level_list": [0.001, 0.002, 0.005, 0.01, 0.015, 0.02, 0.03, 0.04, 0.05, 0.07, 0.1, 0.2, 0.5, 10.0], "contour_level_selection_type": "level_list", "contour_reference_level": 0.01, "contour_shade": "on", "contour_shade_colour_list": ["rgb(0.45,0.6,0.45)", "rgb(0.59,0.75,0.59)", "rgb(0.73,0.84,0.73)", "rgb(0.87,0.87,0.87)", "rgb(0.94,0.94,0.94)", "rgb(1,1,1)", "rgb(0.9,0.95,1)", "rgb(0.8,0.9,1)", "rgb(0.67,0.83,1)", "rgb(0.5,0.75,1.0)", "rgb(0.85,0.8,1)", "rgb(0.75,0.68,1)", "rgb(0.6,0.5,1)"], "contour_shade_colour_method": "list", "contour_shade_label_blanking": "off", "contour_shade_max_level": 10.0, "contour_shade_method": "area_fill", "contour_shade_min_level": 0.001}'

-- )
-- ON CONFLICT DO NOTHING;

-- INSERT INTO param (name, mars, paramId, level, title)
-- VALUES ('sp', 'param=sp,levtype=sfc', 134, 0, 'Surface pressure')
-- ON CONFLICT DO NOTHING;

-- -- Althoug level is 10m, grib_api returns level=0
-- INSERT INTO param (name, mars, paramId, level, title, contour)
-- VALUES ('ws', 'param=10u,levtype=sfc,field=u;param=10v,levtype=sfc,field=v;formula="sqrt(u*u+v*v)"',
--   10, 0, '10m wind speed', '"sh_red_f5t70lst"')
-- ON CONFLICT DO NOTHING;

-- INSERT INTO param (name, mars, paramId, level, title)
-- VALUES ('z500', 'param=z,levtype=pl,level=500', 129, 500, 'Geopotential at 500 hPa')
-- ON CONFLICT DO NOTHING;

-- INSERT INTO param (name, mars, paramId, level, title)
-- VALUES ('z850', 'param=z,levtype=pl,level=850', 129, 850, 'Geopotential at 850 hPa')
-- ON CONFLICT DO NOTHING;

-- SELECT * FROM param;

-----------------------------------------------------

