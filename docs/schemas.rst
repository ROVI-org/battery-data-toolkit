Battery Data Schemas
====================

The metadata schemas used by ```batdata``` standardize how we describe the source of battery datasets.
Metadata are held as part of the ``BatteryDataset`` object and saved within the file formats
produced by ``batdata`` to ensure that the provenance of a dataset is kept alongside the actual data.


Understanding the Metadata
--------------------------

The metadata we employ in ``batdata`` follows the style of the JSON or XML data structures which are ubiquitous
in scientific computation and data infrastructure.

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


See the `schemas <https://github.com/ROVI-org/battery-data-toolkit/tree/main/batdata/schemas>`_
for a full accounting of the available fields in our schema.

.. note:: TODO: Render the schemas into an easier-to-read format

Feel free to add fields to any part of the schema.
The schema is a continual work in progress and the battery-data-toolkit will 
store your new fields.
Consider adding `an Issue <https://github.com/ROVI-org/battery-data-toolkit/issues>`_ to our GitHub
if you find you use a term enough that we should add it to the schema.

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


.. note:: TODO: Render the options in web-hosted documentation as well

Column Datasets
---------------

The columns of datasets are described in the `cycling module <https://github.com/ROVI-org/battery-data-toolkit/blob/main/batdata/schemas/cycling.py>`_.

Use the descriptions here when formatting your dataset, playing attention to the sign conventions and units for each column.

Record columns that are not defined in our schema in the ``*_columns`` fields
of the ``BatteryMetadata``.

.. code-block:: python

    from batdata.schemas import BatteryMetadata

    metadata = BatteryMetadata(
        name='test_cell',
        raw_data_columns={'new_signal': 'A column not yet defined in our schemas.'}
    )


.. include:: column-schema.rst
