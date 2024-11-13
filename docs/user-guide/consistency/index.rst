Consistency Checks
==================

Many problems, such as sign convention mishaps or unit conversion issues, can be detected from inconsistencies between
or within columns in a dataset.
The :mod:`battdat.consistency` module provides algorithms that check whether there may be problems within a battery dataset.

All algorithms are based on :class:`~battdat.consistency.base.ConsistencyChecker`,
which creates a list of warnings given a dataset.

.. code-block:: python

    computer = ConsistencyChecker()
    warnings = computer.check(data)

    if len(warnings) > 0:
        print(f'There are {len(warnings)} warnings, which includes: {warnings[0]}')


.. toctree::
    :maxdepth: 1
    :caption: Available consistency checks:

    check-sign-convention

