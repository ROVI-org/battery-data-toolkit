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

The internal structure of each group (e.g., ``f['raw_data']``) are that of
the `PyTables Table format <https://www.pytables.org/usersguide/file_format.html#table-format>`_:
a one-dimensional chunked array with a compound data type.

.. dropdown:: HDF5 content

    .. code-block::

        $ h5ls -rv single-resistor-complex-charge_from-discharged.hdf
        Opened ".\single-resistor-complex-charge_from-discharged.hdf" with sec2 driver.
        /                        Group
            Attribute: CLASS scalar
                Type:      5-byte null-terminated UTF-8 string
            Attribute: PYTABLES_FORMAT_VERSION scalar
                Type:      3-byte null-terminated UTF-8 string
            Attribute: TITLE null
                Type:      1-byte null-terminated UTF-8 string
            Attribute: VERSION scalar
                Type:      3-byte null-terminated UTF-8 string
            Attribute: battdat_version scalar
                Type:      5-byte null-terminated UTF-8 string
            Attribute: json_schema scalar
                Type:      8816-byte null-terminated ASCII string
            Attribute: metadata scalar
                Type:      242-byte null-terminated UTF-8 string
            Location:  1:96
            Links:     1
        /raw_data                Dataset {3701/Inf}
            Attribute: CLASS scalar
                Type:      5-byte null-terminated UTF-8 string
            Attribute: FIELD_0_FILL scalar
                Type:      native double
            Attribute: FIELD_0_NAME scalar
                Type:      9-byte null-terminated UTF-8 string
            Attribute: FIELD_1_FILL scalar
                Type:      native double
            Attribute: FIELD_1_NAME scalar
                Type:      7-byte null-terminated UTF-8 string
            Attribute: FIELD_2_FILL scalar
                Type:      native double
            Attribute: FIELD_2_NAME scalar
                Type:      7-byte null-terminated UTF-8 string
            Attribute: FIELD_3_FILL scalar
                Type:      native long long
            Attribute: FIELD_3_NAME scalar
                Type:      12-byte null-terminated UTF-8 string
            Attribute: NROWS scalar
                Type:      native long long
            Attribute: TITLE null
                Type:      1-byte null-terminated UTF-8 string
            Attribute: VERSION scalar
                Type:      3-byte null-terminated UTF-8 string
            Attribute: json_schema scalar
                Type:      2824-byte null-terminated UTF-8 string
            Attribute: metadata scalar
                Type:      2824-byte null-terminated UTF-8 string
            Location:  1:10240
            Links:     1
            Chunks:    {2048} 65536 bytes
            Storage:   118432 logical bytes, 6670 allocated bytes, 1775.59% utilization
            Filter-0:  shuffle-2 OPT {32}
            Filter-1:  deflate-1 OPT {9}
            Type:      struct {
                           "test_time"        +0    native double
                           "current"          +8    native double
                           "voltage"          +16   native double
                           "cycle_number"     +24   native long long
                       } 32 bytes

Multiple Batteries per File
+++++++++++++++++++++++++++

Data from multiple batteries can share a single HDF5 file as long as they share the same metadata.

Add multiple batteries into an HDF5 file by providing a "prefix" to name each cell.

.. code-block:: python

    test_a.to_battdat_hdf('test.h5', prefix='a')
    test_b.to_battdat_hdf('test.h5', prefix='b', overwrite=False)  # Overwrite is mandatory


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
of each file.

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
