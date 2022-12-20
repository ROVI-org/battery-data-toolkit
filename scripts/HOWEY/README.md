# Howey ingestor scripts 

[Dataset source](https://doi.org/10.1016/j.joule.2021.11.006)

This directory contains two scripts for ingesting the Howey dataset and converting to the HDF5 file format.

There is one serial version, and another that employs multiprocessing to parallelize within a node. Change the number of processors to an appropriate number for the node (e.g. 1/2 the number of cores available).
