High-level Data
+++++++++++++++
All metadata starts with the :class:`~batdata.schemas.BatteryMetadata` object.

``BatteryMetadata``
~~~~~~~~~~~~~~~~~~~

**Source Object**: :class:`batdata.schemas.BatteryMetadata`


Representation for the metadata about a battery

The metadata captures the information about what experiment was run
on what battery. A complete set of metadata should be sufficient to
reproduce an experiment.


.. list-table::
   :header-rows: 1

   * - Column
     - Type
     - Description
   * - name
     - str
     - Name of the cell. Any format for the name is acceptable, as it is intended to be used by the battery data provider.
   * - comments
     - str
     - Long form comments describing the test
   * - version
     - str
     - (**Required**) Version of this metadata. Set by the battery-data-toolkit
   * - is_measurement
     - bool
     - (**Required**) Whether the data was created observationally as opposed to a computer simulation
   * - cycler
     - str
     - Name of the cycling machine
   * - start_date
     - date
     - Date the initial test on the cell began
   * - set_temperature
     - float
     - Set temperature for the battery testing equipment. Units: C
   * - schedule
     - str
     - Schedule file used for the cycling machine
   * - battery
     - BatteryDescription
     - Description of the battery being tested
   * - modeling
     - ModelMetadata
     - Description of simulation approach
   * - source
     - str
     - Organization who created this data
   * - dataset_name
     - str
     - Name of a larger dataset this data is associated with
   * - authors
     - typing.List[typing.Tuple[str, str]]
     - Name and affiliation of each of the authors of the data. First and last names
   * - associated_ids
     - typing.List[pydantic_core._pydantic_core.Url]
     - Any identifiers associated with this data file. Identifiers can be any URI, such as DOIs of associated paper or HTTP addresses of associated websites

Describing Batteries
++++++++++++++++++++
:class:`~batdata.schemas.battery.BatteryDescription` and its related class capture details about the structure of a battery.

``BatteryDescription``
~~~~~~~~~~~~~~~~~~~~~~

**Source Object**: :class:`batdata.schemas.battery.BatteryDescription`


Description of the entire battery

.. list-table::
   :header-rows: 1

   * - Column
     - Type
     - Description
   * - manufacturer
     - str
     - Manufacturer of the battery
   * - design
     - str
     - Name of the battery type, such as the battery product ID
   * - layer_count
     - int
     - Number of layers within the battery
   * - form_factor
     - str
     - The general shape of the battery
   * - mass
     - float
     - Mass of the entire battery. Units: kg
   * - dimensions
     - typing.List[float]
     - Dimensions of the battery in plain text.
   * - anode
     - ElectrodeDescription
     - Name of the anode material
   * - cathode
     - ElectrodeDescription
     - Name of the cathode material
   * - electrolyte
     - ElectrolyteDescription
     - Name of the electrolyte material
   * - nominal_capacity
     - float
     - Rated capacity of the battery. Units: A-hr

``ElectrodeDescription``
~~~~~~~~~~~~~~~~~~~~~~~~

**Source Object**: :class:`batdata.schemas.battery.ElectrodeDescription`


Description of an electrode

.. list-table::
   :header-rows: 1

   * - Column
     - Type
     - Description
   * - name
     - str
     - Short description of the electrolyte type
   * - supplier
     - str
     - Manufacturer of the material
   * - product
     - str
     - Name of the product. Unique to the supplier
   * - thickness
     - float
     - Thickness of the material (units: μm)
   * - area
     - float
     - Total area of the electrode (units: cm2)
   * - loading
     - float
     - Amount of active material per area (units: mg/cm^2)
   * - porosity
     - float
     - Relative volume of the electrode occupied by gas (units: %)

``ElectrolyteDescription``
~~~~~~~~~~~~~~~~~~~~~~~~~~

**Source Object**: :class:`batdata.schemas.battery.ElectrolyteDescription`


Description of the electrolyte

.. list-table::
   :header-rows: 1

   * - Column
     - Type
     - Description
   * - name
     - str
     - Short description of the electrolyte types
   * - additives
     - ElectrolyteAdditive
     - Any additives present in the electrolyte

``ElectrolyteAdditive``
~~~~~~~~~~~~~~~~~~~~~~~

**Source Object**: :class:`batdata.schemas.battery.ElectrolyteAdditive`


Additive to the electrolyte

.. list-table::
   :header-rows: 1

   * - Column
     - Type
     - Description
   * - name
     - str
     - Name of the additive
   * - amount
     - float
     - Amount added to the solution
   * - units
     - float
     - Units of the amount

Simulation Data
+++++++++++++++
:class:`~batdata.schemas.modeling.ModelMetadata` and its related class capture details about data produces using computational methods.

``ModelMetadata``
~~~~~~~~~~~~~~~~~

**Source Object**: :class:`batdata.schemas.modeling.ModelMetadata`


Describe the type and version of a computational tool used to generate battery data

.. list-table::
   :header-rows: 1

   * - Column
     - Type
     - Description
   * - name
     - str
     - Name of the software
   * - version
     - str
     - Version of the software if known
   * - type
     - ModelTypes
     - Type of the computational method it implements.
   * - references
     - typing.List[pydantic_core._pydantic_core.Url]
     - List of references associated with the software
   * - models
     - typing.List[str]
     - Type of mathematical model(s) being used in physics simulation.Use terms defined in BattINFO, such as "BatteryEquivalentCircuitModel".
   * - simulation_type
     - str
     - Type of simulation being performed. Use terms defined in BattINFO, such as "TightlyCoupledModelsSimulation"

