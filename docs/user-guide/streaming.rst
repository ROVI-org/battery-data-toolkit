Streaming Battery Data
======================

Many battery datasets are too large to fit in memory in a single computer at once.
Such data can be read or written incrementally using the streaming module of battery data toolkit,
:class:`batdata.streaming`.

Reading Data as a Stream
------------------------

The battery-data-toolkit allows streaming the raw time series data from an :ref:`HDF5 file format <hdf5>`.

Stream the data either as individual rows or as groups of cycles
with the :meth:`~batdata.streaming.iterate_records_from_file`
or :meth:`~batdata.streaming.iterate_cycles_from_file`.

Both functions produce `a Python generator <https://docs.python.org/3/glossary.html#term-generator>`_
which retrieves a chunk of data from the HDF5 file and can be used to produce data individually

.. code-block:: python

    row_iter = iterate_records_from_file('example.h5')
    row = next(row_iter)

or as part of a for loop.

.. code-block:: python

    for row in iterate_records_file_file('example.h5'):
        do_something_per_timestep(row)

Streaming Data to a File
------------------------

TBD! Writing incrementally is not yet supported, but a feature on our road map.
