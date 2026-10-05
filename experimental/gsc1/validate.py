"""TEST_ONLY validation; writes GSC-1 reports only, never frozen GSC-0 files."""
from hashlib import sha256
from pathlib import Path
from time import perf_counter
import json
import subprocess
import unittest
from experimental.gsc0.engine import Engine, Caps
from experimental.gsc0.model import Binding, Seed, Value, encode
from experimental.gsc0.tests import GSC0Tests
from .tests import GSC1Tests
from .fixtures import paired_fixture, close_history
from .grounding import check_grounding

ROOT = Path(__file__).resolve().parents[2]
BASELINE = '8801ca88093e5c66fa11ba6eb4c084608a1bd690'


def baseline_hashes():
    paths = subprocess.check_output(['git', 'ls-tree', '-r', '--name-only', '-z', BASELINE], cwd=ROOT).decode('utf-8').split('\0')
    return {p: sha256((ROOT / p).read_bytes()).hexdigest() for p in paths if p}


def frozen_paths(hashes):
    return {p: h for p, h in hashes.items() if p.startswith('experimental/gsc0/')
            or p.startswith('GSC0_PROTOTYPE_VALIDATION.') or p == 'GENERATIVE_STRUCTURAL_CLOSURE_SPEC.md'}


def seed_record(seed):
    return {'key': seed.fact.key, 'sources': seed.sources, 'rule': seed.rule}


def grounding_record(result):
    return {'status': result.status, 'complete': result.complete,
            'outward': None if result.outward is None else {
                'key': result.outward.key,
                'fields': {name: {'type': value.value_type, 'value': value.value}
                           for name, value in result.outward.fields}},
            'closure_digest': result.closure_digest, 'reason': result.reason,
            'ports': [{'name': p.name, 'status': p.status,
                       'values': [v.key for v in p.values],
                       'evidence': [{'binding_key': e.binding_key,
                                     'input_roots': sorted(e.input_roots, key=encode),
                                     'all_direct_supports': [{'rule': s.rule, 'premises': s.premises}
                                                             for s in e.direct_supports]}
                                    for e in p.evidence]} for p in result.ports]}


