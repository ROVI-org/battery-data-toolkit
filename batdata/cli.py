from materials_io.utils.interface import get_parser
from argparse import ArgumentParser
from tqdm import tqdm
import logging
import sys
import os

logger = logging.getLogger(__name__)


# List of the default parsers that are allowed to be used
_known_parsers = ['arbin']


def main():
    """Invokes the CLI application"""

    # Create the argument parser
    parser = ArgumentParser(
        description="Reads through a directory of battery data files and converts them to HDF"
    )
    parser.add_argument('--debug', action='store_true',
                        default=False, help='Print logs at the debug level')
    parser.add_argument('in_path', help='Path to root directory of data files', type=str)
    parser.add_argument('out_path', help='Path to root directory of output files', type=str)

    # Run it
    args = parser.parse_args()

    # Start the logger
    logging.basicConfig(stream=sys.stdout, level=logging.DEBUG if args.debug else logging.INFO,
                        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # Loop through all files
    for parser_name in _known_parsers:
        parser = get_parser(parser_name)
        logger.info(f'Started running with {parser.__class__.__name__} extractor')

        # File all files that are _possible_ to parse
        candidate_files = list(parser.identify_files(args.in_path))
        logger.info(f'Found {len(candidate_files)} files that could be read by this extractor')

        # Run the extractor on all files
        for in_file in tqdm(candidate_files):
            try:
                # Attempt to parse
                logger.debug(f'Attempting to extract from: {in_file}')
                data, *_ = parser.generate_dataframe(in_file)

                # If successful, save to HDF5 format
                out_dir = os.path.join(
                    args.out_path,
                    os.path.dirname(in_file),
                )
                os.makedirs(out_dir, exist_ok=True)
                out_path = os.path.join(
                    out_dir, '.'.join(os.path.basename(in_file).split('.')[:-1]) + '.hdf'
                )
                logger.debug(f'Writing to {out_path}')
                data.to_hdf(out_path, key='df', mode='w')
            finally:
                pass
