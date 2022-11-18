"""Pasrse example MACCOR data

"""
from tqdm import tqdm
import pandas as pd

import shutil
import os
from batdata.schemas import BatteryMetadata
from batdata.extractors.maccor import MACCORExtractor

# Hard code root directory of data
root_folder = os.path.join(os.path.dirname(__file__))
output_folder = os.path.join(os.path.join(os.path.dirname(__file__)), 'out_maccor')

if __name__ == "__main__":
    # Find all potential files
    extractor = MACCORExtractor()
    all_files = list(extractor.identify_files(root_folder))
    print(f'Located {len(all_files)} csv files in {root_folder}')

    # Parse metadata from filenames
    def parse_filename(path):
        # Get metdata from filename
        filename = os.path.basename(path)
        metadata = {}
        metadata['path'] = path
        metadata['filename'] = filename
        metadata['channel'] = 4
        return metadata

    metadata = list(filter(lambda x: x is not None, map(parse_filename, all_files)))

    # Create a dataframe of all files
    data = pd.DataFrame(metadata)
    print(f'Found {len(data)} total data files')

    # Delete the old files
    if os.path.isdir(output_folder):
        shutil.rmtree(output_folder)
    os.makedirs(output_folder)

    # Coerce data into numeric types

    data['cell_id'] = range(len(data))  # Give each battery a unique cell ID
    n_cells = len(set(data["cell_id"]))

    # Loop over all of the batteries
    for cell_index, (_, subset) in tqdm(enumerate(data.groupby('cell_id')), total=n_cells):
        # cell_index will be monotonically increasing, giving us a short reference to a file name

        # Get the files to be parsed
        files = subset['path'].tolist()

        # Make a metadata object
        cell_metadata = subset.iloc[0]
        metadata = BatteryMetadata(name=cell_metadata['filename'][:-4])
        name = cell_metadata['filename'][:-4]
        # Parse them into a single object
        cell_data = extractor.parse_to_dataframe(files, metadata=metadata)

        # Save it to disk
        out_path = os.path.join(output_folder, f'cell_{name}.h5')
        cell_data.to_batdata_hdf(out_path, complevel=9)
