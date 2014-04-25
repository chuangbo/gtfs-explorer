# [GTFS Explorer](http://gtfs.chuangbo.li)

Disclaimer: It's a EXPERIMENTAL tool for explore GTFS data. It's not a complete production, more like sort of notes of me on learning GTFS.

![GTFS Explorer Stops View](https://github.com/chuangbo/gtfs-explorer/raw/master/screenshoot-stops.png)

![GTFS Explorer Route View](https://github.com/chuangbo/gtfs-explorer/raw/master/screenshoot-route.png)

### What is GTFS?
[GTFS](https://developers.google.com/transit/gtfs/) = General Transit Feed Specification

## Features

- Single Page App
- Load minimum data for display information, not load all the city's data entirely
- Go back and forword the history of map view
- Friendly UI
- GTFS data parser, from GTFS to Django's dump data format

## Installation

### Dependencies
- PostGIS 2
- Django 1.6 (virtualenv is highly recommended.)
- GTFS data (Auckland's data is included)

### Prepare Database and Virtualenv

#### on a lovely Mac

It's very simple.

1. Download Postgres.app, it also contains PostGIS, so sweet.
2. Install `GDAL Complete` from http://www.kyngchaos.com/software/frameworks

And then,

```sh
$ virtualenv env
$ . env/bin/activate
$ pip install -r requirements.txt
$ # Done!
```

#### Ubuntu server, precise 12.04 LTS

First, prepare the database.

```sh
$ # add PostGIS Apt source, you might need sudo if you are not root
$ echo 'deb http://apt.postgresql.org/pub/repos/apt/ precise-pgdg main' > /etc/apt/sources.list.d/pgdg.list
$ wget --quiet -O - http://apt.postgresql.org/pub/repos/apt/ACCC4CF8.asc | sudo apt-key add -
$ apt-get update
$ apt-get install postgresql-9.3 postgresql-9.3-postgis
$ su - postgres
$ createuser --createdb -P gtfs # input password here, twice
$ createdb -O gtfs gtfs
$ psql gtfs
gtfs=# CREATE EXTENSION postgis;
gtfs=# \q
```

And, install gdal and PostgreSQL-dev for compiling python's library `psycopg2`

```sh
$ apt-get install binutils libproj-dev gdal-bin
$ apt-get install libpq-dev
```

And the same here,

```sh
$ virtualenv env
$ . env/bin/activate
$ pip install -r requirements.txt
$ # Done!
```

### How to import initial data of GTFS of Auckland City

First of all, you sould prepare the database named `gtfs` by default of PostgreSQL with PostGIS extension. I would assume that you could do this and skip this step. If you do not know how to do this, check GeoDjango installation documents out first, I'm pretty sure they can help you.

*You can find this GTFS data on http://www.gtfs-data-exchange.com/agency/auckland-transport/.*

```sh
$ wget http://gtfs.s3.amazonaws.com/auckland-transport_20140416_0216.zip
$ unzip auckland-transport_20140416_0216.zip -d Feed_2014-03-12
$ python explorer/data/gtfs2django_data.py Feed_2014-03-12 > init_data.json
$ ./manage.py syncdb # create the table
$ ./manage.py loaddata init_data.json
$ ./manage.py update_index # create the search indexes
$ # Done!
```

## Testing

TODO

## License

Copyright (c) 2014 Chuangbo Li Licensed under the MIT license.
