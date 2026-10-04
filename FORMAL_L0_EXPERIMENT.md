# BECA-V0 正式 L0 实验同步与改造报告

基准：iking-i/beca-architecture v0.8，提交 `867e1f192f7f21298450a553a4a733ec8f15a999`。本轮只改本地实验实现与实验文档，未改核心理论，未发布远端提交，未运行 Minecraft 长时间实验。

本阶段允许不分化，不要求 upward recursion。唯一 active recursive layer 是 L0。`Continuity(A) != 0` 仍是唯一理论级个体定义约束，下面的初始化及外部资源配置都不是新增理论约束。

## 1. 当前结果与不能宣称的结果

代码与测试已经验证：单过程的前次结果进入后次关系读取；容量写入真实被拒绝；原始后果进入观察与后续递归；关系满后，后次递归实际无法读取此前试图保留的关系。没有自动扩容、删除最旧、压缩、分化或升层。

当前**尚未验证 architecture-limit recognition**。数值解释器只能积累关系证据、核对预测与传回失败，没有通用的组织层问题表示生成器。它不会自动产生“当前组织方式构成限制”的结论。审计输出 recognition_status=not_observed，formal_stage_goal_observed=false。这是能力边界，不应靠长期运行或人工 metadata 宣布补齐。

## 2. 修改文件与目的

| 文件 | 修改目的 |
| --- | --- |
| individual/formal_l0.py（新增） | 单过程 L0 解释器；前次反馈驱动后次关系读取；容量拒绝写入、失败重新输入；显式初始动作采样 |
| individual/experiment.json（新增） | 外部固定容量配置；进程8、活动单元64、关系96、保留观察6、证据引用4、条件通道16、每关系结果64 |
| individual/core.py | 正常入口切换 formal_l0；保留身体能力与连续事务；显式旧策略调试入口；动作外部策略事件；正式历史禁止回到旧适应引擎 |
| individual/internal_state.py | 增加 l0_state，保存持久过程、反馈、物理配置及输入寄存器；不改旧历史 |
| individual/observation.py | ObservationFrame 增加 internal_observations，容纳原始内部操作后果 |
| individual/policies.py | 登记单过程初始化与动作采样来源；区分登记存在和正式路径启用 |
| individual/action_space.py | 参数采样的随机源选择与正式路径来源保持一致；不改游戏能力 |
| individual/l0_audit.py（新增） | 六类证据、容量后果重入、绑定极限证据、候选来源检查，独立于信息整合 |
| individual/experiment_audit.py | 区分历史/正式审计；去除 real_upward 等错误命名；历史闭环不能通过本阶段 |
| individual/policy_audit.py | 审计当前启用/禁用来源；没有参数调整不再被当成来源审计失败 |
| supervisor/supervisor.py、limits.yaml | 转发正式/调试配置；固定资源监控；增加生命周期数据库族64GiB阈值；停止判据要求完整阶段证据 |
| debug/run_fixture.py | 旧数值夹具明确使用旧策略调试路径 |
| debug/validate_formal_l0.py（新增） | 12次观察的短时数值验证，独立 TEST_ONLY 文件夹，不切换当前主线，不连接游戏 |
| tests/test_formal_l0.py（新增）、test_structure.py、test_supervisor.py | 单过程递归、无固定适应、容量后果、反事实读取、审计负例、资源停止及旧回归 |
| README.md、POLICY_BOUNDARIES.md、VALIDATION_STAGE3.md | 当前目标与旧证据分开，旧信息整合不得解释为升层 |
| EXPERIMENTAL_VALIDATION.md、MINIMAL_INDIVIDUAL_MODEL.md、EXPERIMENTAL_IMPLEMENTATION_BOUNDARY.md、TESTABLE_PREDICTIONS.md（本地同步） | 保留仓库v0.8内容，增加本阶段范围与能力边界；远端主分支未修改 |

## 3. 正式路径审计：固定策略、机制与可变结构

下表来自执行函数，非 README 名称推断。旧策略的实现保留，生产调用已经隔离到 StructuralEngine，仅显式 legacy_policy_debug 可运行。

