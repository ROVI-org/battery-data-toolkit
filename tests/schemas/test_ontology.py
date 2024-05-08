"""Test the ability to resolve cross-references from the ontology"""

from batdata.schemas import BatteryMetadata
from batdata.schemas.ontology import cross_reference_terms


def test_crossref():
    terms = cross_reference_terms(BatteryMetadata)
    assert 'is_measurement' in terms
    assert terms['is_measurement'].name == 'emmo.Measurement'
    assert 'EMMO' in terms['is_measurement'].iri
    assert 'well defined mesurement procedure.' in terms['is_measurement'].iri
