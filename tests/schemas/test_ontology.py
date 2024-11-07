"""Test the ability to resolve cross-references from the ontology"""

from battdat.schemas import BatteryMetadata
from battdat.schemas.ontology import cross_reference_terms, gather_descendants, load_battinfo, resolve_term


def test_crossref():
    terms = cross_reference_terms(BatteryMetadata)
    assert 'is_measurement' in terms
    assert terms['is_measurement'].name == 'emmo.Measurement'
    assert 'EMMO' in terms['is_measurement'].iri
    assert 'well defined mesurement procedure.' in terms['is_measurement'].elucidation


def test_resolve():
    assert resolve_term('PhysicsBasedSimulation') is not None
    assert resolve_term('https://w3id.org/emmo#EMMO_f7ed665b_c2e1_42bc_889b_6b42ed3a36f0') is not None


def test_descendants():
    bi = load_battinfo()
    desc = [t.name for t in gather_descendants(bi.PhysicsBasedSimulation)]
    assert 'emmo.StandaloneModelSimulation' in desc

    desc = [t.name for t in gather_descendants('PhysicsBasedSimulation')]
    assert 'emmo.StandaloneModelSimulation' in desc
