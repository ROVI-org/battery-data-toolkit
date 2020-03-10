# Battery Data Extractor 

This directory contains utilities for converting battery testing data files from native formats
to a standardized HDF5 file.

It also contains some scripts that run these utilities on datasets available to the ASOH project.

## Installation

You can install the toolkit with conda or pip as below. 

### Conda
`conda env create --file environment.yml --force`

### Pip
`pip install -r requirements.txt`

`pip install -e .`

## Project Organization

The `scripts` folder holds code that processes different datasets used by our collaboration. 

Any logic that is general enough to warrant re-use is moved into the `batdata` Python package.

The Python package also holds the schemas, which are described in 
[`schemas.py`](./batdata/schemas.py).
