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

''Source Metadata'' captures high-level information about a battery dataset
in the :class:`~batdata.schemas.BatteryMetadata` object.
Information included in ``BatteryMetadata``, in contrast to `Column Schemas`_, are relevant to
all measurements performed on a battery, such as:

1. The type of battery (e.g., NMC Li-ion, Pb acid)
2. The simulation code used, if the data is from a model
3. How the battery was cycled
4. The authors of the data and any related publications

:class:`~batdata.schemas.BatteryMetadata` objects have a hierarchical structure where
each record is composed of a single document that has fields which can correspond
to single values, collections of values, or entire sub-documents.

Create new metadata through the Python interface by first creating a ``BatteryMetadata`` object.

.. code-block:: python

    from batdata.schemas import BatteryMetadata

    metadata = BatteryMetadata(
        name='test-cell',
    )

Different types of information are grouped together into subdocuments,
such as details about the battery in :class:`~batdata.schemas.battery.BatteryDescription`

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

:class:`~batdata.schemas.BatteryMetadata` automatically validate inputs,
and can convert to and JSON formats. (`Pydantic <https://docs.pydantic.dev/latest/>`_!)

See the :mod:`batdata.schemas` for a full accounting of the available fields in our schema.

Source of Terminology
+++++++++++++++++++++

The `BattINFO ontology <https://big-map.github.io/BattINFO/index.html>`_ is the core source of terms.

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

.. note::
    The schema will be a continual work in progress.
    Consider adding `an Issue <https://github.com/ROVI-org/battery-data-toolkit/issues>`_ to the GitHub
    if you find you use a term enough it should be part of the schema.

Column Schemas
--------------

The contents of each data table available with a dataset are described using a :class:`~batdata.schemas.column.ColumnSchema`.
The schema is a collection of :class:`~batdata.schemas.column.ColumnInfo` objects detailing each column.

    >>> from batdata.schemas.eis import EISData
    >>> EISData().test_id.model_dump()
    {'required': True,
     'type': <DataType.INTEGER: 'integer'>,
     'description': 'Integer used to identify rows belonging to the same experiment.',
     'units': None,
     'monotonic': False}

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
