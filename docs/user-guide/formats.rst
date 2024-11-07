File Formats
============

The battery data toolkit stores data and metadata in two formats:

- *HDF5*: A format for saving all available information about a battery into a single file
- *Parquet*: A format optimized for storing column data, but requires saving separate files for each type of data (cycle vs raw)

.. contents::
  :local:
  :depth: 1

.. _hdf5:

HDF5
----

The `HDF5 format <https://support.hdfgroup.org/documentation/hdf5/latest/>`_ stores array data as a nested series of dictionaries.
``battdat`` stores each type of data known about a battery in separate groups
and the metadata for the battery as the metadata.

.. code-block:: python

    import h5py
    import json

    with h5py.File('example.h5') as f:
        metadata = json.loads(f.attrs['metadata'])  # Data describing the cell and how it was tested
        raw_data = f['raw_data']  # HDF5 group holding raw data
        schema = raw_data.attrs['metadata']  # Description of each column

The internal structure of each group (e.g., ``f['raw_data']``) are in `the PyTables layout <https://www.pytables.org/usersguide/file_format.html>`_.
The format is readable through pytables and Pandas's :func:`~pandas.read_hdf` function, but readers for other languages do not yet exist.

.. note::

    We may change to a simplified HDF5 layout for simpler cross-language compatibility.


Multiple Batteries per File
+++++++++++++++++++++++++++

Data from multiple batteries can share a single HDF5 file as long as they share the same metadata.

Add multiple batteries into an HDF5 file by providing a "prefix" to name each cell.

.. code-block:: python

    test_a.to_battdat_hdf('test.h5', prefix='a')
    test_b.to_battdat_hdf('test.h5', prefix='b', append=True)  # Append is mandatory


Load a specific cell by providing a specific prefix on load

.. code-block:: python

    test_a = BatteryDataset.from_battdat_hdf('test.h5', prefix='a')


or load any of the included cells by providing an index

.. code-block:: python

    test_a = BatteryDataset.from_battdat_hdf('test.h5', prefix=0)

Load all cells by iterating over them:

.. code-block:: python

    for name, cell in BatteryDataset.all_cells_from_battdat_hdf('test.h5'):
        do_some_processing(cell)

Parquet
-------

The `Apache Parquet format <https://en.wikipedia.org/wiki/Apache_Parquet>`_ is designed for high performance I/O of tabular data.
``battdat`` stores each type of data in a separate file and the metadata in `file-level metadata <https://parquet.apache.org/docs/file-format/metadata/>`_
of the file.

.. code-block:: python

    from pyarrow import parquet as pq
    import json

    # Reading the metadata
    file_metadata = pq.read_metadata('raw_data.parquet')  # Parquet metadata
    metadata = json.loads(file_metadata.metadata[b'battery_metadata'])  # For the battery
    schema = json.loads(file_metadata.metadata[b'table_metadata'])  # For the columns

    # Reading the data
    table = pq.read_table('raw_data.parquet')  # In pyarrow's native Table format
    df = table.to_pandas()  # As a dataframe

The internal structure of a Parquet file saved by ``battdat`` has column names and data types which match those provided when saving the file.
Any numeric types will be the same format (e.g., ``float32`` vs ``float64``)
and times are stored as floating point numbers, rather than Parquet's time format.
