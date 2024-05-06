# The `BatteryDataset` Object

The `BatteryDataset` object is the central object for the battery data tookit. 
Extractors render vendor-specific data into the `BatteryDataset`,
schemas describe its contents,
and post-processing codes manipulate.

## Using the `BatteryDataset` Object

The `BatteryDataset` holds different types of data about a battery in separate Pandas dataframes,
and metadata describing the source of the data in a `.metadata` attribute.

> TBD: Describe the types of data

## Loading and Saving

The battery data and metadata can be saved in a few different styles, each with different advantages.

### HDF5

The HDF5 file format stores all data about a battery in a single file.

> TBD: Explain that we use `pytables` now, but that may change in the future

#### Multiple Batteries per File

Battery Data Toolkit supports storing data from multiple, related batteries in the same HDF5 file 
as long as they share the same metadata.

Add multiple batteries into an HDF5 file by providing a "prefix" to name each cell.

```python
test_a.to_batdata_hdf('test.h5', prefix='a')
test_b.to_batdata_hdf('test.h5', prefix='b', append=True)  # Append is mandatory
```

Load a specific cell by providing a specific prefix on load

```python
test_a = BatteryDataset.from_batdata_hdf('test.h5', prefix='a')
```

or load any of the included cells by providing an index

```python
test_a = BatteryDataset.from_batdata_hdf('test.h5', prefix=0)
```

Load all cells by iterating over them:

```python
for name, cell in BatteryDataset.all_cells_from_batdata_hdf('test.h5'):
    do_some_processing(cell)
```

### Parquet

TBD.
