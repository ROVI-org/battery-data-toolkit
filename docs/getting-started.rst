Getting Started
===============

Battery-Data-Toolkit is a Python toolkit for storing and manipulating data from battery systems.
Most operations are based on `Pandas <https://pandas.pydata.org/docs/>`_ to simplify using
common libraries for data science for battery science.

Installation
------------

Battery Data Toolkit is available on PyPI and is pure Python.
Installing via Pip will work on most systems:

.. code-block:: shell

    pip install battery-data-toolkit

Build the toolkit for development by cloning the repository
then installing with the "tests" and "docs" optional packages:

.. code-block:: shell

    git clone git@github.com:ROVI-org/battery-data-toolkit.git
    cd battery-data-toolkit
    pip install -e .[test,docs]