| 规则或内容 | 实际位置 | 分类 | 正式路径状态 |
| --- | --- | --- | --- |
| 新结果增加数量（floor3、increment1） | integration.integrate；generation.quantity | EXTERNAL_FIXED_POLICY | 禁用，正式路径不调用 integrate |
| 稳定阈值3→数量1及停止 | integration.integrate；generation.stability、recursion.retirement | EXTERNAL_FIXED_POLICY | 禁用 |
| 分辨率固定减半、最小1e-5 | integration.integrate；generation.resolution | EXTERNAL_FIXED_POLICY | 禁用 |
| 压力≥0.8→预算减半 | recursion.generate_processes；recursion.allocation | EXTERNAL_FIXED_POLICY | 禁用；压力只保留为外部测量 |
| 过程槽满→终止最旧信息过程 | recursion.generate_processes | EXTERNAL_FIXED_POLICY | 禁用；槽满拒绝创建，不终止已有过程 |
| 单元/关系满→淘汰最旧；结果满→整关系归档 | structure.StructuralEngine.advance、integration.integrate | EXTERNAL_FIXED_POLICY | 禁用；拒绝新记录，原记录保留 |
| 固定滑动窗口、删除最早条件桶/尝试次数 | structure.advance、RecursiveProcess.publish_partial_result、actions.select_action | EXTERNAL_FIXED_POLICY | 禁用；正式保留记忆不滚动，不调用旧发布或评分器 |
| 强度+1及衰减0.98 | structure.StructuralEngine.advance；structure.strength | EXTERNAL_FIXED_POLICY | 禁用；证据次数记录不等于该强弱适应策略 |
| 少尝试/未解决加动作分数 | actions.select_action；action.scoring | EXTERNAL_FIXED_POLICY | 禁用，无 novelty/exploration bonus |
| 最大评分后LCG平分选择 | actions.select_action；action.selection | EXTERNAL_FIXED_POLICY | 禁用，正式采样不读 scores/attempts/unresolved |
| 新问题生成门控、通道候选优先、停滞淘汰、同签名合并 | recursion.generate_processes/advance_processes、integration.integrate | EXTERNAL_FIXED_POLICY | 禁用，单一过程持续处理流，不按这些规则生成或终止 |
| 初始化一个过程 | formal_l0.advance；formal.process_initialization | EXTERNAL_FIXED_POLICY | 保留，明确是实验初始化；之后不自动改变数量 |
| 从当前可用动作中固定伪随机采样 | formal_l0.select_uniform_action；formal.action_sampling | EXTERNAL_FIXED_POLICY | 保留，缺少内部动作策略时的初始采样，不冒称自主策略 |
| 数值/引用参数域采样 | action_space.bind_parameters；action.parameter_binding | EXTERNAL_FIXED_POLICY | 保留，来源单独记录，不注入攻略/配方/最佳工具答案 |
| 数值编码、固定传感器序列与读取宽度 | FrameEncoder、FormalL0Engine.advance | EXTERNAL_FIXED_MECHANISM | 保留，表示能力本身有限且布局固定；不称作内部形成 |
| 单过程反复执行、前次反馈决定实际关系读取 | FormalL0Engine.advance | EXTERNAL_FIXED_MECHANISM | 保留；执行算法作者是程序员，被读取的数据因经历变化 |
| 历史形成的关系、结果证据及后次预期 | InternalState.relations、l0_state.feedback | INTERNAL_VARIABLE_STRUCTURE | 保留且可反事实检查；当前只证明证据/数据变化，不证明组织方式变化 |
| 活动单元、关系、保留记录、证据引用、通道、过程槽上限 | FormalLimits；experiment.json | ENVIRONMENT_CONSTRAINT | 固定只读运行配置；超限真实拒绝，无适应答案 |
| RAM/CPU/生命周期数据库族阈值与人工停止 | Supervisor._collect/_enforce；limits.yaml | ENVIRONMENT_CONSTRAINT | A没有修改接口；超限外部停止，不扩大预算或删除历史 |
| SQLite事务、单写入租约、连续版本、Bridge动作执行器 | EventStore、ExperimentLease、MinecraftBridge | EXTERNAL_FIXED_MECHANISM | 保留 |

