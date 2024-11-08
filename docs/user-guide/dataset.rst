The `BatteryDataset` Object
===========================

The :class:`~battdat.data.BatteryDataset` object is the central object for the battery data toolkit.
Extractors render vendor-specific data into the `BatteryDataset`,
schemas describe its contents,
and post-processing codes manipulate its datasets.


Structure of a ``BatteryDataset``
---------------------------------

The :class:`~battdat.data.BatteryDataset` holds all information about a battery system together in the same Python object.
Every dataset holds three attributes:

#. :attr:`~battdat.data.BatteryDataset.metadata`: Information describing the source of the data
   (see `Source Metadata <schemas/source-metadata.html>`_)
#. :attr:`~battdat.data.BatteryDataset.datasets`: A named collection of data tables
#. :attr:`~battdat.data.BatteryDataset.schemas`: Descriptions of the columns in each data table
   (see `Column Schema <schemas/column-schema.html>`_)

The types of tables held in each dataset depends on the type of battery.
Datasets describing a single cell may only include a single time series of the measurements,
whereas a dataset describing an entire system may have time series for each cell in each module
and those for multiple power conversion systems.

``battdat`` provides subclasses of :class:`~battdat.data.BatteryDataset` for different types of battery data.
Each subclass provides suggested names for certain types of data (e.g., ``raw_data`` for measurements
during operation of a single cell).
The current template classes are:

.. list-table::
   :header-rows: 1

   * - Class
     - Use Case
   * - :class:`~battdat.data.CellDataset`
     - Single battery cell with measurements of voltage, current, and other data at specific times
       or averaged over entire cycles.

Loading and Saving
------------------

The battery data and metadata can be saved in a few different styles, each with different advantages.

Functions to save are named ``to_[format]`` and
functions for loading data are named ``from_[format]``.

See the `formats <formats.html>`_ documentation page for more detail.

Loading functions loads the entire dataset. See `streaming <streaming.html>`_ for
how to load large datasets incrementally.
