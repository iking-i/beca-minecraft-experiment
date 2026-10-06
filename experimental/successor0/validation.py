"""Fixed A/B/C/D and detached consumer controls. No runtime dependencies."""
from dataclasses import replace
import json
from .consumer import consume
from .engine import counts, form
from .model import Activation, Bind, Port, RequireBound, Transfer, Value


CRITERIA = (
    "S0_T1_REQUIREMENT_NON_PRESCRIPTION", "S0_T2_UNIQUE_PRODUCER_SCOPE",
    "S0_T3_REQUIREMENT_CAUSALITY", "S0_T4_LOCAL_FORMATION",
    "S0_T5_NON_EXHAUSTIVE_D10", "S0_T6_NON_EXHAUSTIVE_D100",
    "S0_T7_NON_EXHAUSTIVE_D1000", "S0_T8_NECESSARY_EDGE_ABLATION",
    "S0_T9_FORMED_ORGANIZATION_CONSUMPTION", "S0_T10_CONSUMER_ABLATION")


def fixture(prefix=""):
    u, m, q, v = (prefix + name for name in ("u", "m", "q", "V"))
    h = frozenset((Port(u, "T", "test"), Port(m, "T", "test"), Port(q, "T", "test"),
                   Value(v, "T", "test"), Bind(u, v), Transfer(u, m), Transfer(m, q)))
    return h, RequireBound(q, "T", "test")


def distractors(n):
    material = set()
    for i in range(n):
        a, b, v = (f"d{i}:{name}" for name in ("a", "b", "value"))
        material.update((Port(a, "T", "test"), Port(b, "T", "test"),
                         Value(v, "T", "test"), Bind(a, v), Transfer(a, b)))
    return frozenset(material)


def support_ablation(s):
    # Detached projection of an already formed organization, not producer input.
    return replace(s, supports=frozenset(e for e in s.supports
                                        if not (e.rule == "TRANSFER" and e.conclusion == Bind("m", "V"))))


def run_validation():
    h, r = fixture()
    a, b = form(h, r), form(h)
    c = form(h - {Transfer("u", "m")}, r)
    case_results = {}
    for name, result in (("A", a), ("B", b), ("C", c)):
        case_results[name] = {"status": result.status, **counts(result),
                              "consumer": consume(result.organization, "q").status,
                              "identity": result.organization.identity if result.organization else None}
    outcomes = {}
    renamed_h, renamed_r = fixture("opaque:")
    renamed = form(renamed_h, renamed_r)
    outcomes[CRITERIA[0]] = (set(r.__dataclass_fields__) == {"port", "type", "scope"}
                             and consume(renamed.organization, renamed_r.port).value == "opaque:V")
    multiple = form(h | {Transfer("u", "q")}, r)
    cyclic = form(h | {Transfer("q", "u")}, r)
    outcomes[CRITERIA[1]] = multiple.status == cyclic.status == "INVALID_FIXTURE"
    outcomes[CRITERIA[2]] = b.organization is None and counts(b) == {
        "activated_relation_count": 0, "derived_binding_count": 0, "formed_support_count": 0}
    outcomes[CRITERIA[3]] = (a.status == "COMPLETE_LOCAL_SUPPORT" and counts(a) == {
        "activated_relation_count": 2, "derived_binding_count": 2, "formed_support_count": 6}
        and consume(a.organization, "q").value == "V")
    for n, criterion in zip((10, 100, 1000), CRITERIA[4:7]):
        extra = distractors(n)
        d = form(h | extra, r)
        activated = sum(isinstance(f, Activation) and f.relation in extra
                        for f in d.organization.facts)
        derived = sum(e.rule == "TRANSFER" and e.conclusion.port.startswith("d")
                      for e in d.organization.supports)
        trace_outside = any(entry[0] == "LOOKUP" and entry[1].startswith("d") for entry in d.trace)
        case_results[f"D{n}"] = {"status": d.status, **counts(d),
                                  "identity": d.organization.identity,
                                  "distractor_component_count": n,
                                  "distractor_activated_count": activated,
                                  "distractor_derived_fact_count": derived,
                                  "trace": [[e[0], str(e[1:])] for e in d.trace]}
        outcomes[criterion] = (d.organization.logical_content() == a.organization.logical_content()
                               and d.organization.identity == a.organization.identity
                               and counts(d) == counts(a) and activated == derived == 0
                               and not trace_outside and consume(d.organization, "q").value == "V")
    outcomes[CRITERIA[7]] = (c.status == "UNRESOLVED" and Bind("m", "V") not in c.organization.facts
                             and Bind("q", "V") not in c.organization.facts
                             and consume(c.organization, "q").status == "UNRESOLVED")
    screened = support_ablation(a.organization)
    outcomes[CRITERIA[8]] = (screened.facts == a.organization.facts
                             and screened.requirement == a.organization.requirement
                             and consume(screened, "q").status == "UNRESOLVED")
    outcomes[CRITERIA[9]] = (consume(a.organization, "q").status == "RESOLVED"
                             and consume(None, "q").status == "UNRESOLVED")
    status = "PASS" if all(outcomes.values()) else "FAIL"
    return {"status": status, "scope": "TEST_ONLY unique-producer acyclic typed Transfer; external requirement",
            "criteria": {k: "PASS" if v else "FAIL" for k, v in outcomes.items()},
            "cases": case_results, "consumer_ablation": consume(None, "q").status,
            "support_ablation": consume(screened, "q").status,
            "first_failure": next((k for k, v in outcomes.items() if not v), None),
            "case_a_organization": a.organization.logical_content(),
            "case_a_trace": [[e[0], str(e[1:])] for e in a.trace],
            "claim": "Given an externally supplied opaque requirement, a fixed non-semantic local formation rule can form and causally expose a requirement-bounded organization without global exhaustive structural enumeration, within the unique-producer acyclic TEST_ONLY scope."}


if __name__ == "__main__":
    print(json.dumps(run_validation(), ensure_ascii=False, indent=2))