目前正式路径仍保留的初始行为策略只有：单过程初始化、动作伪随机采样、参数域采样。策略类别沿用 Registry 的 INITIAL_EXTERNAL_POLICY；审计事实使用 EXTERNAL_FIXED_POLICY。二者都表示外部作者，不能因为参数在 AState 内就改称内部形成。

generation_parameters中的旧default_quantity、pattern_quantities、condition_resolution等作为兼容/历史字段保留，值可能仍为旧初始化值；formal_l0不读取它们决定数量、分辨率或适应行为。实际k_actual从新正式过程日志读取，初始化为1，之后不因新结果改变。首次登记策略列表也可能包括已禁用的旧策略；不能把“登记了”当成“仍驱动正式实验”。

## 4. 真实 current effective limit

主要选择**有限的关系记忆组织**：有固定记录槽，新的关系写入会被拒绝。前次整合仍返回这次尝试的关系引用；后次递归请求读取它时实际读不到，从而不能按原方式使用该信息。审计要求“先前容量拒绝该引用→后次真实读取失败”的证据，输出 behaviorally_binding_limit_observed；不把所有无关缓存满都自动当成有行为意义的极限。

其他可观察端口包括活动单元、保留观察、证据引用和条件通道。固定输入序列中只能同时读取N个条件值，多出的引用作为不足后果提供，不自动重排或扩容。

原始后果格式包含 limit_id、operation、used、capacity、requested、operation_performed=false、frame_id、source_state_version、object_refs、organization_ref、representation、source。后果代码包括 WRITE_FAILED_CAPACITY、RELATION_CAPACITY_REACHED、ACTIVE_MEMORY_LIMIT、PROCESS_SLOT_UNAVAILABLE、INFORMATION_NOT_SIMULTANEOUSLY_AVAILABLE。没有“建议压缩”“创建L1”等答案字段。

保留的历史记录不滚动删除。两个当前/前次输入寄存器是固定传感器承载，不充当偷偷滚动的保留记忆；替换输入信号与淘汰历史记录分开。固定一批输入反馈寄存器把刚产生的失败送入下一次输入，不需要取得新的记忆槽；更旧完整信息始终在 canonical SQLite 历史中。A 不自动无限读取审计历史来绕过活动记忆限制。

证据次数从初始化起就固定表示为计数，与有限证据引用槽分开；不是容量满后才改用计数，也不视作系统形成了新的压缩/记忆组织策略。引用写入失败不会被次数增加掩盖，仍记录原始失败。

N 是严格执行的逻辑记录槽上限，不是已经实现的操作系统硬RAM配额。Supervisor对CPU/RAM和数据库族磁盘使用进行采样、越界终止，可能存在采样间隔的超额，不等于容器/cgroup/Windows Job Object强制配额。当前没有新增OS沙箱；Bridge能力边界、外部控制权限保持原状。不存在 A 申请扩容、增加节点或修改资源配置的接口。

## 5. 执行链与真实审计样例

```text
环境数值观察 + 上轮原始操作后果
→ L0单过程读取前次反馈的关系引用
→ 核对可用证据/当前结果，输出partial
→ 同层整合尝试记忆写入
→ 保存关系证据及下一次反馈
→ 写入失败作为下一次输入
```

短时数值夹具：A-9c4c6d64-60ea-4c82-96a5-d2acd8eaac83，12次观察，A0→A16，1次过程创建、11次partial、11次信息整合、35次原始容量后果、10次后果重入。该数据不是Minecraft结果，也不是当前主线。

具体样例：A5尝试写第2个活动单元，used=1、capacity=1、requested=2，WRITE_FAILED_CAPACITY，limit_id=ba7c92ef-f8f9-4a26-aae5-ef52837e09c7；A6的实际partial输入引用了同一个完整后果。A5的整合返回关系引用U-02817f82dc0fe284ef19:-1，A6真实读取这个引用。另有关系容量拒绝与后次关系读取失败，可在报告的binding_limit_witnesses查到。

