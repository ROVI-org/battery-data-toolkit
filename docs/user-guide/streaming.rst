Streaming Battery Data
======================

Many battery datasets are too large to fit in memory in a single computer at once.
Such data can be read or written incrementally using the streaming module of battery data toolkit,
:class:`battdat.streaming`.

Reading Data as a Stream
------------------------

The battery-data-toolkit allows streaming the raw time series data from an :ref:`HDF5 file format <hdf5>`.

Stream the data either as individual rows or all rows belonging to each cycle
with the :meth:`~battdat.streaming.iterate_records_from_file`
or :meth:`~battdat.streaming.iterate_cycles_from_file`.

Both functions produce `a Python generator <https://docs.python.org/3/glossary.html#term-generator>`_
which retrieves a chunk of data from the HDF5 file incrementally and can be used to produce data individually

.. code-block:: python

    row_iter = iterate_records_from_file('example.h5')
    row = next(row_iter)
    do_something_per_timestep(row)

or as part of a for loop.

.. code-block:: python

    for cycle in iterate_cycles_from_file('example.h5'):
        do_something_per_cycle(cycle)

Reading full cycles by file can produce either a single :class:`~pandas.DataFrame` when reading a single table,
a dictionary of ``DataFrames``, or a full :class:`~battdat.data.BatteryDataset` depending on the
options for ``key`` and ``make_dataset``.

.. code-block:: python

    # Read as a single DataFrame
    df = next(iterate_cycles_from_file('example.h5', key='raw_data'))

    # Read multiple tables as a dictionary
    dict_of_df = next(iterate_cycles_from_file('example.h5', key=['raw_data', 'cycle_stats']))

    # Read all tables as a Dataset
    dataset = next(iterate_cycles_from_file('example.h5', key=None, make_dataset=True))


Streaming Data to a File
------------------------

Write large datasets into battery-data-toolkit-compatible formats incrementally using the :class:`~battdat.streaming.hdf5.HDF5Writer`.

Start the writer class by providing the path to the HDF5 file and the metadata to be written
then opening it via Python's ``with`` syntax.

.. code-block:: python

    metadata = BatteryMetadata(name='example')
    with HDF5Writer('streamed.h5', metadata=metadata) as writer:
        for time, current, voltage in data_stream:
            writer.write_row({'test_time': time, 'current': current, 'voltage': voltage})

The writer only writes to disk after enough rows are collected or the end of a data stream is signaled by exiting the ``with`` block.
