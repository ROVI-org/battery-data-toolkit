Streaming Battery Data
======================

Many battery datasets are too large to fit in memory in a single computer at once.
Such data can be read or written incrementally using the streaming module of battery data toolkit,
:class:`batdata.streaming`.

Reading Data as a Stream
------------------------

The battery-data-toolkit allows streaming the raw time series data from an :ref:`HDF5 file format <hdf5>`.

Stream the data either as individual rows or all rows belonging to each cycle
with the :meth:`~batdata.streaming.iterate_records_from_file`
or :meth:`~batdata.streaming.iterate_cycles_from_file`.

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


Streaming Data to a File
------------------------

Write large datasets into battery-data-toolkit-compatible formats incrementally using the :class:`~batdata.streaming.hdf5.HDF5Writer`.

Start the writer class by providing the path to the HDF5 file and the metadata to be written
then opening it via Python's ``with`` syntax.

.. code-block:: python

    metadata = BatteryMetadata(name='example')
    with HDF5Writer('streamed.h5', metadata=metadata) as writer:
        for time, current, voltage in data_stream:
            writer.write_row({'test_time': time, 'current': current, 'voltage': voltage})

The writer only writes to disk after enough rows are collected or the end of a data stream is signaled by exiting the ``with`` block.
