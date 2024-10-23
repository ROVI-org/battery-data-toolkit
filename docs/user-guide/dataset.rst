The `BatteryDataset` Object
===========================

The `BatteryDataset` object is the central object for the battery data toolkit.
Extractors render vendor-specific data into the `BatteryDataset`,
schemas describe its contents,
and post-processing codes manipulate.

Using the `BatteryDataset` Object
---------------------------------

The `BatteryDataset` holds different types of data about a battery in separate Pandas dataframes,
and metadata describing the source of the data in a `.metadata` attribute.

.. note::

    TBD: Describe the types of data

Loading and Saving
------------------

The battery data and metadata can be saved in a few different styles, each with different advantages.

Functions to save are named ``to_batdata_[format]`` and
functions for loading data are named ``from_batdata_[format]``.

See the `formats <formats.html>`_ documentation page for more detail.

Loading functions loads the entire dataset. See `streaming <streaming.html>`_ for
how to load large datasets incrementally.
