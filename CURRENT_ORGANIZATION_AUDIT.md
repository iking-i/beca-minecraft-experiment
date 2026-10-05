# Current Organization — Source and Existing-Evidence Audit

日期：2026-10-05。标准：[CURRENT_ORGANIZATION_CRITERION.md](CURRENT_ORGANIZATION_CRITERION.md)，CO-WAC-1。

仓库读取基线：`8a4df339dd3576cd5930a71630eda8830ea30087`。本轮只新增标准与审计两个文档，不运行测试/closure、启动正式 A 或连接游戏，不修改源码、原型、测试、数据或理论仓库。GSC-2 不在审计范围，不提出后续机制。

## 1. 方法与证据边界

评分重新从实际生产规则、执行读取和既有反事实的断言/具体数值推导，**不继承 README、旧审计或机器报告的总体 PASS/FAIL 标签**。旧 JSON 只用于核对已记录的输入、字段、支持和实验结果；测试源码用于核对它到底检查了什么。没有本轮重跑，就不声称本轮实测通过。

范围：

- FormalL0：当前 `FormalL0Engine.advance` 的 observation→temporal relation evidence→feedback→next read，以及实际 formal action path。主对象是新增/更新的关系记忆实例，不把固定过程壳当新组织。
- GSC-0：完整有限 closure；主新组合对象为 R4，另单列 Eq/Bind/PortBind 与 Shared graph 的生产作用。
- GSC-1：消费 frozen GSC-0 的 binding closure，主新增对象为 GroundedOutwardStructure；显式 routing 与 tuple packaging 分别审计。

既有证据源包括 `tests/test_formal_l0.py`、`debug/behavioral_validation.py`、`BEHAVIORAL_CAUSAL_CLOSURE.json`、`tests/fixtures/formal-baseline-summary.json`、两套 GSC tests 和 validation JSON。既有 JSON 的测试计数是执行记录范围，不自动成为 C1—C5 的逐项证明。

## 2. FormalL0

### C1 Novelty — PASS（新的描述/关系实例范围）

