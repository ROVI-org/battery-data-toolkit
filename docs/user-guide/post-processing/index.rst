Post-Processing
===============

Most sources of battery data provide the voltage and current over time,
but the other properties which are derived from them may be missing.
The battery data toolkit provides "post-processing" classes which
add compute these derived data sources.

All post-processing tools are based on the :class:`~battdat.postprocess.base.BaseFeatureComputer` class
and, as a result, provide a :meth:`~battdat.postprocess.base.BaseFeatureComputer.compute_features` function that adds
new information to a battery dataset.
Use them by first creating the tool and invoking that method with
a :class:`~battdat.data.BatteryDataset`:

.. code-block:: python

    computer = FeatureComputer()
    new_columns = computer.compute_features(data)

New columns will be added to a part of the dataset (e.g., the cycle-level statistics) and those new columns
will be returned from the function.

The feature computers fall into two categories:

- :class:`~battdat.postprocess.base.RawDataEnhancer`, which add information to the raw data as a function of time
- :class:`~battdat.postprocess.base.CycleSummarizer`, which summarize the raw data and add new columns to the ``cycle_stats``


.. note::

    Post-processing is only supported for :class:`battdat.data.CellDataset` for now.

Integral Quantities
-------------------

Functions which add columns associated with the accumulated values of data in other columns.

.. toctree::
    :maxdepth: 1

    cell-capacity


Time
----

Compute columns which are derived fields associated with the relative time or timespans of data.

.. toctree::
    :maxdepth: 1

    cycle-times
