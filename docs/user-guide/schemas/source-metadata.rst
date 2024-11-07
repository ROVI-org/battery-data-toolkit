Source Metadata
===============

''Source Metadata'' captures high-level information about a battery dataset
in the :class:`~batdata.schemas.BatteryMetadata` object.
Information included in ``BatteryMetadata``, in contrast to `Column Schemas <column-schema.html>`_, are relevant to
all measurements performed on a battery, such as:

1. The type of battery (e.g., NMC Li-ion, Pb acid)
2. The simulation code used, if the data is from a model
3. How the battery was cycled
4. The authors of the data and any related publications

Metadata Structure
------------------

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

.. note::

    Validation only checks that already-defined fields are specified properly.
    Add metadata beyond what is described in battery-data-toolkit as desired.

Source of Terminology
---------------------

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


.. note::
    The schema will be a continual work in progress.
    Consider adding `an Issue <https://github.com/ROVI-org/battery-data-toolkit/issues>`_ to the GitHub
    if you find you use a term enough it should be part of the schema.

Metadata Objects
----------------

The battery-data-toolkit expresses the metadata schema using `Pydantic BaseModel objects <https://docs.pydantic.dev/latest/>`_.

.. include:: rendered-metadata-schema.rst