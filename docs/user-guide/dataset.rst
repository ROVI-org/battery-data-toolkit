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
#. :attr:`~battdat.data.BatteryDataset.tables`: A named collection of data tables as Pandas :class:`~pd.DataFrame`.
#. :attr:`~battdat.data.BatteryDataset.schemas`: Descriptions of the columns in each data table
   (see `Column Schema <schemas/column-schema.html>`_)

The types of tables held in each dataset depends on the type of battery.
Datasets describing a single cell may only include a single time series of the measurements,
whereas a dataset describing an entire system may have time series for each cell in each module
and those for multiple power conversion systems.

Access the data tables within the dataset by indexing the dataset:

.. code-block:: python

    dataset = BatteryDataset.from_hdf('example.h5')

    # These two ways for accessing a table are equivalent
    df = dataset['raw_data']
    df = dataset.tables['raw_data']
    df['voltage'].max()  # Compute the maximum voltage


Creating a ``BatteryDataset``
-----------------------------

Build a dataset by passing a collection of tables and their schemas along with the metadata to the constructor.
Once assembled, all component tables will be saved and loaded together.

.. code-block:: python

    from battdat.schemas import BatteryMetadata
    from battdat.schemas.column import RawData
    from battdat.data import BatteryDataset

    metadata = BatteryMetadata(name='2_cell_module')
    col_schema = RawData()  # Use the same schema for both tables
    dataset = BatteryDataset(
        data={'cell_1': cell1_df, 'cell_2': cell2_df},
        schemas={'cell_1': col_schema, 'cell_2': col_schema}
        metadata=metadata
    )

Check that your data and metadata agree using the :meth:`~battdat.data.BatteryDataset.validate` method.

.. code-block:: python

    dataset.validate()

The validate function will raise errors if the tables do not match the column schema
and will return names of columns without descriptions, if desired.

Dataset Templates
+++++++++++++++++

``battdat`` provides subclasses of :class:`~battdat.data.BatteryDataset` for different types of battery data.
Each subclass provides suggested names for certain types of data (e.g., ``raw_data`` for measurements
during operation of a single cell) and predefines schema to use for each column.
The current template classes are:

.. _type-table:

.. list-table::
   :header-rows: 1

   * - Class
     - Description
   * - :class:`~battdat.data.CellDataset`
     - Single battery cell with measurements of voltage, current, and other data at specific times
       or averaged over entire cycles. Tables (and their schemas) include:

       - ``raw_data`` (`RawData <schemas/column-schema.html#rawdata>`_): Measurements of system state at specific points in time.
       - ``cycle_stats`` (`CycleStats <schemas/column-schema.html#cyclestats>`_): Descriptive statistics about state over entire cycles.
       - ``eis_data`` (`EISData <schemas/column-schema.html#eisdata>`_): EIS measurements at different frequencies, over time.

Loading and Saving
------------------

The battery data and metadata can be saved in a few different styles, each with different advantages.

Functions to save are named ``to_[format]`` and
functions for loading data are named ``from_[format]``.

See the `formats <formats.html>`_ documentation page for more detail.

Loading functions loads the entire dataset. See `streaming <streaming.html>`_ for
how to load large datasets incrementally.
