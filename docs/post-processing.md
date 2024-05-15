# Post-Processing

Most sources of battery data provide the voltage and current over time, 
but the other properties which are derived from them may be missing.
The battery data toolkit provides "post-processing" classes which 
add compute these derived data sources.

All post-processing tools are based on the `BaseFeatureComputer` class 
and, as a result, provide a `compute_features` function that adds
new information to a battery dataset.
Use them by first creating the tool and invoking that method with 
a `BatteryDataset`:

```python
computer = FeatureComputer()
new_columns = computer.compute_features(data)
```

New columns will be added to a part of the dataset (e.g., the cycle-level statistics) and those new columns
will be returned from the function.

The feature computers fall into two categories:

- `RawDataEnhancer`, which add information to the raw data as a function of time
- `CycleSummarize`, which summarize the raw data and add new columns to the `cycle_stats`

Read more about the individual tools in the [feature documentation](./features/README.md)
