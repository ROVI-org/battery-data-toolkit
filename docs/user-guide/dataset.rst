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
#. :attr:`~battdat.data.BatteryDataset.tables`: A named collection of data tables as Pandas :class:`~pandas.DataFrame`.
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

Load data from another file format using battdat's `dataset readers <io.html>`_.
If there is no available reader,
build by passing a collection of tables as :class:`~pandas.DataFrame` and their schemas along with the metadata to the constructor.
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

Columns of the dataframes can be any `NumPy data type <https://numpy.org/doc/stable/reference/generated/numpy.dtype.kind.html#numpy.dtype.kind>`_
except timedeltas (m), timestamps (M), or voids (v).
Battery data toolkit does not yet support storing these types in HDF5 or Parquet formats.
Columns where all values are arrays of the same size are also supported.

Check that your data and metadata agree using the :meth:`~battdat.data.BatteryDataset.validate` method.

.. code-block:: python

    dataset.validate()

The validate function will raise errors if the tables do not match the column schema
and will return names of columns without descriptions, if desired.

Factory Methods
+++++++++++++++

:class:`~battdat.data.BatteryDataset` contains factory methods that build datasets from
tables with pre-defined names and tables.
All are named ``make_*_dataset``.

For example, :meth:`~battdat.data.BatteryDataset.make_cell_dataset` creates a dataset
which represents a single-cell battery.

.. code-block:: python

    from battdat.data import BatteryDataset

    dataset = BatteryDataset.make_cell_data(raw_data=df)

Each table will be associated with a default schema.
Describe columns not yet present in the schema by adding them after assembly:

.. code-block:: python

    from battdat.schemas.columns import ColumnInfo
    dataset.schemas['raw_data'].add_column(
        name='new_col',
        description='Information not already included in RawData',
        units='ohm',
    )

The current factory methods are:

.. _type-table:

.. list-table::
   :header-rows: 1

   * - Method
     - Description
   * - :class:`~battdat.data.BatteryDataset.make_cell_dataset`
     - Single battery cell with measurements of voltage, current, and other data at specific times
       or averaged over entire cycles. Tables (and their schemas) include:

       - ``raw_data`` (`RawData <schemas/column-schema.html#rawdata>`_): Measurements of system state at specific points in time.
       - ``cycle_stats`` (`CycleLevelData <schemas/column-schema.html#cycleleveldata>`_): Descriptive statistics about state over entire cycles.
       - ``eis_data`` (`EISData <schemas/column-schema.html#eisdata>`_): EIS measurements at different frequencies, over time.

Loading and Saving
------------------

The battery data and metadata can be saved in a few different styles, each with different advantages.

Functions to save are named ``to_[format]`` and
functions for loading data are named ``from_[format]``.

See the `formats <formats.html>`_ documentation page for more detail.

Loading functions loads the entire dataset. See `streaming <streaming.html>`_ for
how to load large datasets incrementally.
