``RawData``
+++++++++++

**Source Object**: :class:`batdata.schemas.column.RawData`


Data describing measurements of a single cell

.. list-table::
   :header-rows: 1

   * - Column
     - Description
     - Units
   * - file_number
     - Which file a row came from, if the data was originally split into multiple files
     - None
   * - state
     - Whether the battery is being charged, discharged or otherwise.
     - None
   * - method
     - Method to control the charge or discharge
     - None
   * - cycle_number
     - Index of the testing cycle, starting at 0.
     - None
   * - step_index
     - Index of the step number within a testing cycle. A step change is defined by a change states between charging, discharging, or resting.
     - None
   * - substep_index
     - Change of the control method within a cycle.
     - None
   * - test_time
     - Time from the beginning of measurements
     - s
   * - voltage
     - Measured voltage of the system
     - V
   * - current
     - Measured current of the system. Positive current represents the battery discharging.
     - A
   * - internal_resistance
     - Internal resistance of the battery.
     - ohm
   * - time
     - Time as a UNIX timestamp.
     - s
   * - temperature
     - Temperature of the battery
     - C
   * - cycle_time
     - Time from the beginning of a cycle
     - s
   * - cycle_capacity
     - Cumulative change in amount of charge transferred from a battery since the start of a cycle. Positive values indicate the battery has discharged since the start of the cycle.
     - A-hr
   * - cycle_energy
     - Cumulative change in amount of energy transferred from a battery since the start of a cycle. Positive values indicate the battery has discharged since the start of the cycle.
     - J
   * - cycle_capacity_charge
     - Cycle capacity computed only during the 'charging' phase of a cycle
     - A-hr
   * - cycle_capacity_discharge
     - Cycle capacity computed only during the 'discharging' phase of a cycle
     - A-hr

``CycleLevelData``
++++++++++++++++++

**Source Object**: :class:`batdata.schemas.column.CycleLevelData`


Statistics about the performance of a cell over entire cycles

.. list-table::
   :header-rows: 1

   * - Column
     - Description
     - Units
   * - cycle_number
     - Index of the cycle
     - None
   * - cycle_start
     - Time since the first data point recorded for this battery for the start of this cycle
     - s
   * - cycle_duration
     - Duration of this cycle
     - s
   * - capacity_discharge
     - Total amount of electrons released during discharge
     - A-hr
   * - energy_discharge
     - Total amount of energy released during discharge
     - W-hr
   * - capacity_charge
     - Total amount of electrons stored during charge
     - A-hr
   * - energy_charge
     - Total amount of energy stored during charge
     - W-hr
   * - coulomb_efficiency
     - Fraction of electric charge that is lost during charge and recharge
     - %
   * - energy_efficiency
     - Amount of energy lost during charge and discharge
     - None
   * - discharge_V_average
     - Average voltage during discharging
     - V
   * - charge_V_average
     - Average voltage during charge
     - V
   * - V_maximum
     - Maximum voltage during cycle
     - V
   * - V_minimum
     - Minimum voltage during cycle
     - V
   * - discharge_I_average
     - Average current during discharge
     - A
   * - charge_I_average
     - Average current during charge
     - A
   * - temperature_minimum
     - Minimum observed battery temperature during cycle
     - C
   * - temperature_maximum
     - Maximum observed battery temperature during cycle
     - C
   * - temperature_average
     - Average observed battery temperature during cycle
     - C

``EISData``
+++++++++++

**Source Object**: :class:`batdata.schemas.eis.EISData`


Measurements for a specific EIS test

.. list-table::
   :header-rows: 1

   * - Column
     - Description
     - Units
   * - test_id
     - Integer used to identify rows belonging to the same experiment.
     - None
   * - test_time
     - Time from the beginning of measurements.
     - s
   * - time
     - Time as a UNIX timestamp. Assumed to be in UTC
     - None
   * - frequency
     - Applied frequency
     - Hz
   * - z_real
     - Real component of impedance
     - Ohm
   * - z_imag
     - Imaginary component of impedance
     - Ohm
   * - z_mag
     - Magnitude of impedance
     - Ohm
   * - z_phase
     - Phase angle of the impedance
     - Degree

