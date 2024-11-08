The `BatteryDataset` Object
===========================

The :class:`~battdat.data.BatteryDataset` object is the central object for the battery data toolkit.
Extractors render vendor-specific data into the `BatteryDataset`,
schemas describe its contents,
and post-processing codes manipulate its datasets.

Creating a Battery Dataset
--------------------------



Using the `BatteryDataset` Object
---------------------------------

The :class:`~battdat.data.BatteryDataset` holds different types of data about a battery in separate Pandas dataframes,
metadata describing the source of the data as the :attr:`~battdat.data.BatteryDataset.metadata` attribute,
and schema describing each dataframe in the :class:`~battdat.data.BatteryDataset.schemas` attribute.

All datasets

Loading and Saving
------------------

The battery data and metadata can be saved in a few different styles, each with different advantages.

Functions to save are named ``to_battdat_[format]`` and
functions for loading data are named ``from_battdat_[format]``.

See the `formats <formats.html>`_ documentation page for more detail.

Loading functions loads the entire dataset. See `streaming <streaming.html>`_ for
how to load large datasets incrementally.
