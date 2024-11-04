Describing Battery Data
=======================

The metadata schemas used by ``batdata`` standardize how we describe the source of battery datasets
and annotate what the data are.
Metadata are held as part of the :class:`batdata.data.BatteryDataset` object and saved within the file formats
produced by ``batdata`` to ensure that the provenance of a dataset is kept alongside the actual data.

Descriptions are defined in two parts:

.. contents::
   :local:
   :depth: 2

Source Metadata
---------------

The metadata we employ in ``batdata`` follows the style of the JSON or XML data structures which are ubiquitous
in scientific computation and data infrastructure.
Each record is composed of a single document that has a hierarchical set of fields which can correspond
to single values or collections of values.

We recommend creating the metadata for a battery through the Python interface. 
Start by creating a ``BatteryMetadata`` object. There are no required fields, but you should always give your data a name.

.. code-block:: python

    from batdata.schemas import BatteryMetadata

    metadata = BatteryMetadata(
        name='test-cell',
    )

The metadata is a nested document where different types of information are grouped together into sub objects.
For example, the details about the battery being tested are in `BatteryDescription`

.. code-block:: python

    from batdata.schemas.battery import BatteryDescription
    from batdata.schemas import BatteryMetadata

    metadata = BatteryMetadata(
        name='test-cell',
        battery=BatteryDescription(
            manufacturer='famous',
            nominal_capacity=1.,
        )
    )

Components
++++++++++

We use a component-based approach for the metadata about a dataset.

See the `schemas <https://github.com/ROVI-org/battery-data-toolkit/tree/main/batdata/schemas>`_
for a full accounting of the available fields in our schema.

.. include:: metadata-schema.rst

Source of Terminology
+++++++++++++++++++++

We use terms from `BattINFO ontology <https://big-map.github.io/BattINFO/index.html>`_ wherever possible.

Fields in the schema whose names correspond to a BattINFO term are marked
with the "IRI" of the field, which points to a website containing the description.

Fields whose values should be terms from the BattINFO ontology are marked with the root of the terms.
For example, the ``model_type`` field of `ModelMetadata` can be any type of
`MathematicalModel <https://emmo-repo.github.io/emmo.html#EMMO_f7ed665b_c2e1_42bc_889b_6b42ed3a36f0>`_.
Look them up using some utilities in ``batdata``.

.. code-block:: python

    from batdata.schemas.ontology import gather_descendants

    print(gather_descendants('MathematicalModel'))


Feel free to add fields to any part of the schema.
The schema is a continual work in progress and the battery-data-toolkit will
store your new fields.
Consider adding `an Issue <https://github.com/ROVI-org/battery-data-toolkit/issues>`_ to our GitHub
if you find you use a term enough that we should add it to the schema.

Column Schemas
--------------

The :attr:`~batdata.data.BatteryDataset.schemas` attribute of a dataset holds
a description of each column of each constituent table.
Each schema is a :class:`~batdata.schemas.column.ColumnSchema`,
which provides access to descriptions of each column as :class:`~batdata.schemas.column.ColumnInfo` objects.

    >>> from batdata.schemas.eis import EISData
    >>> EISData().test_id.model_dump()
    {'required': True,
     'type': <DataType.INTEGER: 'integer'>,
     'description': 'Integer used to identify rows belonging to the same experiment.',
     'units': None,
     'monotonic': False}

These column descriptions will be written when saving your data.

As detailed below, the battery-data-toolkit provides schemas for common types of data (e.g., cycling data for single cells, EIS).
Document a new type of data by either creating a subclass of :class:`~batdata.schemas.column.ColumnSchema`
or adding individual columns to an existing schema.

.. code-block:: python

    from batdata.schemas.column import RawData, ColumnInfo

    schema = RawData()  # Schema for sensor measurements of cell
    schema.extra_columns['room_temp'] = ColumnInfo(
        description='Temperature of the room as measured by the HVAC system',
        units='C', data_type='float',
    )

.. include:: column-schema.rst
