"""Tools used for linking terms in our data format to the BattINFO ontology"""
from dataclasses import dataclass, field
from functools import cache
from typing import Type, List, Optional, Union

from ontopy import World
from owlready2 import Thing
from pydantic import BaseModel

_battinfo_url = 'https://raw.githubusercontent.com/emmo-repo/domain-battery/master/battery-inferred.ttl'


@cache
def load_battinfo():
    """Download and store the latest ontology into an in-memory"""
    return World().get_ontology(_battinfo_url).load()


@dataclass
class TermInfo:
    """Information about a term as referenced from the BattINFO ontology"""

    name: str
    """Name of the matching term"""
    iri: str = field(repr=False)
    """IRI of the term"""
    elucidation: Optional[str] = field(repr=False)
    """Explanation of the term"""

    @classmethod
    def from_thing(cls, thing: Thing):
        # Retrieve the description, as provided by EMMO
        eluc = thing.get_annotations().get('elucidation')
        if eluc is not None:
            eluc = str(eluc[0])
        return TermInfo(name=str(thing), iri=thing.iri, elucidation=eluc)


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
            terms[name] = TermInfo.from_thing(term)

    return terms


def resolve_term(name_or_iri: str) -> Thing:
    """Resolve the Term object associated with a string

    Args:
        name_or_iri: The preferred label or the IRI of a term in the ontology
    Returns:
        Thing matching the term
    """

    # Attempt to find it
    bi = load_battinfo()
    if name_or_iri.startswith('https://'):
        term = bi.search_one(iri=name_or_iri)
        t = 'IRI'
    else:
        term = bi.search_one(prefLabel=name_or_iri)
        t = 'name'

    if term is None:
        raise ValueError(f'Could not find the {t}={name_or_iri}')
    return term


def gather_descendants(term: Union[Type[Thing], str]) -> List[TermInfo]:
    """Get descriptions of the descendants of a certain base type

    Args:
        term: Term for which to gather all descendants. Either the class object itself or its preferred label or IRI
    Returns:
        List of descriptions of the descendants
    """

    # Resolve the term object, if needed
    if isinstance(term, str):
        term = resolve_term(term)

    return [
        TermInfo.from_thing(d) for d in term.descendants(include_self=False)
    ]
