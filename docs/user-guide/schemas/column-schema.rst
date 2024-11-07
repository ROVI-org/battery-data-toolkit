Column Schemas
==============

The contents of each data table available with a dataset are described using a :class:`~batdata.schemas.column.ColumnSchema`.
The schema is a collection of :class:`~batdata.schemas.column.ColumnInfo` objects detailing each column,
which includes

1. **Description**: A English description of the contents
2. **Type**: Type of each record (e.g., integer, string)
3. **Units**: Units for the values, if applicable
4. **Required**: Whether the column *must* be present in the table
5. **Monotonic**: Whether values in never decrease between sequential rows

Using a Column Schema
---------------------

:class:`~batdata.schemas.column.ColumnSchema` stored inside the `HDF5 and Parquet files <../formats.html>`_
provided by the battery data toolkit are used to describe existing and validating new data.

List the columns names with :attr:`~batdata.schemas.column.ColumnSchema.columns` attribute
and access information for a single column through the get item method:

.. code-block:: python

    data = BatteryDataset.from_batdata_hdf(out_path)
    schema = data.schemas['eis_data']  # ColumnSchema for the ``eis_data`` table
    print(schema['test_id'].model_dump())

The above code prints the data for a specific column.

.. code-block:: python

    {'required': True,
     'type': <DataType.INTEGER: 'integer'>,
     'description': 'Integer used to identify rows belonging to the same experiment.',
     'units': None,
     'monotonic': False}


Use the :meth:`~batdata.schemas.column.ColumnSchema.validate_dataframe` to check
if a dataframe matches requirements for each column.

Pre-defined Schema
------------------

The battery-data-toolkit provides schemas for common types of data (e.g., cycling data for single cells, EIS).

.. include:: rendered-column-schema.rst

Defining a New Column Schema
----------------------------

Document a new type of data by either creating a subclass of :class:`~batdata.schemas.column.ColumnSchema`
or adding individual columns to an existing schema.

.. code-block:: python

    from batdata.schemas.column import RawData, ColumnInfo

    schema = RawData()  # Schema for sensor measurements of cell
    schema.extra_columns['room_temp'] = ColumnInfo(
        description='Temperature of the room as measured by the HVAC system',
        units='C', data_type='float',
    )
