Exporting Data to Other Tools
=============================

The `batdata.exporters` modules provides tools for writing the data from battery-data-toolkit's internal format
into files suitable for use in other tools.

All exporter interfaces provide a `export` function which takes the dataset to be written
and a path to the directory in which to store the files.
The exporter objects themselves take arguments which control how all dataset
being exported are written, such as the number of rows per file.

.. code-block:: python

    from batdata.exporters.ba import BatteryArchiveExporter

    exporter = BatteryArchiveExporter(chunk_size=1000000)
    exporter.export(dataset, 'output_dir')

.. note:: We assume each dataset will be stored in its own directory, but that's not a decision we won't revisit.

BatteryArchive
--------------

The `BatteryArchive <https://batteryarchive.org/>`_ project stores battery data in an SQL database.
Our exporter does not connect to this database and, instead, writes each battery dataset into 
files with column names that match
`BatteryArchive's SQL schema <https://github.com/battery-lcf/batteryarchive-agent/blob/main/data/ba_data_schema.sql>`_
so that adding them to the archive is simple.

.. note:: Write how we convert metadata