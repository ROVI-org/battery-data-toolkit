Reading and Writing Datasets
============================

The :mod:`battdat.io` module provides tools to read and write from :class:`~battdat.data.BatteryDataset` objects.

.. list-table::
   :align: center
   :header-rows: 1

   * - Format
     - Module
     - Reading
     - Writing
   * - Arbin
     - :mod:`~battdat.io.arbin`
     - ✔️
     - ✖️
   * - Battery Archive (https://www.batteryarchive.org)
     - :mod:`~battdat.io.ba`
     - ✖️
     - ✔️
   * - Battery Data Hub (https://batterydata.energy.gov)
     - :mod:`~battdat.io.batterydata`
     - ✔️
     - ✖️
   * - `HDF5 <formats.html#hdf5>`_
     - :mod:`~battdat.io.hdf`
     - ✔️
     - ✔️
   * - MACCOR
     - :mod:`~battdat.io.maccor`
     - ✔️
     - ✖️
   * - `Parquet <formats.html#parquet>`_
     - :mod:`~battdat.io.parquet`
     - ✔️
     - ✔️


.. note::

    The parquet and HDF5 formats write to the `battery-data-toolkit file formats <formats.html>`_.

Reading Data
------------

:class:`~battdat.io.base.DatasetReader` classes provide the ability to create a dataset
through the :class:`~battdat.io.base.DatasetReader.read_dataset` method.
The inputs to ``read_dataset`` always include a :class:`~battdat.schemas.BatteryMetadata` object
containing information beyond what is available in the files.

Most :class:`~battdat.io.base.DatasetReader` read data from a filesystem and are based on :class:`~battdat.io.base.DatasetFileReader`.
These readers take list of paths to data files alongside the metadata and also include methods (e.g., :meth:`~battdat.io.base.DatasetFileReader.group`) to
find files:

.. code-block:: python

    from battdat.io.batterydata import BDReader

    extractor = BDReader(store_all=True)
    group = next(extractor.identify_files('./example-path/'))
    dataset = extractor.read_dataset(group)

Writing Data
------------

:class:`~battdat.io.base.DatasetWriter` classes write :class:`battdat.data.BatteryDataset` objects into forms usable by other tools.

For example, the :class:`~battdat.io.ba.BatteryArchiveWriter` converts the metadata into the schema used by `Battery Archive <https://www.batteryarchive.org>`_
and writes the data into the preferred format: CSV files no longer than 100k rows.


.. code-block:: python

    from battdat.io.ba import BatteryArchiveWriter
    exporter = BatteryArchiveWriter()
    exporter.export(example_data, './to-upload')