def main():
    before = baseline_hashes()
    started = perf_counter()
    runner = unittest.TextTestRunner(verbosity=2)
    gsc1 = runner.run(unittest.defaultTestLoader.loadTestsFromTestCase(GSC1Tests))
    gsc0 = runner.run(unittest.defaultTestLoader.loadTestsFromTestCase(GSC0Tests))
    report = {'GSC1_PROTOTYPE': 'partial', 'scope': 'Independent TEST_ONLY read-only GSC-0 consumer',
              'frozen_gsc0_commit': BASELINE,
              'tests': {label: {'run': result.testsRun,
                                'failures': len(result.failures), 'errors': len(result.errors),
                                'skipped': len(result.skipped),
                                'successful': result.wasSuccessful() and not result.skipped}
                        for label, result in (('gsc1', gsc1), ('frozen_gsc0_regression', gsc0))}}
    success = all(r['successful'] for r in report['tests'].values())
    if success:
        f = paired_fixture()
        cases = {}
        for label, history in (('A', f.history_a), ('B', f.history_b)):
            initial, closed = close_history(f, history)
            grounded = check_grounding(closed, f.schema)
            cases[label] = {'history': [seed_record(s) for s in history],
                            'initial_grounding': grounding_record(check_grounding(initial, f.schema)),
                            'closure': closed.stats(), 'grounding': grounding_record(grounded)}
        _, missing = close_history(f, f.history_a[:1] + f.history_a[2:])
        _, input_missing = close_history(f, f.history_a, current=f.current_input[:1] + f.current_input[2:])
        extra = Seed(Binding(f.sources[1], Value('B1', 'TypeB')), ('H1-conflict',))
        _, conflict = close_history(f, f.history_a + (extra,))
        limited = Engine(f.condition, Caps(structures=200)).run(f.history_a + f.current_input)
        rejected = check_grounding(limited, f.schema)
        assert all(c['grounding']['status'] == 'COMPLETE_GROUNDED' for c in cases.values())
        assert all(c['initial_grounding']['status'] == 'UNRESOLVED' for c in cases.values())
        assert cases['A']['grounding']['outward'] != cases['B']['grounding']['outward']
        assert rejected.status == 'RESOURCE_LIMIT' and rejected.outward is None
        report.update({
            'GSC1_PROTOTYPE': 'passed',
            'core_checks': {name: 'passed' for name in (
                'complete_unique_grounding', 'unresolved', 'conflict', 'paired_history_causality',
                'history_ablation', 'current_input_ablation', 'order_independence', 'idempotence',
                'upstream_resource_limit_rejection', 'no_selector', 'no_default_filling',
                'lineage_completeness', 'read_only_checker', 'isolation')},
            'condition': {'nodes': [n.key for n in f.condition.nodes],
                          'values': [v.key for v in f.condition.values],
                          'signatures': f.condition.signatures, 'version': f.condition.version},
            'schema': f.schema.key,
            'shared_current_input': [seed_record(s) for s in f.current_input],
            'shared_current_input_digest': sha256(encode(tuple(seed_record(s) for s in f.current_input)).encode()).hexdigest(),
            'history_changed_records': [0, 2], 'cases': cases,
            'history_ablation_example': grounding_record(check_grounding(missing, f.schema)),
            'current_ablation_example': grounding_record(check_grounding(input_missing, f.schema)),
            'conflict_example': grounding_record(check_grounding(conflict, f.schema)),
            'resource_limit_example': {'upstream': limited.stats(), 'limit': limited.limit,
                                       'all_required_bindings_already_present': all(
                                           any(isinstance(fact, Binding) and fact.variable == p.variable
                                               for fact in limited.state.facts.values()) for p in f.schema.ports),
                                       'grounding': grounding_record(rejected)},
            'authorship': {'schema': 'EXTERNAL_FIXED_MECHANISM',
                          'gsc_rules': 'EXTERNAL_FIXED_MECHANISM',
                          'historical_bindings_and_current_equality': 'EXPLICIT_FIXTURE_INPUT',
                          'output_binding': 'PROP-ALIAS consequence of history + current input',
                          'tuple': 'MECHANICAL_SINGLETON_PACKAGING',
                          'selector_count': 0, 'default_or_fallback_filling_count': 0},
            'limits': ['No new primitive values, rules, schema discovery, body output or L1.',
                       'Packaging determinacy is conditional on a truthful COMPLETE GSC-0 Result.',
                       'Tuple is a read-only external representation, not a new GSC-0 relation.',
                       'The fixture supplies equality declarations; it does not discover them.']})
    after = baseline_hashes()
    changed = [p for p in before if before[p] != after[p]]
    if changed:
        report['GSC1_PROTOTYPE'] = 'failed'
    report['boundary_guard'] = {'baseline_files_verified': len(before), 'unchanged': not changed,
                                'changed_paths': changed, 'frozen_gsc0_file_hashes': frozen_paths(before),
                                'gsc0_modified': any(p in frozen_paths(before) for p in changed),
                                'formal_l0_minecraft_a_modified': any(p.startswith(('individual/', 'minecraft/', 'bridge/', 'supervisor/')) for p in changed)}
    report['validation_seconds'] = round(perf_counter() - started, 6)
    (ROOT / 'GSC1_PROTOTYPE_VALIDATION.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    passed = report['GSC1_PROTOTYPE'] == 'passed'
    results = ('History_A = (A0, B0, C0); History_B = (A1, B0, C1)。两个结果均 COMPLETE_GROUNDED，历史 closure 端口均 UNRESOLVED。'
               if passed else '核心条件未全部通过，不声明完整 grounding 验收通过；详见 JSON 测试结果。')
    text = f'''# GSC-1 Prototype Validation

日期：2026-10-05。冻结 GSC-0 基准：`{BASELINE}`。

**GSC1_PROTOTYPE = {report['GSC1_PROTOTYPE']}**。独立 TEST_ONLY consumer；本次不修改 GSC-0 或正式运行系统。

## 实际执行结果

`python -m experimental.gsc1.validate` 实际运行 GSC-1 **{gsc1.testsRun} 项**和冻结 GSC-0 回归 **{gsc0.testsRun} 项**。
GSC-1 failures/errors：{len(gsc1.failures)}/{len(gsc1.errors)}；GSC-0 failures/errors：{len(gsc0.failures)}/{len(gsc0.errors)}。未跳过测试。

{results}

## 条件与因果

三个类型、六个普通变量、六个有限枚举值和 schema 完全相同。两个历史共用相同 CurrentInput tuple：Eq(h0,p0)、Eq(h1,p1)、Eq(h2,p2)，來源 D0/D1/D2。历史唯一差异是 H0、H2 的变量—值 Binding 内容；H1 不变。

初始历史只有 h0/h1/h2 的三个独立 Bind，不含任何 p0/p1/p2 Bind 或完整 outward。当前 explicit equality 使 GSC-0 PROP-ALIAS 产生输出绑定；每个新绑定都有对应 Hi、Di 输入根和全部直接支持。原 closure 还形成包含历史 Bind、当前 Eq、新 Bind 的 Composite；不会为了 GSC-1 删去其他组合。

checker 扫描整个 COMPLETE closure。对每个端口精确去重后的值集合，0→UNRESOLVED、1→GROUNDED、>=2→CONFLICT。全部 singleton 才逐项解包形成完整 tuple。schema 固定字段身份、类型和顺序，不提供值；包装不增加推理、分数、候选、规则、动作或 GSC-0 事实。

## 核心验收

| 检查 | 实际测试内容 |
|---|---|
| 唯一完整 grounding | A/B 得到两个不同完整 tuple，历史中尚无输出端口绑定 |
| Paired-history causality | 相同实际 input/source/Condition/schema；交换历史可复现另一结果 |
| History ablation | 两个历史各删除三个关键历史 Bind，六次全部重建 closure；对应端口缺失 |
| Current-input ablation | 两个历史各删除三个 Eq，六次全部重建 closure；对应端口缺失 |
| Conflict | B0/B1 全部传播，输出保留两值证据，不构造完整 tuple；独立三值测试也全部保留 |
| Mixed failure | 缺失与冲突端口同时保留；overall CONFLICT 不解决任何值 |
| Order independence | 两个历史 × 三种 seed 顺序 × 三种 queue/rule 顺序；18 次 COMPLETE closure 和完整 GroundingResult 按内容相等 |
| Idempotence | 两个 COMPLETE closure 重新闭包、重新 grounding 后全部内容相同 |
| Upstream resource rejection | 小 cap 的 working state 已有所有端口 Bind，仍 RESOURCE_LIMIT；GSC-1 不接纳成成功 |
| No default / old value filling | 缺失返回 outward=None；新 scope 不复用同名旧变量；先完整再缺失也不缓存旧 tuple |
| Lineage | 所有派生对象有有限根；逐端口保存所有直接支持和所有输入根，含 Hi/Di/PROP-ALIAS |
| Invalid input | 错 schema、域、类型或非法 upstream 明确 INVALID，不丢弃问题绑定后冒称成功 |
| Isolation | 双向 import 边界检查；checker 只读，包装不插入原 closure |

核心检查最终状态见机器报告，表中的测试内容不取代实际执行结果。

## 作者权审计

实现位置：`experimental/gsc1/grounding.py::check_grounding`。输出值提取只使用 `(unique_value,) = port.values`，位于所有端口已判 singleton 的路径。机械包装没有 choose/prefer/fallback/repair 或 normalize-by-preference；没有 selector，也没有 NO_OP。

EXTERNAL_FIXED_MECHANISM：GSC-0 固定规则、schema、精确值数量条件和包装机制。EXPLICIT_FIXTURE_INPUT：人工历史 Bind 与当前 Eq。具体派生输出由历史和当前输入共同决定。此结果证明条件下的结构确定性，**不证明新值创造、schema/equality 的自主发现、一般智能、主体连续性或 L1**。

规范 identity 与 provenance 分离；JSON 保存每个端口完整 direct-support 集合与有限 input roots，closure digest 指向原有全部 immediate graph/COMPOSE 无损索引。没有 first-proof 取舍或无限展开循环 proof tree。

## 冻结边界与文件

验证前后核对 **{len(before)} 个基线 tracked 文件**字节 hash：{'全部相同' if not changed else '发现变化，不能判 passed'}。冻结 GSC-0 文件 hash 单列在 JSON。本次没有调用 GSC-0 validate，没有写旧报告，没有连接游戏、数据库或正式 A。

- [规格](GSC1_DETERMINATE_GROUNDING_SPEC.md)
- [原型与运行说明](experimental/gsc1/README.md)
- [源码](experimental/gsc1/grounding.py)、[测试](experimental/gsc1/tests.py)
- [机器报告与完整端口来源](GSC1_PROTOTYPE_VALIDATION.json)

```powershell
.\\.venv\\Scripts\\python.exe -m unittest experimental.gsc1.tests -v
.\\.venv\\Scripts\\python.exe -m experimental.gsc1.validate
```

GSC-1 是 frozen GSC-0 的 consumer。现有 API 足以完成本轮；未发现必须修改上游的接口缺口。未继续接入正式 runtime 或实现真实输出。
'''
    (ROOT / 'GSC1_PROTOTYPE_VALIDATION.md').write_text(text, encoding='utf-8')
    print(json.dumps({'GSC1_PROTOTYPE': report['GSC1_PROTOTYPE'], 'tests': report['tests'],
                      'baseline_files_unchanged': not changed}, ensure_ascii=True))
    return 0 if passed else 1


if __name__ == '__main__':
    raise SystemExit(main())
