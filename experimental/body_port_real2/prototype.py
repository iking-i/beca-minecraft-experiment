"""Saved formed facts -> native O -> primitive expression. No history solving."""
from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path

from experimental.body_port0.prototype import BodyPort, Member, Shared, Support, Organization
from experimental.body_port_real1.prototype import Evidence, RealExperience, RealChange, connections, canonical
from experimental.body_port_real1.validation import fact_id, structural
from individual.action_space import formal_command, CATALOG_DATA, DEFINITIONS


ROOT = Path(__file__).resolve().parents[2]
ANCHOR = ROOT / 'experimental/body_port_real1/CLOSEOUT_VALIDATION.json'
FIXED_EXPERIENCE = '03476345-ff88-4128-b64f-1adc22d8d1ad'
FIXED_PORT = BodyPort(2, 0)
EXPECTED_REPORT_SHA256 = '304166194dfd927667a74eaca5d0b42dd5935ae015ebe8bcafa91182e4655814'
TYPES = {t.__name__: t for t in (BodyPort, Member, Shared, Evidence, RealExperience, RealChange)}


class MaterialUnavailable(ValueError):
    pass


def decode(value):
    if isinstance(value, dict):
        if set(value) == {'tuple'}:
            return tuple(decode(v) for v in value['tuple'])
        if set(value) == {'set'}:
            return frozenset(decode(v) for v in value['set'])
        if set(value) == {'type', 'fields'} and value['type'] in TYPES:
            return TYPES[value['type']](**{k: decode(v) for k, v in value['fields'].items()})
        raise MaterialUnavailable('Unknown frozen structural encoding')
    return value


@dataclass(frozen=True)
class FixedMaterial:
    organization: Organization
    current: RealChange
    source_digest: str


def load_fixed(anchor=ANCHOR):
    """Decode the one already formed organization; no producer or DB access."""
    try:
        index = json.loads(Path(anchor).read_text(encoding='utf-8'))
        path = ROOT / index['original_report']
        raw = path.read_bytes()
        digest = sha256(raw).hexdigest()
        if digest != index['original_report_sha256'] or digest != EXPECTED_REPORT_SHA256:
            raise MaterialUnavailable('Frozen report digest mismatch')
        report = json.loads(raw)
        witness = report['witness']
        if (report['classification'] != 'PASS' or witness['experience_id'] != FIXED_EXPERIENCE
                or witness['port'] != {'version': 2, 'code': 0}
                or not witness['before_frame_id'].endswith(':E75')
                or not witness['after_frame_id'].endswith(':E76')):
            raise MaterialUnavailable('Fixed witness mismatch; no reselection')
        facts = {key: decode(value) for key, value in report['formed_fact_index'].items()}
        if any(fact_id(value) != key for key, value in facts.items()):
            raise MaterialUnavailable('Frozen fact identity mismatch')
        supports = frozenset(Support(facts[p['conclusion']], p['rule'],
                                     frozenset(facts[k] for k in p['premises']))
                             for p in report['all_direct_supports'])
        # The report's exact change is compared by dataclass content, not similarity.
        expected = RealChange(tuple(report['change']['scope']),
                              tuple(tuple(decode_sequence(v) for v in change) for change in report['change']['changes']))
        matches = tuple(f for f in facts.values() if isinstance(f, RealChange) and f == expected)
        if len(matches) != 1:
            raise MaterialUnavailable('Fixed C missing/ambiguous')
        return FixedMaterial(Organization(frozenset(facts.values()), supports, True), matches[0], digest)
    except (OSError, KeyError, TypeError, ValueError) as error:
        if isinstance(error, MaterialUnavailable):
            raise
        raise MaterialUnavailable(str(error)) from error


def decode_sequence(value):
    return tuple(decode_sequence(v) for v in value) if isinstance(value, list) else value


def expression_from_formed(organization, current):
    """Code source is solely the native port returned by formed-support reading."""
    read = connections(organization, current)
    if read['status'] != 'CONNECTED':
        return None
    port, = read['ports']
    definition = DEFINITIONS.get(port.code)
    if port.version != CATALOG_DATA['version'] or not definition or definition['parameters']:
        return None
    return {'expression': formal_command(port.code, {})['args'], 'port': port,
            'source': 'SUPPORTED_FORMED_CONNECTION', 'selection': 'UNIQUE_SUPPORTED_ENDPOINT'}
