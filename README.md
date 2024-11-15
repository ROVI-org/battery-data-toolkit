# Battery Data Toolkit

[![Python Package](https://github.com/rovi-org/battery-data-toolkit/actions/workflows/python-package.yml/badge.svg)](https://github.com/rovi-org/battery-data-toolkit/actions/workflows/python-package.yml)
[![Deploy Docs](https://github.com/ROVI-org/battery-data-toolkit/actions/workflows/gh-pages.yml/badge.svg?branch=main)](https://rovi-org.github.io/battery-data-toolkit/)
[![Coverage Status](https://coveralls.io/repos/github/ROVI-org/battery-data-toolkit/badge.svg?branch=main)](https://coveralls.io/github/ROVI-org/battery-data-toolkit?branch=main)
[![PyPI version](https://badge.fury.io/py/battery-data-toolkit.svg)](https://badge.fury.io/py/battery-data-toolkit)

The battery-data-toolkit, `battdat`, creates consistently-formatted collections of battery data.
The library has three main purposes:

1. *Storing battery data in standardized formats.* ``battdat`` stores data in 
   [HDF5 or Parquet files](https://rovi-org.github.io/battery-data-toolkit/user-guide/formats.html) which include 
   [extensive metadata](https://rovi-org.github.io/battery-data-toolkit/user-guide/schemas/index.html). 
2. *Interfacing battery data with the PyData ecosystem*. The core data model,
   [``BatteryDataset``](https://rovi-org.github.io/battery-data-toolkit/user-guide/dataset.html),
   is built atop Pandas DataFrames.
3. *Providing standard implementations of common analysis techniques*. ``battdat`` implements functions which
   [ensure quality](https://rovi-org.github.io/battery-data-toolkit/user-guide/consistency/index.html)
   or [perform common analyses](https://rovi-org.github.io/battery-data-toolkit/user-guide/post-processing/index.html).

## Installation

Install ``battdat`` with pip: `pip install battery-data-toolkit`

## Documentation

Find the documentation at: https://rovi-org.github.io/battery-data-toolkit/

## Support

The motivation and funding for this project came from the Rapid Operational Validation Initiative (ROVI) sponsored by the Office of Electricity.
The focus of ROVI is "to greatly reduce time required for emerging energy storage technologies to go from lab to market by developing new tools that will accelerate the testing and validation process needed to ensure commercial success." 
If interested, you can read more about ROVI here.
