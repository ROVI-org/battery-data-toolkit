"""Parse batches 1 and 2 from the Severson dataset

This script contains logic specific to how this particular paper encoded their metadata,
such as how the charging schedule is recorded in the file name and additional test data
is captured on the website: https://data.matr.io/1/projects/5c48dd2bc625d700019f3204

The script is hard-coded to read from a Box folder.

"""

from battdat.extractors.arbin import ArbinExtractor

from tqdm import tqdm
import pandas as pd

import shutil
import os
import re

# Hard code root directory of data
from battdat.schemas import BatteryMetadata

root_folder = os.path.join(os.path.expanduser("~"), "Box", "ASOH LDRD",
                           "Nature Energy Data and Data Extraction", "Raw CSV files")
output_folder = os.path.join(os.path.join(os.path.dirname(__file__)), 'severson')

# Hard code the channels that are the same cell from the first two batches
first_two_batches = ['2017-05-12', '2017-06-30']
channels_to_combine = [1, 2, 3, 5, 6]

# Define the regex for reading metadata from filenames
#  Example file name: 2017-05-12_5_4C-50per_3_6C_CH21
#  Template: <date>_<charge_1>_<SOC_switch>_<charge_2>_CH<channel_number>
#   - date: Test date
#   - charge_1: First charge rate
#   - charge_2: Second charge rate
#   - SOC_switch: SOC at which charge rate switches
#   - channel_number: Channel number in the testing machine
filename_regex = re.compile(r"(?P<date>\d{4}-\d{2}-\d{2})_(?P<charge1>[\d_]+)C-"
                            r"(?P<soc_switch>\d+)per_(?P<charge2>[\d_]+)C_CH(?P<channel>\d+)\.csv")

# Data from the third batch do not have the charge information
batch3_regex = re.compile(r"(?P<date>\d{4}-\d{2}-\d{2})_batch8_CH(?P<channel>\d+)\.csv")

# Metadata for all of the batteries
test_metadata = {
    'cycler': 'Arbin LBT Potentiostat',
    'set_temperature': 30.0,

    'manufacturer': 'A123 Systems',
    'design': 'APR18650M1A',
    'nominal_capacity': 1.1,
    'anode': 'graphite',
    'cathode': 'LFP',
    'source': 'Stanford University',
    'dataset_name': 'Severson, Nature Energy (2019)',
    'associated_ids': [
        'https://doi.org/10.1038/s41560-019-0356-8',
        'https://data.matr.io/1/projects/5c48dd2bc625d700019f3204'
    ]
}


if __name__ == "__main__":
    # Find all of the potential files
    extractor = ArbinExtractor()
    all_files = list(extractor.identify_files(root_folder))
    print(f'Located {len(all_files)} csv files in {root_folder}')

    # Parse metadata from filenames
    def parse_filename(path):
        # Get metdata from filename
        filename = os.path.basename(path)
        match = filename_regex.match(filename)
        if match is None:
            # Attempt the batch 3 regex
            match = batch3_regex.match(filename)
            if match is None:
                return None

        # Store the data in a dict
        metadata = match.groupdict()
        metadata['path'] = path
        metadata['filename'] = filename
        return metadata
    metadata = list(filter(lambda x: x is not None, map(parse_filename, all_files)))

    # Create a dataframe of all of the files
    data = pd.DataFrame(metadata)
    print(f'Found {len(data)} total data files')

    # Delete the old files
    if os.path.isdir(output_folder):
        shutil.rmtree(output_folder)
    os.makedirs(output_folder)

    # Coerce data into numeric types
    data['channel'] = pd.to_numeric(data['channel'])

    # Group the channels that are continuations of each other
    data['cell_id'] = range(len(data))  # Give each battery a unique cell ID
    data.sort_values(['date', 'channel'], inplace=True, ascending=True)  # To have reporducible order
    for ch in channels_to_combine:
        subset = data.query(f'channel=="{ch}"')
        subset = subset[subset['date'].isin(first_two_batches)]
        data.loc[subset.index, 'cell_id'] = subset['cell_id'].min()
    n_cells = len(set(data["cell_id"]))
    print(f'There are {n_cells} unique cells')

    # Loop over all of the batteries
    for cell_index, (_, subset) in tqdm(enumerate(data.groupby('cell_id')), total=n_cells):
        # cell_index will be monotonically increasing, giving us a short reference to a file name

        # Get the files to be parsed
        files = subset['path'].tolist()

        # Make a metadata object
        cell_metadata = subset.iloc[0]
        metadata = BatteryMetadata(name=cell_metadata['filename'][:-4],
                                   start_date=cell_metadata['date'], **test_metadata)

        # Parse them into a single object
        cell_data = extractor.parse_to_dataframe(files, metadata=metadata)

        # Save it to disk
        out_path = os.path.join(output_folder, f'cell_{cell_index}.h5')
        cell_data.to_hdf(out_path, complevel=9)