源码：[formal_l0.py:119](individual/formal_l0.py#L119) 按变化 pattern 建 unit；[第 173 行](individual/formal_l0.py#L173) 形成 antecedent/action 的 root；[第 223 行](individual/formal_l0.py#L223) 查找/创建 relation；[第 240 行](individual/formal_l0.py#L240) 加入此前不存在的 outcome。新关系内容可与此前不同，不只是 experience UUID 或 evidence_count 增加。

[structure.py:16](individual/structure.py#L16) 的 pattern_id 只编码 channel/kind 形状，不编码完整数值、语义用途；它是截断 SHA-256 内容索引，不是 hash-to-action。碰撞/抽象信息损失未在这里证明不存在，不能扩大为任意原始观察的唯一表达。

反事实与实质记录：`BEHAVIORAL_CAUSAL_CLOSURE.json.substantive_relation_contents` 的两个历史中，同一个 `U-ee9cd61aee438f8f69d4:-1` root，一侧只含 outcome `U-0294313806f11063b38a`，另一侧还含 `U-ee9cd61aee438f8f69d4`；这是真实关系材料内容差异，不是 ID 变化。`test_new_results_pressure_and_legacy_quantity_fields_do_not_cause_branching` 使用变化观察，约束该变化不能被解释为新分支/策略更新。

限制：固定 temporal-association 模板内的新实例，`causality='temporal_association_only'`；不能据此称世界因果发现、新处理方式或新组织。

### C2 Provenance — PARTIAL

源码：[formal_l0.py:182](individual/formal_l0.py#L182) experience 保留 frame/action/context/change refs；[第 205 行](individual/formal_l0.py#L205) partial 消费 feedback；[第 244 行](individual/formal_l0.py#L244) outcome 保存 experience/partial/limit refs；integration 与 feedback 保留输入 ID、state version、model hashes。

已有 `test_limit_is_raw_observation_and_later_recursion_consumes_exact_failure` 比较旧 raw failure 与后续输入的完整内容、消费的 limit ID；`test_process_slot_failure_preserves_all_legacy_lineage_no_forced_retirement` 检查旧过程不被覆盖。行为 JSON 的 `audited_actions[*].resolved_history` 可解析 integration→partial→experience→frames/relation refs，不能因为解析成功就把其行为内容算内生。

精确限制：[formal_l0.py:246](individual/formal_l0.py#L246) evidence_window 满时不再把新 ref 存进 outcome，但 evidence_count 已增加；完整 journal 仍有 experience/partial/integration，不等于删除旧日志。当前材料没有一个像 GSC closure 那样逐个断言所有候选关系的全部直接支持/输入根完整性的 oracle；也不能以 model hash/source 标签替代该核对。因此是有来源链子证据的 PARTIAL，**不是断言 journal lineage 已丢失**。

### C3 Organization — FAIL

实际写入仅是固定 root 的 relation row、outcome 集合、计数和有界 refs。[formal_l0.py:256](individual/formal_l0.py#L256) integration 只汇报这些操作；这不是因为 `organization_changed=False` 标签才 FAIL，而是创建/更新代码没有生产组织间新协调关系、新的组织依赖表达或新的处理组织方法。

反馈的 `next_relation_ref=root`（[第 271 行](individual/formal_l0.py#L271)）是固定地址生成规则；process 的问题固定为 temporal_relation_evaluation。读取内容变了，但问题/整合/读表组织仍保持同一模板。

反例断言：`test_full_memory_rejects_writes_and_preserves_old_records_no_eviction_compression_or_spawn` 明确排除 split/merge/remove 等操作；`test_one_process_repeats_and_previous_result_changes_later_processing_without_branching` 检查同一 process 重复发布、单一 L0。这里不是说没有关系，而是没有超出上述记录组织的独立新组织证据。原 schema 内新实例不自动等于 C3。

### C4 Causal efficacy — PASS（仅关系记忆→后续读取）

**实际执行链：** relation 写入 → feedback.next_relation_ref → 下一次 [formal_l0.py:195](individual/formal_l0.py#L195) `internal.relations.get(reference)` → `expected_outcomes` → partial.processing 的预测/读取字段。指针引用和被引用表内容都确实被读取，不是仅贴 provenance ID。

**反事实控制：** [test_formal_l0.py:117](tests/test_formal_l0.py#L117) 保留原状态其他内容，仅在 detached copy 擦除 relations，使用同一次观察和版本；实际 `read_succeeded` 从 true 变 false，`expected_outcomes` 不同。

**已有精确值：** 行为 JSON `ablation` 保持 frame/bootstrap/body/caps/feedback reference 不变。同一 requested_relation_ref `U-0294313806f11063b38a:-1`，擦除前读出 `[U-ee9cd61aee438f8f69d4, U-4f53cda18c2baa0c0354]`，擦除后读失败且列表为空。其检验代码是 [debug/behavioral_validation.py:33](debug/behavioral_validation.py#L33) `ablation`，对 `advance` 的实际 partial 字段比较，不仅比较命令。

**路径/可形成结构：** 有 reference 但读失败会进入 [formal_l0.py:199](individual/formal_l0.py#L199) failure 分支，生产资源读失败材料；源码可以定位这个分支影响。该擦除测试直接验证的是 read/expected，而非所有后续组织。新 relation 的写入仍按固定 root/outcome 规则；sample gap、容量和模板约束未改变。

**输出范围：** JSON `action_changed=false`，两个实际 formal 命令均 code=46、parameters={}；[formal_l0.py:296](individual/formal_l0.py#L296) sampler 不读关系来定动作。故这里的 PASS 是关系记忆实例的有限内部处理效力，不是“新组织方式”、内生行为或 C3+C4 联合通过。最终命令相同并不取消实际读取变化。

### C5 Non-prescription — FAIL

[formal_l0.py:296](individual/formal_l0.py#L296) sampler 使用固定 LCG，再 `codes[after % len(codes)]` 选择动作；[action_space.py:86](individual/action_space.py#L86) `choose` 用同类逻辑选择参数/target。[core.py:217](individual/core.py#L217) 当前 formal 路径实际调用 sampler 和 binder，不是 unused legacy 函数。

动作可用域/合法类型是能力边界，但从域中选一个 code、block_ref、entity_ref 等是外部决策；注册为 INITIAL_EXTERNAL_POLICY 不使其内生。`test_formal_path_never_calls_old_adaptation_engine_or_action_scoring` 只证明未调用旧 scoring，不证明 selector 不存在；`test_action_sampler_ignores_novelty_and_attempts_and_is_not_claimed_internal` 反而断言有无这些历史差异都给出同样选择。

其他固定贡献分别说明：pending_actions[-1] 是记录最近实际动作的时间关联约定；next_relation_ref=root 是通用读址机制，本身不等于替 A 选择行为答案。condition_channels 容量不足时按已有 sensor 序列取前 N 个 context，容量上限与固定输入截取规则需区分：前者限制可容纳多少，后者外部规定保留哪些，不是 A 学会的 priority。这些均不是自主问题/关联组织形成的证据。没有发现 reward 最大化代码；不因缺 reward 就忽略已实际执行的动作/目标 selector。资源失败拒绝写入没有 fallback，不能掩盖实际动作采样。

## 3. GSC-0

### C1 Novelty — PASS（新结构关系/Composite 实例）

[engine.py:282](experimental/gsc0/engine.py#L282) 生成 Eq 闭包、别名 Bind、端口 Bind 与 Conflict；[第 420 行](experimental/gsc0/engine.py#L420) 构造此前不存在的 connected leaf set。R4 是组合键，不是新业务 Relation。

`test_generation` 断言初始 closure 不含 R4、当前 COMPLETE closure 含 R4；`test_history_ablation` 删除 R2 并重建，`test_difference_ablation` 分别去掉 D1/D2。已有 JSON 记录 R4.present_before_difference=false，members 为 R1/R2/R3/Bind(X,3)，input_roots 为 R1/R2/R3/D1/D2。源材料值 3 是 fixture 给定，不是新 primitive value。

### C2 Provenance — PASS（有限 COMPLETE fixture）

[engine.py:69](experimental/gsc0/engine.py#L69) direct_supports 合并显式支持和无损 COMPOSE 索引；[第 74 行](experimental/gsc0/engine.py#L74) root_witnesses 查有限根；[第 126 行](experimental/gsc0/engine.py#L126) for_conclusion 枚举所有合法 operand/witness 支持，非 first proof。

`test_all_derived_facts_have_finite_root_witness`、`test_all_immediate_basic_rule_supports` 检查根和普通规则饱和。独立显式 proof graph oracle（[tests.py:152](experimental/gsc0/tests.py#L152)）比较小域所有 COMPOSE 支持及 edge count，connected-subset union oracle 检查组织支持无漏项。已有 R4 记录含 138 种直接支持和上述五个输入根。

限制：大图全部支持用索引表示，oracle 是小域；不是无限 proof-tree 枚举、任意未来输入的实测保证或 incomplete 的完整来源结论。消融从 seeds 重建，没有保留失去根的旧派生对象。

### C3 Organization — PARTIAL

[model.py:127](experimental/gsc0/model.py#L127) Composite flatten 为 leaf-key set；[engine.py:122](experimental/gsc0/engine.py#L122) shared 保留全部现成端口的 Eq witnesses。R1/R2 经 Y/X、R2/R3 经 B 的连接组织有可追踪关系，不是毫无组织信息的 UUID 包壳。

但生成的新对象内容仍是连通支持集合与既有 incidence 证据；没有由 Composite 自身产生的新组织内关系或处理约束。R4/K12/K123 的区别是组合实例，不是解释器的新组织方式。[tests.py:199](experimental/gsc0/tests.py#L199) 验证 flat/canonical/shared，不能证明相同成员内部组织重构。

R2 或 equality 消融使组合不成立，证明成员/现成连接对组合作用；不能因此把一份 connected set 直接升级为完整 C3 PASS。部分组织表达成立，完整新组织/新组织方式未证明。

### C4 Causal efficacy — PARTIAL

**实际有效的叶级链：** D1:Bind(Y,3) + D2:Eq(Y,X) → [engine.py:300](experimental/gsc0/engine.py#L300) Bind(X,3) → PROP-PORT 的 PortBind(R2,0,X,3)；Eq 还进入 [第 379 行](experimental/gsc0/engine.py#L379) eqs 集，决定 Shared witnesses、adjacency 和连通组合的可形成范围。这是计算执行依赖，不只是给 R4 附来源 ID。

**已有消融：** 去 D1 时 Bind(X,3) 无输入来源；去 D2 时 X/Y 无桥接；去 R2 时失去 X/B 的关系材料。这些反事实测试重建完整闭包并断言指定 R4 不再存在。冲突 fixture 还验证所有值传播至所有端口、Conflict 继续参与组合；不能只拿最后一个 R4 布尔值作因果证据。

**Composite 本身的消费者限制：** `Engine.consequences` 只读取 Node/Eq/Binding/Relation，不将 Composite 用作新 Bind/Eq/问题生成前提。[engine.py:400](experimental/gsc0/engine.py#L400) 读取已有 Composite members 更新 support masks；COMPOSE lineage 允许 K12 等作为更大组合的支持。但执行算法按 leaf adjacency 穷尽连通子集；它不是先读 K12 的“组织策略”再决定怎么处理。

**缺失的干预证据：** 原测试消融删除的是 root 材料 R2/D1/D2，未在相同 leaves/eqs 下单独移除 R4 的组织内容来验证后续非审计读取变化。只删包装后重算会如何，是代码路径可以讨论的静态性质，不是已有实测消融。新组合进入其他 COMPOSE 支持，支持图/索引确有读取；这不证明其组织身份独立改变传播规律。

**输出范围：** 没有 runtime/action consumer，没有在新组织驱动下形成新问题/组织方式的测试。故叶关系图的真实效力成立，但主被测 Composite 的组织级 C4 仅 PARTIAL；不能将逻辑 provenance 图中的 parent proof 直接当作新的决策执行链。

### C5 Non-prescription — PASS（通用 closure，不是自主输入作者权）

实际 rules 为固定通用 ALIGN/PROP/CONFLICT 与全连通 COMPOSE；同条件下全部合法对象/支持保留。[engine.py:195](experimental/gsc0/engine.py#L195) queue order 影响遍历，不选择答案；[model.py:144](experimental/gsc0/model.py#L144) sorted set 只 canonicalize。`test_seed_queue_rule_order`、idempotence、conflict preservation、no_semantic_shortcut、resource limit tests 检查没有 first proof、值择一或 top-k partial success。

R4 是测试的审计别名，不是 runtime 选择出的答案。fixture 人工给 Bind(Y,3) 和 Eq(Y,X)，对应输入来源明确；这是此有限内部身份/绑定材料的条件，**不证明系统自行发现 equality**。闭包没有规定“选 R4”“遇某 Minecraft observation 生成某动作”或固定 internal→outward target map，C5 PASS 限于这个实际范围。

合法 generic identity facts 与已指定 outward correspondence 应区分。把所有外部输入都叫 policy 会使任何环境输入都不能使用；把任意已规定目标边叫 observation 则会洗掉 routing。下一节 Eq(h,p) 的用途不同，必须另判。

## 4. GSC-1

### C1 Novelty — PASS（新端口绑定与 tuple 实例）

[fixtures.py:25](experimental/gsc1/fixtures.py#L25) 两个历史只有 h0/h1/h2 的独立 Bind；[第 29 行](experimental/gsc1/fixtures.py#L29) 输入 Eq(h_i,p_i)。GSC-0 先派生 p_i 的新 Bind；[grounding.py:54](experimental/gsc1/grounding.py#L54) 将三条 singleton 包成新的 GroundedOutwardStructure。

`test_tuples_not_present_in_history` 检查初始 closure 的输出端口均 UNRESOLVED；`test_two_complete_unique_outputs` 检查两个 tuple 的 exact 值。已有 JSON 的 A/B 输出分别为 `(A0,B0,C0)`、`(A1,B0,C1)`，initial grounding 均无完整 outward。

新的是端口关联实例与完整包装，不是 primitive values，也不是角色/路由的自主生产。

### C2 Provenance — PASS（已声明对应条件内）

[grounding.py:39](experimental/gsc1/grounding.py#L39) 保存每条 Bind 的全部 direct_supports 和 input_roots，完整结果附 closure digest；[tests.py:145](experimental/gsc1/tests.py#L145) 逐端口核对支持集合、根和 PROP-ALIAS，并检查所有派生对象有限根。

已有 JSON A.p0 的 exact support 是 `PROP-ALIAS(Bind(h0,A0), Eq(h0,p0))`，根含 H0/D0；另有 Bind(p0,A0)+Eq(p0,p0) 的循环直接支持，不能替代根生产见证。去 Hi/Di 的反事实重建后相应端口缺失。包装按每个 singleton 的全部证据说明来源，而不是择一证明。

限制：包装不把组织存回 closure，没有新的组织生产图；closure digest 指向上游有限图，不是整个大图已逐项导出到 JSON。来源可追踪且能辨认外部 D0 routing，C2 PASS 不等于 C5 PASS。

### C3 Organization — FAIL（自身新增 tuple 的组织主张）

[model.py:43](experimental/gsc1/model.py#L43) key = 固定 schema_key + fields；checker 的每个 required port 按预声明 name/variable/type 扫描普通 Bind，再解包 singleton。它不生产端口间新的依赖、角色或组织内约束；字段 correspondence 在 fixture/schema 已给定。

`test_generated_composites_and_all_saturated_supports` 确认上游还形成由 Hi/Di/新 Bind 组成的 Composite。这是 GSC-0 的组合子证据，不是 tuple 自身的新组织规律。上游的 C3 PARTIAL 不能自动让 consumer 的固定 schema 包装通过。

历史/当前输入消融时 tuple 消失，证明填入材料必要，不证明字段组织本身是内生形成。故新 tuple 的 C3 FAIL；不是否定其新颖性或 singleton 的正确性。

### C4 Causal efficacy — PARTIAL

**实际路径：** history Bind + 相同 CurrentInput Eq → GSC-0 新 p Bind → [grounding.py:31](experimental/gsc1/grounding.py#L31) exact Variable lookup → 值数 0/1/>=2 → 完整/缺失/冲突状态和新 tuple。checker 真读 closure 里的 Bind，不从 expected tuple 常量填答案。

**反事实：** [tests.py:47](experimental/gsc1/tests.py#L47) paired histories 对比同一个 current input、同 condition，并交换历史复现另一结果；[第 61 行](experimental/gsc1/tests.py#L61) 两个历史逐 Hi 消融，[第 71 行](experimental/gsc1/tests.py#L71) 逐 Di 消融，对应 port.values 为空；冲突测试保留 B0/B1。dependency 路径上实际材料与 exact binding 集改变，完整 tuple 的可形成性改变，绝非只有最终字符串不同。

**依赖不变部分：** A/B 仍沿同一 h_i→p_i routing 及同样 checker 流程；只有历史值/对应 Bind keys 与 roots 支持内容不同。不能把值改变叫路由/组织方式改变。历史/输入消融能改变查到的绑定和 packaging 条件，但没有替换已生成 tuple 的独立消费干预。

**主新对象的后续读取：** [tests.py:179](experimental/gsc1/tests.py#L179) 明确 outward 不插入 GSC-0 facts；[第 171 行](experimental/gsc1/tests.py#L171) 重复调用 checker 只读原 closure，不缓存旧 tuple。没有下一轮从 GroundedOutwardStructure 读取组织关系的路径；idempotence 是重算原绑定，不是 tuple 驱动后续递归。

**输出范围：** 既有 record 可证明数据 grounding 的实际作用，不能证明完整 tuple 自身的组织级因果效力，更无 body/action 效力。C4 因真实绑定读取子证据而 PARTIAL，不以两个不同 tuple 直接给 PASS。

### C5 Non-prescription — FAIL（明确的 external structural routing）

具体生产边在 [fixtures.py:29](experimental/gsc1/fixtures.py#L29)：`zip(sources,outputs)` 提供 Eq(h0,p0)、Eq(h1,p1)、Eq(h2,p2)。这不是从内部关系/Composite 推导出的 target correspondence。D0/D1/D2 根因此是外部连接作者的直接证据。

此 Eq 不是运行中的值 selector：checker 不从两个绑定里选一个，conflict/missing 时 outward=None。它仍提前指定 internal→outward 的目的地，所以 C5 FAIL。允许 generic equality/传播规则，不等于允许把具体 routing 的实例作者权洗成内部。

`test_no_selector_default_filling_or_execution_in_checker` 仅审计 checker，不能涵盖 fixture 的 fixed mapping；`test_current_input_ablation_each_port_both_histories` 反而证明三条 external Eq 是当前成功的必要输入。schema 三种 type 可作为合法类型条件，但不能把每对唯一 compatible 的设计当成新连接的证明。

## 5. 五层结果的独立对照

| 层次 | FormalL0 | GSC-0 | GSC-1 |
|---|---|---|---|
| 新记录 | 事件、experience/partial ID、计数 | input/proof/witness 记录 | grounding/evidence 记录 |
| 新关系实例 | temporal root/outcome 内容新增；只主张时间关联 | Eq/Bind/PortBind/Conflict 实例新增 | 在已给 routing 下新增 p Bind，来自 GSC-0 |
| 新 Composite/包装 | 固定 relation row 的聚合，不是连通 Composite | 新 connected support set，有原 incidence witnesses | 固定 outward schema 的新 tuple；上游 Composite 仍是 GSC-0 |
| 新的因果有效组织 | 关系记忆有实读效力；完整组织形成未成立 | 叶图有效，Composite 主对象完整组织效力未成立 | 绑定读取有效，tuple 未作为后续组织被消费 |
| 新的组织方式 | 未见生成路径；固定 temporal evaluator/lookup | 未见生成路径；固定 closure/flat composition | 未见生成路径；固定 routing 与 checker |

不能把前两行等同第四/五行，也不能把“来源可追踪”当成“来源是内部”。本表不审计任何其他机制。

## 6. 边界与评分限制

静态读取与已有具体记录可以支持限定裁定，不会替代未执行的组织级干预；缺口已经在各项指出。FormalL0 的原始实验 JSON 来自较早输入 commit，当前实际函数与其 read/sampler/binder 路径已逐项核对；不据旧整体失败标签直接给本表结果。

本轮没有读取或变更 canonical SQLite，没有新测试数据/运行记录。提交前后核对读取基线的 135 个既有 tracked 文件字节 hash；只有本审计和标准两个文档新增。旧 prototype passed 状态不因新的工作标准被偷偷改写。

## 7. 三机制 × 五标准总矩阵

| 机制 | C1 Novelty | C2 Provenance | C3 Organization | C4 Causal efficacy | C5 Non-prescription |
|---|---|---|---|---|---|
| FormalL0 | PASS | PARTIAL | FAIL | PASS | FAIL |
| GSC-0 | PASS | PASS | PARTIAL | PARTIAL | PASS |
| GSC-1 | PASS | PASS | FAIL | PARTIAL | FAIL |

按 CO-WAC-1 的顺序和“所有三机制均尚未完整 PASS”的定义，**共同最早未解决的标准是 C3 Organization**。C1 三者在实例范围 PASS；C2 FormalL0 仍 PARTIAL，但另两者在有限来源范围 PASS，所以 C2 不是共同列。C3 的 FAIL/PARTIAL 是本轮工作证据裁定，不是 Perfect Recursion 普遍公理或理论不可能性结论。此处停止，不据矩阵提出解决方案。
