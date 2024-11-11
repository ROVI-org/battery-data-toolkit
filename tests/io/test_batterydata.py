from datetime import datetime

from pytest import fixture
from pydantic import AnyUrl

from battdat.io.batterydata import BDExtractor, generate_metadata

example_metadata = {'cell_type': ['Pouch cell'],
                    'creator_user_id': 'a853d711-0e37-44c9-80c9-a41d450c2da4',
                    'date_dataset_created': '2018-08-16',
                    'electrolyte_class_dataset': ['Organic liquid'],
                    'id': 'ef9dec93-17a2-445a-b58e-dc3eadb1f79d',
                    'isopen': False,
                    'manufacturer_supplier': 'CAMP',
                    'maximum_voltage': '4.1',
                    'metadata_created': '2024-04-19T21:18:38.938069',
                    'metadata_modified': '2024-04-20T00:45:59.866451',
                    'minimum_voltage': '3',
                    'name': 'xcel-round-2-slpc_reupload_2',
                    'negative_electrode': ['Graphite'],
                    'nominal_cell_capacity': '0.037',
                    'notes': 'Single layer pouch cell from CAMP (2.5mAh/cm2) at various charge protocols (CCCV and Multi-step).',
                    'num_resources': 35,
                    'num_tags': 9,
                    'onec_cell_capacity': '0.032',
                    'organization': {'id': '67de8624-a528-43df-9b63-a65a410920bb',
                                     'name': 'xcel',
                                     'title': 'XCEL',
                                     'type': 'project',
                                     'description': 'XCEL Project ',
                                     'image_url': '',
                                     'created': '2023-06-08T17:38:37.007623',
                                     'is_organization': True,
                                     'approval_status': 'approved',
                                     'state': 'active'},
                    'owner_org': '67de8624-a528-43df-9b63-a65a410920bb',
                    'poc_email_address': 'Sangwook.Kim@inl.gov',
                    'poc_institution': ['INL'],
                    'poc_name': 'skim',
                    'positive_electrode': ['NMC532'],
                    'private': False,
                    'reference_electrode': ['No'],
                    'separator_class': ['PP polymer'],
                    'state': 'active',
                    'technology': ['Li-ion'],
                    'title': 'XCEL Round 2 SLPC',
                    'type': 'dataset',
                    'tags': [{'display_name': 'fast charge',
                              'id': '04f1dafd-24f0-496e-b263-96038a9da8f8',
                              'name': 'fast charge',
                              'state': 'active',
                              'vocabulary_id': None}]}


@fixture()
def test_files(file_path):
    return file_path / 'batterydata'


def test_detect_then_convert(test_files):
    # Find two files
    extractor = BDExtractor(store_all=False)
    group = next(extractor.identify_files(test_files))
    assert len(group) == 2

    # Parse them
    data = extractor.read_dataset(group)
    assert data.metadata.name == 'p492-13'

    # Test a few of columns which require conversion
    assert data.raw_data['cycle_number'].max() == 8
    first_measurement = datetime.fromtimestamp(data.raw_data['time'].iloc[0])
    assert first_measurement.year == 2020
    assert first_measurement.day == 3

    # Ensure it validates
    data.validate()


def test_store_all(test_files):
    """Make sure we get exactly one copy of all columns"""

    # Find two files
    extractor = BDExtractor(store_all=True)
    group = next(extractor.identify_files(test_files))
    data = extractor.read_dataset(group)

    # Make sure we only have the renamed `cycle_number` and not original `Cycle_Index`
    for df in [data.raw_data, data.cycle_stats]:
        assert 'cycle_number' in df.columns
        assert 'Cycle_Index' not in df.columns

    # Make sure NREL-specific columns are stored
    assert 'datenum_d' in data.cycle_stats.columns
    assert 'Charge_Throughput_Ah' in data.raw_data.columns


def test_metadata():
    metadata = generate_metadata(example_metadata, ('https://test.url/',))
    assert AnyUrl('https://test.url/') in metadata.associated_ids
    assert metadata.battery.cathode.name == 'NMC532'
