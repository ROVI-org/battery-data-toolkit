Battery Data Toolkit
====================

The battery-data-toolkit, ``battdat``, creates consistently-formatted collections of battery data.
The library has three main purposes:

1. *Storing battery data in standardized formats.* ``battdat`` stores data in
   `high-performance file formats <./user-guide/formats.html>`_ and include
   `extensive metadata <./user-guide/schemas/index.html>`_ alongside data.
2. *Interfacing battery data with the PyData ecosystem*. The core data model,
   `BatteryDataset <./user-guide/dataset.html>`_,
   is built atop Pandas DataFrames.
3. *Providing standard implementations of common analysis techniques*. ``battdat`` implements functions which
   `ensure quality <./user-guide/consistency/index.html>`_
   or `perform common analyses <./user-guide/post-processing/index.html>`_.

Source code: https://github.com/ROVI-org/battery-data-toolkit

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   getting-started
   user-guide/index
   source/modules
