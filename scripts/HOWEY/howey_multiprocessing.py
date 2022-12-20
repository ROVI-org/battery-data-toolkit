"""Parse tIVT .npy data from the Howey dataset

cite howey paper

"""

from batdata.extractors.tIVT import TIVTExtractor

from tqdm import tqdm
import numpy as np
import pandas as pd

import shutil
import os

from batdata.schemas import BatteryMetadata
from multiprocessing import Pool

root_folder = '/lcrc/project/battdat/npaulson/howey_data/data_files_raw'
output_folder = '/lcrc/project/battdat/npaulson/howey_data/data_files_processed'

# Metadata for all batteries
test_metadata = {
    'use case': ('photovoltaic cell with Pb-acid for lighting,'
                 'phone charging, and small appliances in sub-Saharan Africa'),
    'manufacturer': 'BBOXX Ltd.',
    'nominal_capacity': 20,
    'nominal_voltage': 12,
    'source': 'University of Oxford',
    'dataset_name': 'Aitio, Joule (2021)',
    'associated_ids': [
        'https://doi.org/10.1016/j.joule.2021.11.006'
    ]
}


def process_write(inp):
    cell_index, subset = inp

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
    cell_data.to_batdata_hdf(out_path, complevel=9)


if __name__ == "__main__":
    # Find all of the potential files
    extractor = TIVTExtractor()
    all_files = list(extractor.identify_files(root_folder))
    print(f'Located {len(all_files)} csv files in {root_folder}')

    df_md = pd.read_csv('/lcrc/project/battdat/npaulson/howey_data/meta_data.csv')
    df_md['ACTIVATED'] = pd.to_datetime(df_md['ACTIVATED'])
    df_md['IN_REPAIR_SYSTEM'] = pd.to_datetime(df_md['IN_REPAIR_SYSTEM'])

    # Parse metadata
    def get_metadata(path):
        st = path.find('raw/') + 4
        num = np.int32(path[st:-4])
        filename = path[st:]

        metadata = {
            'cell_id': num,
            'path': path,
            'filename': filename,
            'date': df_md['ACTIVATED'].values[num],
            'date_in_repair_sys': df_md['IN_REPAIR_SYSTEM'].values[num],
            'reached_failure': df_md['STILL_ALIVE'].values[num],
            'lifetime_days': df_md['Lifetime'].values[num]
        }
        return metadata

    metadata = list(filter(lambda x: x is not None, map(get_metadata, all_files)))

    # Create a dataframe of all files
    data = pd.DataFrame(metadata)
    print(f'Found {len(data)} total data files')

    # Delete the old files
    if os.path.isdir(output_folder):
        shutil.rmtree(output_folder)
    os.makedirs(output_folder)

    n_cells = len(set(data["cell_id"]))
    print(f'There are {n_cells} unique cells')

    inputs = []
    for cell_index, (_, subset) in enumerate(data.groupby('cell_id')):
        inputs.append((cell_index, subset))

    with Pool(18) as p:
        r = list(tqdm(p.imap(process_write, inputs), total=n_cells))
