# Battery Data Extractor 

This directory contains utilities for converting battery testing data files from native formats
to a standardized HDF5 file.

It also contains some scripts that run these utilities on datasets available to the ASOH project.

## Installation

Install the environment needed with `conda env create --file environment.yml --force`.

## Project Organization

The `scripts` folder holds code that processes different datasets used by our collaboration. 

Any logic that is general enough to warrant re-use is moved into the `batdata` Python package.

The Python package also holds the schemas, which are described in 
[`schemas.py`](./batdata/schemas.py).
