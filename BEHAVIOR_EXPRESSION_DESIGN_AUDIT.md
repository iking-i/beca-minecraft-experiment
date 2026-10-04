# Behavior Expression Design Audit

日期：2026-10-04。范围：机制设计审计；没有实现候选，没有运行实验，没有修改历史。

## 1. 基准与结论

读取并核对的实验仓库 HEAD：`92ffa42b796afeeb6686a1093c5e7d8f799e6aa2`（`iking-i/beca-minecraft-experiment`）。理论仓库 HEAD：`89a56ad7ce236adfcb52b13d3e6fe7014ff88ddd`（`iking-i/beca-architecture`）。本文件的提交是上述实验基准的文档增量，不是新的实现验收。

理论依据是该提交的 [SPEC.md v0.9](https://github.com/iking-i/beca-architecture/blob/89a56ad7ce236adfcb52b13d3e6fe7014ff88ddd/SPEC.md) 和 [EXPERIMENTAL_IMPLEMENTATION_BOUNDARY.md v0.9](https://github.com/iking-i/beca-architecture/blob/89a56ad7ce236adfcb52b13d3e6fe7014ff88ddd/EXPERIMENTAL_IMPLEMENTATION_BOUNDARY.md)。不以历史 v0.8 定义覆盖 v0.9：`Continuity(A) != 0` 是本个体实验的延续条件，不是整个 Perfect Recursion 理论的普遍不变量；因果连续与主体身份也不能直接等同。

**NO CLEAN IMPLEMENTATION YET。** 当前没有可直接接入正式路径、同时闭合表达内容、所有必要参数和身体端口控制作者权的方案。下面的候选是待审计设计，不是已形成的内部能力。不证明这样的机制不可能，只确认现有生成机制和证据不足。

- `WORLD_ENTRY_FREEZE = passed`：保留原验收及其范围，不把它解释为行为作者权通过。
- `BEHAVIORAL_CAUSAL_CLOSURE = failed`：保留原结论，不通过设计文本改变它。
- 推荐继续研究“内部控制图携带完整表达”，但**不推荐现在接入它**；表达生成与控制关系生成仍未解决。

完整阅读范围：`BEHAVIORAL_CAUSAL_CLOSURE.md/.json`；`individual/formal_l0.py`、`core.py`、`internal_state.py`、`action_space.py`、`decision_provenance.py`、`policies.py`、`structure.py`、`formal_boundary.py`；`POLICY_BOUNDARIES.md`、`FORMAL_L0_EXPERIMENT.md`、本仓库 `EXPERIMENTAL_IMPLEMENTATION_BOUNDARY.md`、`EXPERIMENTAL_VALIDATION.md`；上述两份当前理论文件。判断基于执行路径与已有小型证据，不仅基于注释。

## 2. 当前代码究竟缺少什么

以下行号均针对上述实验基准；本轮没有变动它们。

| 位置 | 实际操作及字段 | 已有能力与缺口 |
|---|---|---|
| `individual/core.py:115`，`ACore.accept_observation` | 编码输入，调用 `FormalL0Engine.advance`，持久化状态变化 | 环境输入确实进入同一个 A 的状态链；没有调用行为表达生成器 |
| `individual/structure.py:16`，`pattern_id`；`formal_l0.py:117` 起 | 差异形成模式标签、units | 模式 hash 是标识，不是动作选择；不能改作行为 RNG 并声称内部作者权 |
| `individual/formal_l0.py:149` 起，`advance` | 创建一个 `temporal_relation_evaluation` process | 固定解释器提供过程；过程目前只做时间关联处理 |
| `individual/formal_l0.py:172–192` | experience 保存 antecedent、执行过的 action_code、`action_parameters`、前后 frame、context；`causality=temporal_association_only` | 过去动作及参数是材料，不是未来执行意图；记录的先后关系不证明动作导致结果 |
| `individual/formal_l0.py:196–217` | 读取 `feedback.next_relation_ref` 指向的 relation，产生 expected/matched/unexpected 等 partial 数据 | 历史改变后续递归读取；没有生产未来动作项或控制边 |
| `individual/formal_l0.py:223–268` | 更新 relation 的 outcomes、evidence_count、有限 evidence_refs；integration 操作为 `record_distinct_experience`；`organization_changed=false` | 当前 relation 不保留完整可执行参数绑定，integration 不构造未来表达或端口控制关系 |
| `individual/formal_l0.py:270–278` | 写入下次读哪一个 relation 的 feedback | 这是递归读取的反馈指针；不是“哪个行为获得身体端口”的内部关系 |
| `individual/core.py:209–229`，`execute_discrete_action` | 正式路径选 code，缺少参数时调用 binder，再调用 `formal_command` | 没有内部表达到身体端口的路径；显式传入 code 的测试调用不是 A 自己形成表达 |
| `individual/formal_l0.py:296–315`，`select_uniform_action` | LCG 更新 `random_state`；`codes[after % len(codes)]` | `formal.action_sampling` 仍是持续外部动作作者。pattern 仅写入元数据，relations 不决定结果 |
| `individual/action_space.py:75–152`，`bind_parameters` | `action.parameter_binding` 通过 LCG 及固定域取值形成参数 | 域是否合法与选择域中哪一个值是两件事；无语义名称也不等于没有外部选择策略 |
| `individual/action_space.py:155`，`formal_command` | code/parameters 机械封装为 `perform` RPC | 已有可复用的非语义传送部分；尚无内部作者的完整输入 |
| `individual/policies.py:190`，`validate_internal_proposal` | 检查来源标签和引用字段，返回 `activated=false`、`history_references_verified=false` | 不生成、不验证真实历史作者权、不激活政策；不是可借用的隐藏生成器 |
| `individual/decision_provenance.py:7`，`decision_authorship` | 来源标记检查 | 标签或 integration ID 不能替代实际消费内容的因果证据 |

已有数据足以提供部分原材料：units、relations、experiences、partials、feedback、process、integration、当前 opaque refs。但**足够记录过去不等于足够生成未来**。当前缺少的最小操作是：递归过程能够构造并改变一个完整的、面向未来端口的有类型项，包括 code、每个必要参数及其引用、以及决定该项获得端口的控制关系；integration 能保存这些对象而不自行赋予优先级。现在没有这类 producer，也没有其内容从历史产生的执行证据。

完整 append-only journal 是外部审计历史，不是 A 可无限访问的记忆。不能把审计器的数据库全读能力默默借给候选生成器。

### 已有反事实证据的准确范围

`BEHAVIORAL_CAUSAL_CLOSURE.json` 与配套报告记录两个独立 TEST_ONLY 历史：坐标偏移 `[0,1,0,1,0]` 与 `[0,2,4,6,0]`，随后相同当前输入及相同 bootstrap。relation `U-ee9cd61aee438f8f69d4:-1` 的证据分别为 count 2 / 一个 outcome 与 count 3 / 两个 outcomes。两者正式动作仍为 `code=46, parameters={}`，外部随机状态均为 `0 → 1013904223`。

从分离副本移除 relations 后，下一次真正的 recursive read 由 `read_succeeded=true` 变为 false、expected_outcomes 变为空；动作及参数不变。32 个当时可用 code 的离线参数探针也全部相同，包括 code 16 的 slot 7、code 15 的 inventory_slot 36 / 相同 opaque reference_block / face 1。

实际请求为 A9 / event 85，执行 A10 / event 88，新观察 A11 / event 90。这是测试载体，不是真实 Minecraft 新验收。证据支持“历史影响内部结构及递归读取”，不支持“内部结构决定未来身体行为”。本轮不重跑这些测试，不生成新数据。

## 3. 设计约束与每条边的作者权记法

用以下分类标注图的**具体操作**，不把整条链笼统标为 internal：

- **M = EXTERNAL_FIXED_MECHANISM**：定义语法、类型、机械求值/编译、原样传输、provenance、有限存储。固定解释器并不必然是行为策略；关键在于它是否替 A 填写选择内容。
- **E = ENVIRONMENT_CONSTRAINT**：已有身体合法域、引用寿命、端口物理串行性、资源容量。约束只规定可行性，不从合法选项中挑答案。
- **P = EXTERNAL_FIXED_POLICY**：宿主规定历史匹配重放、概率偏好、优先级、下一动作、参数值或仲裁方向。
- **H = INTERNAL_VARIABLE_STRUCTURE**：内容由实际递归历史形成，并在后续执行中被实际读取且影响结果。存放在 InternalState 不构成此分类的证据。
- **H?**：候选需要形成但尚无 producer/证据的内部内容边。问号表示缺口，绝不是实际已验证的 H。
- **B/M**：任务允许的初始无语义 bootstrap variation；作为外部来源独立记录。若继续决定正式行为，本任务应按 P 审计，不能永久改名为 bootstrap。

合法域和 opaque refs 的验证属于 M/E；域内值的选择必须另给作者。类型错误、失效引用、缺参或端口冲突只能报告，不能自动补合法值、寻找替代目标或改为另一个动作。

“没有输出”不是 A 选择了等待或 NO_OP。不能把缺失表达补成 NO_OP 来伪造闭环，也不能借此改变冻结身体已有的输入持续/停止行为。人工 pause/terminate 的外部安全权限保持原边界。

## 4. 候选一：历史项投影与匹配重放（否定对照）

**分类：EXTERNAL_POLICY_CONTAMINATED。拒绝。** 它利用现有材料最容易接通端口，也正因此需要明确列出，而不是将“读取已有 relation”误认作干净解法。本候选不符合本任务的禁止项。

### 完整因果图与每条边

```text
bootstrap → 历史动作及全部参数                         [B/M；当前持续 sampler 为 P]
身体后果 → frame → experience/partial                 [E → M；观察内容是历史材料]
experience/partial → relation evidence                [M；形成内容 H]
当前 frame + relations → 匹配/最新/频次选中的历史项      [P：宿主决定匹配与仲裁]
选中历史项 → 复制 code 与参数的未来 expression           [P：宿主规定重放]
旧 refs → 当前 refs（若自动找替代对象）                  [P：宿主重绑定；禁止]
expression → 类型/域/引用检查                          [M/E]
唯一合法完整 expression → perform → 身体后果            [M → E]
身体后果 → 新 frame → 后续历史                          [M；不会洗掉上游 P]
```

| 必答项 | 审计回答 |
|---|---|
| 1. 表达是什么 | 有类型的 `{code, parameters, source_refs}`；完整复制 experience 的已执行命令。现有 relation 本身没有完整参数，必须访问受限可用的 experience 材料，不能无限读 journal |
| 2. 最初如何出现 | bootstrap 执行产生历史样本；第一条未来表达由外部“取过去项重放”规则制造，不是内部形成意图 |
| 3. 如何变化、内容来源 | 样本值来自真实经历，但选择哪个样本、何时重放由固定匹配/最近/频次规则决定；经历改变输出不等于作者权闭合 |
| 4. 如何到端口 | 外部匹配器选择历史项，外部复制器生成完整命令，机械发送 |
| 5. code 作者 | 历史原始 code 作者通常为外部 sampler；未来采用该 code 的作者仍是外部重放政策 |
| 6. 每个参数作者 | 值最初来自外部 binder；未来复制由外部政策。过期 refs 若宿主自动替换，又增加外部作者；不替换则只能拒绝 |
| 7. 固定了什么 | 存储/类型/发送是 M；匹配条件、样本优先级、重放映射是 P |
| 8. 历史形成什么 | 时间关联、样本、证据集合是真实 H；没有形成重放控制关系 |
| 9. 隐藏仲裁 | 同 antecedent 多 outcome、多 action、多同分项时，需要最新/频次/排列等规则；这些都是 P，而非“readout” |
| 10. 多表达谁获端口 | 宿主匹配器/排序器。只保留一个候选也只是把仲裁提前到记录或投影阶段 |
| 11. 是否失败 | 是。固定重放政策不可通过 provenance、内部字段或不使用语义名称消除 |

没有 reward 也会污染：匹配、频次和最近偏好自身就规定行为方向。把 evidence_count 变成概率，或把历史 hash 变成随机种子，同样不满足要求。重放项可以作为递归材料，但不能由宿主直接当未来命令。本方案可仍在 L0、可不改身体，但这些不能挽救行为作者权。

## 5. 候选二：有类型表达项与递归改写

**分类：INSUFFICIENT。** 干净的项语法与解释器可成立；但当前 formal_l0 没有生成表达内容、改写内容或应用控制的过程。如果外部直接补规则或遍历优先级，候选降为 EXTERNAL_POLICY_CONTAMINATED；不能把这种补全称为实现细节。

### 完整因果图与每条边

```text
类型/表达语法/已有合法域 → 可构造项的空间                [M/E；只提供可能性]
bootstrap variation → 初始项/初始改写素材               [B/M；外部作者明示]
frame + experiences + partials + 旧表达项
    → 递归过程产生新表达项与改写项                      [H?：当前无内容生成操作]
新项 + 旧项 → integration 保存新的项图/引用              [M；待生成内容 H?]
内部改写项 + 内部应用地址/控制关系 + 当前项
    → 指定一次改写所得的完整 expression                [M 求值；规则/地址/控制 H?]
多个可改写项 → 实际应用哪一个、输出哪一个                [H?；不能由宿主先匹配先执行]
expression → 必要参数逐项求值 → 完整 command             [M；值/取值关系 H?]
完整 command + 内部端口提交关系 → 合法性检查              [M/E；提交关系 H?]
合法唯一提交 → perform → 身体后果 → 新 frame/历史          [M → E → M]
新历史 + 原表达/改写/控制项 → 下一次递归处理              [H?：需可追踪生产，不是自动强化]
```

| 必答项 | 审计回答 |
|---|---|
| 1. 表达是什么 | 同层有类型项图：一个动作数值项、每个必要参数项、显式 ref 项、组成关系及来源。项还可表示对其他项的复制/连接/替换操作；不是新增 Minecraft 宏 |
| 2. 最初如何出现 | 外部语法先存在；无语义 bootstrap 项记录外部来源。第一次 history-formed 项必须由真实 process 输出，经 integration 保存；当前没有该输出路径 |
| 3. 如何变化、内容来源 | 需要历史形成的改写项指定修改对象、修改位置、新内容及应用关系。泛用复制/构造/替换能力可以是 M；“遇到哪种历史就替换成哪项”不能由宿主写定 |
| 4. 如何到端口 | 解释器仅执行内部给出的应用地址和改写项，将内部已提交的完整表达机械编译到原 perform。不得扫描项池自动找“可执行的最佳项” |
| 5. code 作者 | 完整动作数值项及采用它的控制关系的实际 producer。当前只有 bootstrap 外部作者，尚无 H 作者；改写项里写一个外部常量不自动变 H |
| 6. 每个参数作者 | 每个值、引用和取值操作的内部项及其 producer；缺少任何一项都不能调用 LCG 补齐。只生成 code 时为 INCOMPLETE_AUTHORSHIP |
| 7. 固定了什么 | 类型、项操作语义、求值/序列化、检查、有限容量是 M/E。固定改写模板、自动应用条件和归约优先级可能是 P，必须分别审计 |
| 8. 历史形成什么 | 要形成表达项、改写内容与采用关系，而不只是 evidence_count；现有时间关系仅是输入材料，这条生成边目前空缺 |
| 9. 隐藏仲裁 | 多个规则同时匹配、不同改写不交换、多个合法输出：左侧优先、深度优先、首个合法、最少步数、随机挑一个都可能替系统选行为 |
| 10. 多表达谁获端口 | 必须由内部已形成的应用/提交关系指定。若仅声称所有项自动归约到唯一 normal form，还需证明终止与合流，且初始规则内容非外部策略；当前没有这些证据 |
| 11. 是否失败 | 作为立即可实施的闭环方案不成立。加入固定应用顺序来补洞则明确失败；仅保留可操作语言则是 MECHANISM_ONLY，仍非形成机制 |

“所有操作平等可用”不回答谁应用哪个操作；随机生成改写也不回答何以保留、采用及何以成为历史内容的作用。不得靠历史驱动 RNG 代替这条边。此候选无须价值语义，但筛选生成物的有效性与筛选其行为“更好”必须分开。

表达、改写项、控制项从实验条件开始就是 O0 中的普通对象；固定项解释器仍是 G0。改变这些对象不自动是向上递归。本设计不开放 G0 替换，不开始 L1。

## 6. 候选三：内部控制图携带完整表达与线性端口提交

**分类：PROMISING（研究方向），完整方案仍 INSUFFICIENT。** 相比“表达池 + 外部 selector”，它让控制关系本身成为必须证明来源的内部对象，因而更容易暴露而非隐藏仲裁缺口。PROMISING 不表示已经可以干净实现。

### 完整因果图与每条边

```text
现有身体端口串行性/容量 → 提交协议                     [E/M；不决定谁提交]
bootstrap variation → 初始表达/初始控制对象              [B/M；初始内容非 H]
frame + experience/partial + feedback + 旧控制图
    → process 形成完整表达及其控制连接                  [H?：尚无生成能力]
partial → integration 保存表达/控制图                    [M；内容 H?；不自动置为 active]
内部当前控制引用 + 内部路径/分支条件
    → 唯一完整表达与一次提交凭证                        [M 求值；引用/路径/条件 H?]
唯一内部提交 → 类型/引用/容量检查                        [M/E；无挑选、补参、重绑定]
检查通过 → 同一原生 perform → 身体后果                   [M → E]
结果事实 + 新 frame → 递归材料                           [M；无成功偏好/失败惩罚]
递归材料 + 原控制图 → 新控制/表达/下一提交关系              [H?：需真实生成与内容因果证据]
```

若有多个请求而没有内部唯一提交关系，图必须停在缺口：`多个表达 → ? → 一个提交`。不得以宿主原子锁、FIFO、最先完成、process ID 排序或随机抽取填充问号。

| 必答项 | 审计回答 |
|---|---|
| 1. 表达是什么 | 有类型命令项加显式控制边：code、全部参数项/refs、当前控制引用、到表达项的路径、提交关系及 lineage。提交凭证只防重复/并发，不表达价值 |
| 2. 最初如何出现 | 初始端口协议是 M；初始控制位置/路径/表达若由实验者提供，必须记 bootstrap/初始外部作者。初始存在一个 process 不证明它生成了控制结构 |
| 3. 如何变化、内容来源 | 需要 process 从真实可用历史与旧图产生新节点/边、参数取值关系及下一控制引用。现在 formal_l0 的 partial 不包含这些对象。integration 只能保存 producer 内容，不能自动把最近结果设为当前控制 |
| 4. 如何到端口 | 宿主按内部提交关系解引用一个已经确定的完整命令，只做原 perform 编译与合法性检查；不遍历所有表达寻找可以执行的一项 |
| 5. code 作者 | 内部表达项 producer 与决定采用该项的控制关系 producer，二者都需历史见证。仅“process 发出了请求”不足以证明作者权 |
| 6. 每个参数作者 | 内部图中的值/引用/取值连接及其 producer。code 或参数仍由外部填、LCG 补、宿主选 ref，都是 INCOMPLETE_AUTHORSHIP |
| 7. 固定了什么 | 提交类型、原子消费、重复校验、完整性检查、传输、资源限额是 M/E。凭证发给谁、哪个输出成为当前控制、冲突后恢复哪个是选择内容，不能固定给宿主 |
| 8. 历史形成什么 | 理想情况下形成表达内容及实际采用它的控制图。当前只有历史 relation 与下次 relation-read feedback，不能把该 feedback 偷换成身体控制指针 |
| 9. 隐藏仲裁 | 首个写者取得凭证、先执行现有唯一 process、固定节点访问顺序、最近 integration 覆盖控制引用都会把仲裁搬进协议。图中有 guard 还必须审计谁产生 guard 和多个 guard 同真时如何处理 |
| 10. 多表达谁获端口 | 内部图形成的单一提交关系决定；宿主只认这个明确指向。不允许宿主创建这个指向。重复/矛盾提交可被协议整体拒绝并报告原始事实，但拒绝不解决下一次如何形成唯一提交 |
| 11. 是否失败 | 若凭证取得依赖固定宿主争抢/优先级规则，则失败。当前尚未给出历史形成控制图的 producer，故不能声称已避免所有固定仲裁 |

单身体只能按其物理规则接受输入，属于环境边界；选择哪个表达先输入不是物理规则自然给出的行为答案。协议的原子性只能证明一次命令不被重复消费，不能证明该命令是 A 选择的。拒绝多提交是协议完整性检查；如果随后宿主重试一个、选最先到达者或转换为 NO_OP，则重新引入 P。

不引入 weight。若未来内部产生 weight，也必须分别证明数值生产、更新关系、采用关系的历史作者；宿主规定最大 weight 获胜仍是 P。把最大值算法放入 InternalState 不会改变这一点。

本候选可以保留现有唯一 A、现有一个 process 及原 body.perform；不需要额外角色/进程/层。一个 process 内仍会出现多个表达，单 process 并不消除选择问题。

## 7. 所有必要参数的作者权审计

对候选二/三，以下是**必须满足的合格条件，而非已实现方案**。候选一的来源始终是外部复制/选择；它即使复制全部参数也不通过。

| 参数族 | 可由机制固定的部分 | 内部表达必须明确生产的部分 | 禁止的宿主补全 |
|---|---|---|---|
| action_code | 原冻结数值 codec、当前合法域 | 具体 code 项及采用关系 | 采样/取首个合法/固定 observation→code |
| block_ref、reference_block、object_ref | 当前 opaque 域、类型、carrier epoch/引用有效性 | 某个现有 token 的明确引用，及将其用于这个参数的关系 | 最近、同类、坐标匹配的自动替换；集合取第一个 |
| entity_ref | 当前实体 token 域、存续检查 | 具体 token 及采用关系 | 把掉落物自动排除、自动挑生物或换目标 |
| slot、inventory_slot、source_slot、target_slot、container slot | 真实可引用槽位、整数/范围/接口条件 | 每个槽位具体值及连接，不只是“某个非空槽” | 最近/非空/首个/自动找空间；修补槽位 |
| container_id | 当前窗口的有效 ID 域 | 表达显式带入相应 token；即使域只有一个也要记取值来源 | 无参数时静默填当前 container_id |
| face、button、mode、equipment slot | codec 合法枚举/范围 | 具体数值项或内部取值关系 | 固定面、默认按钮或由宿主抽样 |
| duration、duration_ms | 原接口单位、范围；已冻结常量 codec 的语义 | 可变参数的具体数值及历史来源 | 120/2000 采样、零值/中点默认；额外停止/续用策略 |
| yaw/pitch、yaw_delta/pitch_delta、坐标数值（若原 schema 需要） | 单位、合法数域、原 codec 转换 | 所有数值项，或由内部构造的取值/计算项产生数值 | 对准最近目标、三个候选值抽样、默认朝向 |
| amount 等数量参数 | 数值类型、原接口合法性 | 具体数量和来源；只在冻结 formal 域实际存在时执行 | 自动整组、最少一个、数量上限采样 |
| 其余 schema 必需项 | 逐项原类型及合法域 | 每个必需项的值、采用关系和 provenance | 省略项交回现有 binder |

表覆盖正式能力及已有 debug 宏中可能出现的参数族，不因此把 debug-only 宏加入正式动作域。读取 past action_parameters 是材料读取，不是参数作者权：过去值是谁产生、何种内部操作产生未来使用关系，都需分别证明。

内部表达可以提供显式取值/计算项而不只 literal，但其操作内容、输入 refs 和采用关系同样必须有作者。宿主解释已给定操作属于 M；宿主决定调用哪一个取值函数属于 P。没有唯一结果的查询应保留集合/缺口，不能由宿主择一。

引用失效时只报告失效，不能自动找“对应的新对象”。新引用的取得必须来自新的已允许感知和真实递归内容。type-valid 不等于任务成功、效用更大或不会死亡；错误/拒绝事实不得自动映射为弱化、逃避或生存偏好。

## 8. Bootstrap、记忆与冻结边界

1. 外部语法/解释规则可以先于经历存在，初始无语义 variation 可以提供素材。每个初始 code、参数、项和控制位置要明示外部来源。不能把首次内部持久化视为来源转换。
2. Bootstrap 表达参与后续组合并不自动证明内部作者权：必须定位实际形成变化内容及采用关系的递归操作。后续所有命令若仍由 sampler 决定，仍是 P；固定运行到第 N 步再启用某规则也不能代替内部形成证据。
3. 没有已验证内部表达时，不能以“需要保持运行”为由秘密安装新的 selector。正式现状保持 failed；未来 bootstrap 仍在影响什么，应逐项报告，不能整体改标签。
4. 表达记忆 port 的物理容量可为 M/E；容量不能决定“保留最好/最近/最常用表达”。容量满时仅形成原始限制事实；删哪项、如何压缩、如何重组仍需明确作者。当前锁定 caps 不改变，不借无限审计日志扩容。
5. 候选二/三只把表达和控制对象纳入 L0 的 O0，固定解释器仍属 G0。普通对象可被继续递归修改，不等于 G0 自身成为对象，不声称 L1。
6. 候选理论上可利用现有 code/schema/perform，不需新身体能力或 Minecraft 高级 API。但 `WORLD_ENTRY_FREEZE.json` 包含 `formal_l0.py`、`action_space.py`、`formal_boundary.py` 等组件 hash；**未来接线若改这些文件，仍须明确处理冻结证据范围，不能继续声称整个旧 manifest 与新实现完全一致**。本轮只加文档，manifest 与所有组件不变。
7. 新内部表示/操作若改变 formal 条件，未来必须显式登记独立条件与预算；不能解锁原 A 的 locked_caps、自动迁移历史或借另一 Session 偷换 G0。当前不会做这些变更。

## 9. 比较与污染检查

| 检查 | 一：历史投影/重放 | 二：表达项/改写 | 三：内部控制图/提交 |
|---|---|---|---|
| 主分类 | EXTERNAL_POLICY_CONTAMINATED | INSUFFICIENT | PROMISING，完整方案仍不足 |
| history 真正是 behavior cause 吗 | 可影响输出，但由固定重放政策规定如何影响 | 要求内容及采用关系来自历史；现在缺 producer | 要求表达与控制关系来自历史；现在两者都缺 producer |
| history→RNG 吗 | 若如此改造也失败 | 不采用；仅随机改写不能补证明 | 不采用；随机凭证分配也不闭合 |
| 隐藏 selector | 匹配、排序、重放，本质就是外部 selector | 规则应用顺序与多项归约可能藏 selector | 当前控制引用的形成、凭证分配可能藏 selector |
| 隐藏 binder | 复制/重绑定/缺参回 sampler | 不允许；每个参数必须由项给出 | 不允许；提交前全部参数已有作者 |
| value semantics | 频次/最近偏好已是政策；无需 reward 也失败 | 无须引入；不得按有用/成功筛选改写 | 无须引入；不得把错误事实作惩罚 |
| 可继续递归吗 | 历史可改，但重放政策未内部形成 | 表达/改写/控制项可作为 O0 对象；尚未实现 | 表达/控制连接可作为 O0 对象；尚未实现 |
| 是否仍在 L0 | 是；不是合格闭环 | 是，不开放 G0 替换 | 是，不增加主体/角色/层 |
| frozen body 必须改吗 | 不必改 codec，但改运行接线会触及 manifest | 不必新增身体能力；未来接线仍需冻结范围审计 | 同左；唯一提交并非现有身体新增宏 |
| 本轮污染 freeze 吗 | 没有实施，未污染 | 没有实施，未污染 | 没有实施，未污染 |

MECHANISM_ONLY 适用于语法、类型检查与机械 command 编译这些可拆出的部分，不代表形成闭环。MIXED 适用于实际存在内部行为贡献但 code/参数/仲裁仍有外部贡献的未来实现；当前不能仅凭附上 provenance 就改称 MIXED。只形成 code 而参数外部选择，明确记 INCOMPLETE_AUTHORSHIP。

## 10. 推荐与最大的未解决问题

不推荐一个可以立即替换 sampler/binder 的完整方案。推荐**候选三作为下一次设计研究的方向**，配合候选二的有类型表达表示：它要求把“采用哪个表达”显式存为可审计的内部控制内容，而不是默许宿主扫描表达池。然而这只是暴露缺口的结构选择，不能证明控制内容已能生成。

最小缺口不是一个字段，也不是泛称“决策模块”，而是下面三项相互依赖的能力及其来源证据：

1. **内容构造能力**：现有 partial 只能报告时间关联读取及证据，缺少构造新的未来命令项（code + 每一参数/引用）的通用操作空间。提供操作空间可以是 M；何时调用、调用哪项、产出什么不能仍由外部 observation→模板决定。
2. **控制关系构造能力**：现有 `feedback.next_relation_ref` 只指定读取历史关系，缺少从历史形成“哪一表达项获得当前端口、下一控制位置是什么”的连接。手填 active_ref 或固定最近 integration 覆盖，是把宿主 selector 移入状态，不是补全。
3. **无择一的完整提交能力**：宿主执行一个内部明确提交的完整项是 M；若内部仍给出多个候选，宿主不能替它完成择一。重复、失效、缺参只拒绝/报告，不恢复为 sampler。当前既没有内部唯一提交的生产路径，也没有 counterfactual 证据。

有类型 construct/reference/compose/replace 操作、有限表达 port、保存 partial 的通用 integration 和 mechanical compiler 可以定义为能力；但这些能力并不自己提供历史形成内容的方法。仍需给出可执行的 producer 路径并逐条审计，不能把“以后由 A 自己决定”当算法。

因此答案为 **NO CLEAN IMPLEMENTATION YET**，不是理论不可能的结论，也不是允许随便补一个中立名称的选择器。

## 11. 下一步最小可实现实验（只描述，未实施）

采用分阶段证据门槛，不以强行得到 action 为目标。

### 阶段 A：仅验证机械接口

在独立 TEST_ONLY 隔离状态中检查“外部显式提供的完整有类型项 → 原 command 编译/冻结 perform”，以及缺参、失效 ref、多提交的拒绝路径。不运行正式 A，不写原数据库，不把人工填的项登记为 internal。这个实验只能证明 MECHANISM_ONLY，不证明形成、选择或行为闭合。已有 code/schema 足够承载，不能为了实验新增宏或合法默认参数。

### 阶段 B：先审计 producer，尚不能承诺形成实验可运行

用现有 bounded units/relations/experiences/partials/feedback 明确拟议构造操作的输入输出：表达项、每个参数项、采用控制关系、原始限制事实均需可引用；每次变化必须记录 process/experience/partial/integration 的真实内容依赖。表达与控制关系同样允许作为下一次 L0 对象输入。

这阶段先提交一个具体 producer 设计再审计。不得先安装“历史匹配就复制”“每条新 relation 自动变成表达”“先生成者得到端口”。如果无法描述不靠这些固定内容规则的 producer，就停在 INSUFFICIENT，而不是运行采样器后换来源标签。

### 阶段 C：有了合格 producer 后才做行为反事实

- 两个独立合法递归历史、相同当前感知内容、域、预算、bootstrap，禁止手填 next_action/control_ref/参数，也禁止历史 hash 设 seed。
- 比较真实生产的表达内容、**全部参数**及控制关系，不只比较 UUID、修订号或标签。解释被消费的对象如何由历史形成。
- 分别消融表达内容、参数项、控制连接；保持解释器、当前感知、bootstrap 和合法域相同。记录具体 code/每个参数/端口提交的差异及实际读取见证。消融只在隔离副本，不破坏主线历史。
- 专测多个表达、多个条件同时成立、输入/存储排列变化：如果结果由宿主排序、race 或 binder 决定，明确失败。检查拒绝后是否偷偷采样、补参数或重绑目标。
- 仅在内部唯一完整提交及所有作者权证据成立后，才进行新的真实 Minecraft action→后果→观察验收；不得借旧 TEST_ONLY 或 world-entry 验收使闭环 passed。

没有预设第一次应选何动作、应有多少表达、何时停止 bootstrap、看到错误如何修复，也没有成功/失败偏好、效用或存活目标。不同历史不保证必然选不同动作；需要的是具体结构被消费的因果证据，而不是为得到不同结果而加入固定映射。

## 12. 本轮交付边界

只新增本审计文档。未修改正式代码、配置、测试、SQLite、canonical lifetime、Session、frozen body、manifest 或旧报告；未运行新的测试载体/真实游戏实验。上述代码位置和实验值是基准已有证据，候选图中的 H? 全部保持未实现。下一步没有开始，L1 没有开始，原 failed 结论保留。
