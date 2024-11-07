Describing Battery Data
=======================

The metadata schemas used by ``batdata`` standardize how we describe the source of battery datasets
and annotate what the data are.
Metadata are held as part of the :class:`batdata.data.BatteryDataset` object and saved within the file formats
produced by ``batdata`` to ensure that the provenance of a dataset is kept alongside the actual data.

Descriptions are defined in two parts:

1. **Source Metadata**: Information about a battery dataset applicable to all measurements.
2. **Column Schemas**: Details about a specific table of measurements.

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   source-metadata
   column-schema