删除历史关系但保留相同代码和前次引用的隔离反事实测试，使后次read_succeeded从true变false、expected_outcomes改变。这证明历史数据影响后续实际处理，仍不证明适应策略由A形成。

完整记录保存在此夹具个体文件夹的数据库与reports/。新分析报告使用带时间名称，原报告保留。

## 6. 审计语义与成功判据

六类独立事实：WITHIN_LAYER_RECURSION、CURRENT_LIMIT_ENCOUNTER、LIMIT_FEEDBACK_REENTERED_RECURSION、ARCHITECTURE_LIMIT_RECOGNITION_CANDIDATE、EXTERNAL_POLICY_EFFECT、INTERNAL_VARIABLE_STRUCTURE_CHANGE。

closed_loop_observed只表示已观察到同层结果反馈。formal_stage_goal_observed还要求行为上绑定的真实极限、后果重入及有独立来源证据的识别候选。候选也只是待复核候选，不等于已发现因果定律或向上递归。

识别候选必须有由递归输出产生的新问题表示，明确以当前组织方式为对象，有实际历史证据及评估来源，并排除固定策略作者。原始失败、计数、人工标签、事件编号和“external_policy_excluded=true”字符串本身都不能证明来源。目前没有生成这种表示的程序，故不会有通过结论。

明确不算成功：多进程、记录增加、structure_revision增加、信息回传、关系次数增加、固定参数调整、物理扩容、程序员改架构、人工命名L1。upward_recursion_observed始终false；本阶段不实施升层检测，不能从此字段推断对未来机制的理论否定。

## 7. 运行与当前缺口

本轮未启动Minecraft，未改变当前主线选择，未删除任何已有生命周期历史。继续同一个A用main.py；旧已满状态不会被自动清空或淘汰腾位。如果明确从零测试另一个A，用individual.lifetime initialize，得到另一个身份文件夹，不能称为原A继续。

```powershell
.\.venv\Scripts\python.exe main.py
.\.venv\Scripts\python.exe -m individual.experiment_audit --session-id latest --sample
.\.venv\Scripts\python.exe -m individual.policy_audit
```

external verification只是实验者的停止工具；当前缺候选生成能力，不建议靠--verify-loop长时间等待宣称已识别。独立旧策略调试路径是--legacy-policy-debug；已经有formal_l0历史的A拒绝改用旧适应引擎。

仍缺：可由经历形成的通用组织层问题表示与假设生成/评估机制。它必须能把任意组织对象纳入问题，不能预写“limit→recognize_architecture”。补齐前，本实验可验证极限反馈基础，不能完整检验architecture-limit recognition是否能自然发生。

未来真正L0→L1还需：让当前层组织成为可执行的递归对象、通用组织构造与试验/采用能力、组织改变的因果评估、更高层生成与低层持续运行、对新层再次应用相同能力。均未在本轮实现，不预设limit→L1或固定拓扑答案。

## 8. 测试与实际范围

新增正式阶段测试覆盖：单过程连续反馈、无分化合法、新结果/压力不增加数量、容量拒绝且原记录不变、原始后果观察与后次引用、历史反事实读取、旧调用路径不执行、动作来源单列、信息整合/百万次revision不算升层或识别、不可变容量、旧槽占满不强制淘汰、旧策略不能通过正式阶段、正式历史不能偷偷回到旧适应引擎。Supervisor另测磁盘阈值停止而不删历史或扩容。

Python全套90项、Node身体接口30项通过；新增正式L0测试12项已包含在Python全套中。两项Node本机网络测试首次被沙箱阻止，允许本机端口访问后全套重跑通过。短时数值审计得到：层内递归=true、真实容量后果=true、行为上绑定的关系极限=true、后果重入=true、内部关系证据变化=true、外部初始化影响=true、识别候选=false、向上递归=false、整个阶段通过=false。
