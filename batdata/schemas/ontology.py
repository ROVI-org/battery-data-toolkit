"""Tools used for linking terms in our data format to the BattINFO ontology"""
from dataclasses import dataclass, field
from functools import cache
from typing import Type

from ontopy import World
from pydantic import BaseModel

_battinfo_url = 'https://raw.githubusercontent.com/emmo-repo/domain-battery/master/battery-inferred.ttl'


@cache
def load_battinfo():
    return World().get_ontology(_battinfo_url).load()


@dataclass
class TermInfo:
    """Information about a term as referenced from the BattINFO ontology"""

    name: str
    """Name of the matching term"""
    iri: str = field(repr=False)
    """IRI of the term"""
    elucidation: str = field(repr=False)
    """Explanation of the term"""


def cross_reference_terms(model: Type[BaseModel]) -> dict[str, TermInfo]:
    """Gather the descriptions of fields from our schema which
    are cross-referenced to a term within the BattINFO/EMMO ontologies

    Args:
        model: Schema object to be cross-referenced
    Returns:
        Mapping between metadata fields in elucidation field from the ontology
    """

    # Load the BattINFO ontology
    battinfo = load_battinfo()

    # Loop over each field in the schema
    terms = {}
    for name, attr in model.model_fields.items():
        # Map to the term in the ontology if known
        if attr.json_schema_extra is not None and (iri := attr.json_schema_extra.get('iri')) is not None:
            term = battinfo.search_one(iri=iri)
            if term is None:
                raise ValueError(f'Count not find matching term for {name} with iri={iri}')

            anno = term.get_annotations()
            if (eluc := anno.get('elucidation')) is not None:
                terms[name] = TermInfo(name=str(term), iri=iri, elucidation=str(eluc[0]))

    return terms
