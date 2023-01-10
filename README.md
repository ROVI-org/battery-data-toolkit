# Battery Data Toolkit

[![Python Package](https://github.com/materials-data-facility/battery-data-toolkit/actions/workflows/python-package.yml/badge.svg)](https://github.com/materials-data-facility/battery-data-toolkit/actions/workflows/python-package.yml)
[![Coverage Status](https://coveralls.io/repos/github/materials-data-facility/battery-data-toolkit/badge.svg?branch=add-coverage)](https://coveralls.io/github/materials-data-facility/battery-data-toolkit?branch=master)
[![PyPI version](https://badge.fury.io/py/battery-data-toolkit.svg)](https://badge.fury.io/py/battery-data-toolkit)

The battery-data-toolkit, `batdata`, converts battery testing data from native formats to a standardized HDF5 file.
These HDF5 files contain the metadata needed to understand the source of the data, 
and can be easily manipulated by common analysis libraries (e.g., Pandas).

This repository also contains [example scripts](./scripts) for converting datasets to the HDF5 format.

## Installation

The package can be installed with pip: `pip install battery-data-toolkit`

## Project Organization

The `scripts` folder holds code that processes different datasets used by our collaboration. 

Any logic that is general enough to warrant re-use is moved into the `batdata` Python package.

The Python package also holds the schemas, which are described in 
[`schemas.py`](./batdata/schemas/__init__.py).
