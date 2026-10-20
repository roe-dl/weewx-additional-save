# weewx-additional-save
Save certain observation types to a separate database or separate
databases.

This extension is also intended to serve as an example how to write an
archive service for WeeWX.

## Prerequisites

WeeWX from version 5.6 on is required.

## Installation instructions

1) download

   ```shell
   wget -O weewx-additional-save.zip https://github.com/roe-dl/weewx-additional-save/archive/master.zip
   ```

2) run the installer

   WeeWX from version 5.6 on and WeeWX packet installation

   ```shell
   sudo weectl extension install weewx-additional-save.zip
   ```

   WeeWX from version 5.6 on and WeeWX pip installation into an virtual environment

   ```shell
   source ~/weewx-venv/bin/activate
   weectl extension install weewx-additional-save.zip
   ```
   
> [!CAUTION]
> You must not use `sudo` if you installed WeeWX by `pip`.

3) configure databases

   See [Configuration instructions](#configuration_instructions) for
   details.

4) restart weewx

   for SysVinit systems:

   ```shell
   sudo /etc/init.d/weewx stop
   sudo /etc/init.d/weewx start
   ```

   for systemd systems:

   ```shell
   sudo systemctl stop weewx
   sudo systemctl start weewx
   ```

## Configuration instructions

In general you will want to use this extension to save observation types
that are not included in the standard `wview_extended` schema. That may
due to some additional data sources or measuring instruments. A data
service (typically installed as an extension) provides the measurements
of that source or instrument. This extension saves the measurements to
the database.

You may argue that you could simply save them by adding new columns to the 
standard database of WeeWX. This is true for some single observation types, 
but if your service provides lots of additional observation types you may 
want to save them to a separate database. 

The following example shows the principle, how the setup looks like.
Adapt it to your needs.

As an example for additional observation types we install the
[weewx-skyfield-alamanc extension](https://github.com/roe-dl/weewx-skyfield-almanac).
Its base purpose is to provide a replacement for the outdated PyEphem based
almanac. But it also provides additional observation types, which is the
reason we can use it here for our example. Among those additional
observation types is `solarAzimuth` and `solarAltitude`. Say, we want to
graph them, and therefore we need to have them in a database.

First we need a *schema* for our database. A schema is a dictionary holding
2 keys, one for the list of columns and one for list of daily summary
tables. For our example with 2 observation types it looks like this:

```Python
astro_table = [
    ('dateTime',             'INTEGER NOT NULL UNIQUE PRIMARY KEY'),
    ('usUnits',              'INTEGER NOT NULL'),
    ('interval',             'INTEGER NOT NULL'),
    ('solarAzimuth',         'REAL'),
    ('solarAltitude',        'REAL')
]

astro_day_summaries = [
    ('solarAzimuth','scalar'),
    ('solarAltiude','scalar')
]

astro_schema = {
    'table': astro_table,
    'day_summaries' : astro_day_summaries
}
```

Save it to a file, say `additional.py` into the `schemas` directory.

> [!CAUTION]
> Please note that the schema is only observed while creating the database.
> Afterwards it is ignored.

Next step is to edit `weewx.conf`. Our database is represented there by
a binding section and a database section. It looks like this:

```
[DataBindings]
    ...
    [[astro_binding]]
        database = astro_sqlite
        table_name = archive
        manager = weewx.manager.DaySummaryManager
        schema = weewx.schemas.additional.astro_schema
        savetoadditionalarchive = true

[DatabaseTypes]
    ...
    [[astro_sqlite]]
        database_name = astro.sdb
        database_type = SQLite

...

[Engine]
    [[Services]]
        ...
        archive_services = weewx.engine.StdArchive, user.savetoadditionalarchive.AdditionalArchive
        ...

```

The entry `savetoadditionalarchive = true` marks the bindings that are to
save by this extension. 

If the key is set to `false` or missing, this extension lets that binding
untouched.

## Usage

This extension creates the database(s) if they do not exist.

To use observation types from a separate database specify the data binding.
The following examples are based on the configuration example. You will
have other observation types depending on your use case.

* Tags:

  Example: `$day(data_binding='astro_binding').solarAltitude.maxtime`

* Plots:

  Example:
  ```
  [ImageGenerator]
      ...
      [[day_images]]
          ...
          [[[dayastro]]]
              data_binding = astro_binding
              [[[[solarAzimuth]]]]
              [[[[solarAltitude]]]]
  ```

  If you add this to `skin.conf` of the Seasons skin add `astro` at the
  end of the list at the key `plot_groups`, then you will see a diagram
  of the Sun's position in sky.

## Notes for developers

After the end of each archive cycle, WeeWX dispatches the
`weewx.NEW_ARCHIVE_RECORD` event. Services can bind a method to that event,
which is then called by WeeWX. The parameter of that method contains
the archive record and the accumulator. Both are in the same unit system. 
Which one it is, you find in the record in `usUnits`. The value applies to the
accumulator as well. 

If you want to convert the data to another unit system, you have to convert 
both the record and the accumulator. Or you extract whatever information you 
need from the accumulator and add it to the record first, and convert the 
record then.

`weewx.manager.Manager.addRecord` does *not* convert units. You have to
provide both the record and the accumulator in the correct target
unit system.

To my knowledge there is no function to convert an accumulator in WeeWX.
WeeWX provides a function to convert records only.

## Links

* [WeeWX](https://weewx.com)
* [WeeWX Skyfield almanac](https://github.com/roe-dl/weewx-skyfield-almanac)
* [Issue #1171](https://github.com/weewx/weewx/issues/1171)
