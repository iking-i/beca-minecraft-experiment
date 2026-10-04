# Current Structure Generation Audit

日期：2026-10-05（Asia/Shanghai）。本轮只做机制级审计，不实现、不运行新实验。

## 1. 基准、阅读范围与修正后的问题

审计开始时，本地与 GitHub 实验 HEAD 均为 `230789b3be6215eda971d3beb1be0dbe85eb969e`；理论 HEAD 为 `89a56ad7ce236adfcb52b13d3e6fe7014ff88ddd`。本文件提交只增加设计文档，不改变被审计实现。

完整核对了用户列出的两份已有审计、十份 individual 源码、四份实验边界文档，以及理论该提交的 [SPEC.md](https://github.com/iking-i/beca-architecture/blob/89a56ad7ce236adfcb52b13d3e6fe7014ff88ddd/SPEC.md)、[ARCHITECTURE.md](https://github.com/iking-i/beca-architecture/blob/89a56ad7ce236adfcb52b13d3e6fe7014ff88ddd/ARCHITECTURE.md)、[BIDIRECTIONAL_RECURSION.md](https://github.com/iking-i/beca-architecture/blob/89a56ad7ce236adfcb52b13d3e6fe7014ff88ddd/BIDIRECTIONAL_RECURSION.md)、[EXPERIMENTAL_IMPLEMENTATION_BOUNDARY.md](https://github.com/iking-i/beca-architecture/blob/89a56ad7ce236adfcb52b13d3e6fe7014ff88ddd/EXPERIMENTAL_IMPLEMENTATION_BOUNDARY.md)。源码行号以下均针对审计基准。

上一轮把主要缺口表达为“行为表达形成 + 内部控制图决定采用哪个表达”，残留了从既有答案池中择一的前提。本轮明确修正：

```text
stored structure ≠ candidate answer
stored relation ≠ future action candidate
primitive capability ≠ 当前应该做什么
```

新的问题是：**当前现实、已有结构、当前递归状态及新差异/后果，能否共同产生一个此前不存在的当前组织，其同一内容既作用于后续内部递归，也可能形成完整的对外作用？**

不要求先生成多个完整行为再仲裁。不要求每次递归输出动作。旧审计文档保留为历史，不修改其中的候选与结论；本文件明确取代其“候选三应作为主要下一步”的设计建议，不把旧建议当成当前已实现能力。

理论 v0.9 允许固定原语支持新的功能组织，但没有给出本实验所需的具体生成算法。它也不保证任何新组合必然形成。`Continuity(A) != 0` 仍是本个体实验的延续条件，不是新增 reward，也不是通用理论公理。本轮的“统一当前结构”是实验设计候选，不冒称四份理论文件已指定了同名数据结构。

## 2. Recording 与 generative 的可检验区别

本轮采用用户要求的四种内容检查；它们不必互斥：

| 类型 | 判断依据 | 不足以满足它的名称 |
|---|---|---|
| A：现实记录 | 内容是当前或过去输入、执行事实、数值差异、次数 | NEW_EVENT、new dict |
| B：已有数据重新引用 | 引用已有对象、复制已知字段、建立索引 | 新 UUID、new pointer |
| C：时间关联 | 将先后观察与期间执行事实关联起来；不因此断言动作因果 | relation、prediction |
| D：新结构构造 | 存在可定位的新连接/组合/变换，其组织内容由递归历史形成，并被后续操作真正使用 | structure_revision、integration ID |

必须区分 D 的两个尺度：

1. **有限的记录结构新颖性**：经历可以第一次引入某个 antecedent/action/outcome 连接。这是真实新内容，可成为后续递归材料，不应说 FormalL0 完全没有新内容。
2. **本轮要求的新当前组织构造**：已有关系的部分、新输入、参数/引用和新连接能被递归构成此前没有的组织，而非只在固定经验表中增添一行。其具体连接与变换须可追踪，必要时产生以前未执行过的完整 code + parameters 组合。

FormalL0 已证明第一种及其后续读取依赖，没有第二种的执行路径。把前者叫“记录型”不否认真实层内反馈；把后者叫“生成型”不要求 L1，也不要求每步发生架构变化。

## 3. FormalL0 的实际生成能力逐项审计

| 对象 | 实际执行位置/函数 | 输入与输出 | A/B/C/D 判断 | 对本轮生成问题的结论 |
|---|---|---|---|---|
| units | `individual/change_detection.py:22`，`detect_changes`；`individual/structure.py:16`，`pattern_id`；`individual/formal_l0.py:117–132`，`advance` | 通道值比较产生 changes；通道 ID/kind 形状 hash 标识 unit；首次存变化记录，后续增加 observations | A；unit 标识为 B；可出现新的描述形状，未构造新的可操作组织 | 不从 R1/R2 部分构造 R4；hash 不应被改作行为 RNG |
| relations | `formal_l0.py:173`、`223–252`，`advance` | root 固定为 previous_unit:最后 pending action_code；保存 antecedent、code、outcomes、计数/有限引用 | C + A/B；首次 outcome 边有有限 D，但连接模板由外部固定 | 真实连接内容由经历形成；无跨关系组合、参数组织或新当前效应构造 |
| experiences | `formal_l0.py:172–192` | 前后 frame、当前差异、过去 action_ids/statuses/parameters、有限 context、raw limit 后果 | A + C；对象引用 B | `causality=temporal_association_only`，不是未来命令，也不是新的构造操作 |
| partials | `formal_l0.py:196–217` | 读取 feedback 指向的 relation；复制 experience/question/feedback，计算读到与否、expected_outcomes、是否已有 outcome | A/B/C 及固定比较派生值 | 比较确实消费历史；没有 operation instance、构造项、参数连接或未来 effect |
| feedback | `formal_l0.py:270–278` | 写入此次 root、expected_outcomes、hash、integration/partial IDs、限制引用 | B；内容随 C 的历史变动 | 下次读取依赖内部历史，但“写哪种反馈”格式固定；不是通用构造状态 |
| integration | `formal_l0.py:223–268` | 固定插入/计数后记录 `record_distinct_experience`、前后 hash；`organization_changed=false` | A/C 更新及 B 审计包装；有限 D 同 relation 行 | `operations` 是已经执行的记录操作描述，不是 process 生成并被解释执行的构造程序 |
| process | `formal_l0.py:149–169`、`193–218` | 外部创建一个 `temporal_relation_evaluation`；固定 question，hypothesis 为空；output 仅 partial_id/publication_number | 初始化/身份为 B 与外部初始策略；后续报告 A/B/C | 没有自产生的新问题、规则、局部结构变换或可执行 operation；question 字段不被解释成可变程序 |
| generation_parameters | `individual/policies.py:83`，`initial_generation_parameters`；`formal_l0.py:258–259` | 兼容/历史初值；integration 复制 before/after 同一数据 | 外部初始化，B | 正式路径不读取它来改变数量/分辨率，也不更新它形成新组织 |
| latest_generation | `formal_l0.py:165–169` | 初始化 process 时生成 UUID，requested/granted=1，`subsequent_quantity_adjustment=false` | 初始外部策略的记账，B | 名称 generation 指过程创建记录，不是持续结构内容生成 |

`same_context_as_prediction` 在 `formal_l0.py:210` 实际只是 `reference == root`；不是完整数值 context 相同的证明。`expected_outcomes` 来自历史 outcomes 列表，不是可产生新关系的模型输出。不能从这些字段名推断已有生成能力。

`structure_revision` 在 `formal_l0.py:289` 每次推进都会增加，资源观察、动作请求或身体事件也能增加它。revision 增长不证明组织构造。`latest_structure_changes` 在正式 advance 结束固定为三个空列表，同样不能靠遥测名称认定新组织。

### 正式路径与 legacy 操作不能混用

`individual/core.py:45–47` 按 profile 选择 `FormalL0Engine` 或 `StructuralEngine`。正式路径只从 `structure.py` 复用 `pattern_id`，不调用旧 engine 的分化/整合。旧 `generation.quantity`、评分、分辨率策略登记存在，不表示它们正式启用。

`InternalState.merge_units`（`individual/internal_state.py:66`）可合并已有单元并改关系引用，但 FormalL0 不调用它；目标、sources、合并时机也没有内部 producer。它依赖旧 strength 数据的实现不能被默认为正式生成操作。Python 的 dict 可以写任意形状，不代表 A 获得了这种操作能力：当前 engine 没有相应解释入口，严格的 InternalState 构造也不接受任意新增顶层字段。

`PolicyRegistry.validate_internal_proposal`（`policies.py:190`）只检查元数据，返回 `activated=false`、`history_references_verified=false`。它不填补 producer 或 result adoption。

## 4. 当前实际因果图及缺失边

每条操作边只使用五类：EXTERNAL_FIXED_MECHANISM、ENVIRONMENT_CONSTRAINT、EXTERNAL_FIXED_POLICY、INTERNAL_VARIABLE_STRUCTURE、UNRESOLVED。机制执行与内容来源分列，避免把执行地点当作者。

| 因果边 | 操作分类 | 内容作者/证据 |
|---|---|---|
| Minecraft reality → 原始身体观察 | ENVIRONMENT_CONSTRAINT | 世界实际状态及原身体感知边界 |
| raw observation → ObservationFrame | EXTERNAL_FIXED_MECHANISM | `observation.FrameEncoder.encode:40` 数值/opaque 编码；覆盖与采样范围属 ENVIRONMENT_CONSTRAINT |
| 前后 frame → ChangeSet → unit | EXTERNAL_FIXED_MECHANISM | `detect_changes:22`、`pattern_id:16`、`advance:117`；具体变化内容来自现实 |
| 前次 unit + 执行事实 + 当前 unit → experience | EXTERNAL_FIXED_MECHANISM | `advance:172`；形成内容为时间记录，不是新行为答案 |
| feedback → 实际 relation read → partial | EXTERNAL_FIXED_MECHANISM | `advance:196`；被读关系内容为 INTERNAL_VARIABLE_STRUCTURE，已证明改变读取结果 |
| experience/partial → relation/outcome 更新 | EXTERNAL_FIXED_MECHANISM | `advance:223`；历史形成内容为 INTERNAL_VARIABLE_STRUCTURE，组织模板固定 |
| 更新 relation → feedback → 下一次内部读取 | EXTERNAL_FIXED_MECHANISM | `advance:270`；实际引用和预期内容为 INTERNAL_VARIABLE_STRUCTURE |
| 当前现实 + 旧结构 + 递归状态 → 新当前组织构造 | UNRESOLVED | 没有构造内容/operation instance 的输出与应用路径 |
| 新当前组织 → inward effect | UNRESOLVED | 现有有限 relation-read 边已存在；扩展到新组织作用尚未实现 |
| 新当前组织 → 完整 outward effect | UNRESOLVED | 正式代码不消费这种对象 |
| 当前 available primitive codes → 实际 code | EXTERNAL_FIXED_POLICY | `formal_l0.select_uniform_action:296`；可用域为 ENVIRONMENT_CONSTRAINT，LCG 取值为政策 |
| 当前参数域 → 实际参数 | EXTERNAL_FIXED_POLICY | `action_space.bind_parameters:75`；域中选择及默认由外部决定 |
| 已选 code/参数 → perform RPC | EXTERNAL_FIXED_MECHANISM | `action_space.formal_command:155`、`core.execute_discrete_action:229` 之后 |
| perform → 世界后果 → 新观察 | ENVIRONMENT_CONSTRAINT / EXTERNAL_FIXED_MECHANISM | 世界后果按原生规则，观测传输是机制；二者不是新组织生成的证据 |

已有负对照：不同合法 TEST_ONLY 历史产生不同 outcomes/计数；关系消融改变 recursive read，却不改变正式 `46/{}` 命令，参数探针也没有变化。旧报告的真实意义保持不变；本轮不读取/写入 canonical SQLite，也不运行新夹具。

## 5. 断点在什么执行结构

断点不只是“关系之后缺一个行为模块”，而在 FormalL0 的处理体内部：

1. `advance:196–217` 只能从一次固定 relation read 计算描述性 partial。partial 没有构造目标、端口连接、数值变换、参数绑定或递归状态组织变化。
2. `advance:223–252` 不解释 partial 中的生成内容；它直接把当前 experience 写入固定 root/outcome 表。`operations` 列表在写入后追加固定 `record_distinct_experience`，并非先由过程产生后被执行。
3. `advance:253–278` 用固定记录格式生成 integration/feedback，不能把 R1 的部分与 R2 的关系、新差异连接成 R4。前次 feedback 影响被读取的数据，却不改变本次能执行的操作空间或形成实例。

因此即使向 InternalState 增加 `current_structure` 或 `world_facing_effect` 字段，这三步也不会自动写出新内容。由外部填这些字段，只是隐藏作者的位置变化。

`temporal_relation_evaluation` 从执行体而非字符串看确实过窄：无通用对象构造、连接、变换和应用接口。改 question.kind 名称、让它接收所有历史、延长时间或扩大槽位都不能补这个操作空间。当前极限的 raw 后果会进入 partial，却没有由它产生重组操作的 producer；不能假定“收到极限”就自动会创造。

## 6. 候选四：Unified Current Recursive Structure

这是新的结构规格，不是已实现算法，也不是从 R1/R2/R3 选 active relation。

```text
CurrentStructure_t  （同一个 A 在当前递归状态中的组织）
  ├─ 当前现实表示、覆盖与输入引用
  ├─ 可被使用的已有 units/relations/experience 材料
  ├─ 正在形成的新连接、变换与参数/引用组织
  ├─ 未完成部分、矛盾、非法事实、容量后果
  ├─ 后续递归实际消费的组织/状态
  └─ optional world_facing_effect
       └─ 仅在完整形成时：原 codec 的 code + 全部必要参数
```

这些是同一个结构的不同因果作用面，不要求分离 cognition 与 behavior 的两个 producer。若出现 R4，它须有实际新连接及历史内容生产记录；不能仅把旧关系放到一个新 dict 外壳中。

允许 R4 使用既有材料的部分，但不定义“匹配过去命令就复制过去 parameters”为生成方式。新完整组合可以从未执行过；新颖性只作为审计事实，不是 reward、保留标准或真实性证明。已有 primitive 的 code 是低层作用语言，不是候选答案列表。

### 新模型的因果边（未实现边明确 UNRESOLVED）

| 边 | 分类 | 是否已存在 |
|---|---|---|
| 当前现实 → 当前输入/差异/原始后果 | EXTERNAL_FIXED_MECHANISM；现实边界 ENVIRONMENT_CONSTRAINT | 已有感知编码，不增加 API |
| 历史 → 当前可用结构材料 | INTERNAL_VARIABLE_STRUCTURE；存取操作 EXTERNAL_FIXED_MECHANISM | 已有有限关系、feedback；不能借无限审计日志 |
| 当前输入 + 材料 + 当前递归组织 → 新连接/值/构造实例 | UNRESOLVED | 当前没有 producer，不能标 internal |
| 具体构造实例 + operands → 新当前组织内容 | UNRESOLVED；未来机械应用部分可属 EXTERNAL_FIXED_MECHANISM | 只有语言建议，未实现实例与应用路径 |
| 同一新组织 → 后续递归的实际输入/组织作用 | UNRESOLVED | 现有 relation-read 是有限前身，不等于新模型通过 |
| 同一新组织 → optional 完整 world-facing effect | UNRESOLVED | 不允许外部另造动作/补参 |
| 唯一完整 effect → validate/compile/transport | EXTERNAL_FIXED_MECHANISM；合法性域 ENVIRONMENT_CONSTRAINT | 原 perform 编译可复用，结构接线未实现 |
| 身体输入 → 世界后果 → 下一次递归输入 | ENVIRONMENT_CONSTRAINT → EXTERNAL_FIXED_MECHANISM | 已有世界/感知能力，不借它证明上游生成 |

## 7. 单一实际状态：已有基础不等于构造已经完成

`ACore` 只维护一个 `_state`。`_transition`（`core.py:91–103`）从旧状态 replace 成下一版本，在 EventStore.transition 后置为当前状态。`state` 属性返回 detached 副本；lease 防止同库的重复实验实例。正式循环/控制处理把状态变化顺序提交，历史 A_n 不是当前并行个体。

所以 **one realized current state 的承载基础已经成立**，不需要为了一个 CurrentStructure 再造外部“统一主体”。但以下推论不成立：

```text
单一 AState → 内容无矛盾 → 唯一完整 effect → 内部作者权成立
```

一个实际状态可以同时包含多个相冲突连接、未定值和缺参。单状态中的 scalar `effect` 字段也可能由宿主 last-write-wins 填出，不能因此通过。数据结构唯一和生成内容唯一是两个问题。

候选四的身体端口可以只读取当前结构的那个 effect 位置，不必从池中选择。但必须是递归构造真的使这个位置形成完整内容，不能由宿主在若干结果中挑一写进去。矛盾内容应留在实际结构中作为未完成组织，不产生完整可执行 effect。

外部事务/版本/序列化可以保持一次实现状态的完整性，属于 EXTERNAL_FIXED_MECHANISM。它们不需要决定“哪个递归构造结果更好”。若用 process order、覆盖先后、最先完成、FIFO 来决定实际采用哪种矛盾内容，就成为 EXTERNAL_FIXED_POLICY。当前只有一个过程可减少并发问题，但同一过程仍可有多个未定连接，不能靠数量 1 证明答案唯一。

## 8. Inward/outward 对称与中间层的必要性

目标是同一个 recursive internal organization 的双向因果接触，不是每个认知固定对应一个动作，也不是感知信息量与动作信息量必须相等。

```text
Reality_t → CurrentStructure_(t+1)
                         ├─ inward：改变后续递归真正读取/构造的内容
                         └─ outward：若完整形成则经原身体改变 Reality
新现实/拒绝/后果 → 再进入同一组织的继续构造
```

| 部分 | 是否必要 | 边界 |
|---|---|---|
| 世界感知及数值/opaque 编码 | 必要的已有接口 | 不偷偷加入语义知识 |
| CurrentStructure 的构造与持续状态 | 本模型必要 | 不能由固定宿主内容映射填充 |
| 世界接口的类型/合法性检查、机械编译与 transport | 必要 | 只转换已形成内容，不选择/补全 |
| 独立 cognition→behavior producer | 不必预设 | inward/outward 可以是同一新组织的作用面 |
| expression pool、候选排序、独立 action selector | 不需要作为此模型的前提 | 无完整 effect 就不发送新 perform |
| 从多个表达中择一的 control graph/port arbitration | 不需要单独添加 | 实际依赖连接可存在于当前结构，但不是外挂择优系统 |
| 计算依赖与输入事件处理顺序 | 仍需明确 | 不是都可以叫政策；一旦顺序决定内容取舍，必须审计 |

当前 perception 改变历史关系，但 outward action 独立由 LCG 决定，因而缺乏这里要求的认知—行为匹配。把同一 integration ID 同时贴到 action 事件不能补因果边。

## 9. 最小结构操作语言与五项作者权

一个可研究的最小操作空间是：有类型节点/端口、显式对象路径、值/opaque refs、连接项，以及可对这些对象进行的构造与替换。它们应允许把旧材料的部分与新输入组成新的组织，并允许继续处理未完成内容。不是给 Minecraft 技能，不是 planner 或随机变异。

可用四类基础操作表达这个空间；以下是规格示例，**不是 A 当前应调用的实例**。单独的 compose/copy/bind/derive 不必全部新增为不同运行模块，它们可由下述操作表达。数值 transform 若需要，要另定义明确类型与函数语义，不能把它当无约束“创造”指令。

| 操作族及意义 | operation vocabulary author | operation instance author | operand author | result author | result adoption author |
|---|---|---|---|---|---|
| construct：创建有类型节点/局部项及端口 | 外部定义允许格式，EXTERNAL_FIXED_MECHANISM | UNRESOLVED：谁形成此次类型、位置与值的实例 | 输入材料可来自现实/历史；使用哪部分 UNRESOLVED | 机械节点分配可属机制；组织内容 UNRESOLVED | 哪些内容成为此次当前组织 UNRESOLVED，不能自动采用最近结果 |
| reference/connect：按显式路径引用对象、构造新端口连接 | 外部定义引用/连接语法与类型检查，EXTERNAL_FIXED_MECHANISM | UNRESOLVED：连接两端和连接关系的此次内容 | 对象本身可为 INTERNAL_VARIABLE_STRUCTURE；对象路径的形成 UNRESOLVED | 机械连接可属机制；新连接内容 UNRESOLVED | 新连接如何参与后续生成/effect UNRESOLVED |
| replace：在显式位置变换局部组织，保留 lineage 与未完成内容 | 外部定义事务性替换能力，EXTERNAL_FIXED_MECHANISM | UNRESOLVED：目标、新内容和此次应用关系 | 旧对象可为内部历史；替换材料的组成 UNRESOLVED | 应用算子可属机制；变换后的组织作者 UNRESOLVED | 不能用 last-write-wins；实际状态转移的内容生产 UNRESOLVED |
| typed transform/bind：按明确运算项构成数值/引用参数连接 | 仅固定类型/运算语义，EXTERNAL_FIXED_MECHANISM | UNRESOLVED：运算项及哪一参数连接的实例 | 原数值/ref 可来自 lawful 输入；参与路径 UNRESOLVED | 值机械求值可属机制；组织这些输入和运算的内容 UNRESOLVED | 是否形成此次 effect 的组成部分 UNRESOLVED |

复制可作为材料引用/构造的底层能力，但外部规定复制哪条过去完整动作作未来答案是政策，不能借 copy 操作洗掉。泛称 derive 不能掩盖里面的匹配规则、推理模板或择优函数。

`compose(R1.partA, R2.partB)` 的 vocabulary 可以外部给定，但这个完整 instance 的 opcode、两个路径、连接位置及应用事实都需要实际 producer。**目前找不到它的因果路径。** 不能整体写成 INTERNAL，也不能以“递归过程形成”代替一条没有的执行边。

### 最小新增路径的精确规格与仍空缺的部分

```text
已有合法 frame + bounded 结构 + previous recursive state
    → [实例内容生产：UNRESOLVED]
    → 带输入引用/位置/值/连接的构造实例或实现态变化
    → [有类型机械应用：可定义 EXTERNAL_FIXED_MECHANISM]
    → 新当前组织（允许 partial/conflict）
    → 后续递归消费 + 若形成则对外作用
```

机械应用可以由解释器实现，不要求再有 selector。但第一条生产边不能被语言词表代替。若采用“变化直接发生”的连续状态转移模型，也要给出具体更新律、内部连接如何形成/改变及哪些内容被消费；不能只写 `C_next=F(C,input)` 便宣称 F 干净。现有 F 就是固定记录/读表，无法得到本轮 R4。

## 10. Selector 无限后退与自然结构变化审计

构造不必在逻辑上经过“生成候选→选择”，也不必每次变化另找一个更高 selector。一个固定解释器执行已形成的依赖连接或唯一操作实例，本身不要求新的择优者；普通物理/计算更新规律也不因固定就一概是 policy。

但是，当前代码没有能结束这个作者权追问的内容生成路径。候选四把问题前移到了组织生成，不是已经解决它。

| 潜在替代方案 | 必须追踪的因果内容 | 本轮判断 |
|---|---|---|
| 新增 operation selector | opcode、operands、应用位置由谁决定 | 把 action selector 往内推；若宿主填写是 EXTERNAL_FIXED_POLICY |
| 所有连接自动触发 | 哪些连接先存在、何时触发、同写入/冲突如何处理 | “全部运行”不自行生成连接内容；顺序/冲突规则仍可能隐含策略，UNRESOLVED |
| 数据流/唯一归约结果 | 网络连接/具体规则从何产生，归约是否合流，顺序是否改变结果 | 机械执行可以 EXTERNAL_FIXED_MECHANISM；内容 producer 与合流证据 UNRESOLVED |
| 历史直接驱动结构变换 | 更新律是否直接规定 observation→具体 code/参数/组合 | 若固定规定答案方向为 EXTERNAL_FIXED_POLICY；当前无不含此映射的生产证据 |
| CurrentStructure 字段自动覆盖 | 谁有写入权限、为何采用此更新而非保留矛盾 | 唯一容器不消除 overwrite policy |

固定 scheduler 可以提供运行机会、输入传输和预算约束；不能默认它天然无行为作者权。如果调度先后使一条未完成构造被覆盖或使一个 effect 获得执行机会，必须追踪。当前 `core.tick:333–361` 还有一个具体外部方向：时间到就调用 sampler，随后观察；它不等于“当前递归已形成完整 effect 时才发送”。Registry 中 `core.scheduler=CORE_MECHANISM` 不足以证明这整个时间驱动行为边都无政策。

因此不引入另一个 rule chooser、operation chooser 或 scheduler 作为答案。尚未解决的部分归为 UNRESOLVED，不得无限增加命名模块，也不得把一切由固定规律发生的新值都否认为内部变化。

## 11. 完整 world-facing effect 及全部参数作者权

当前结构中的 effect 若存在，必须是此次递归构造的完整结果。宿主只允许 validate、reject、compile、transport。不从 available_codes 抽样，不从 relation 找旧 code，不重放最相似历史，不从过去 action_parameters 自动复制完成命令。

| 内容 | 当前实际作者 | 候选四的合格条件 |
|---|---|---|
| code | `formal_l0.select_uniform_action`，EXTERNAL_FIXED_POLICY | 此次构造形成的明确数值项及与当前 effect 的组成关系；目前 UNRESOLVED |
| block_ref/reference_block、entity_ref、object_ref | `action_space.bind_parameters` 的域采样，EXTERNAL_FIXED_POLICY | 每一引用由当前构造组织；原接口只验证当前域/有效性，不能 nearest/first/rebind |
| slot、inventory_slot、source_slot、target_slot、container slot | 域采样，EXTERNAL_FIXED_POLICY | 每一槽位值/连接有此次生产 lineage；不是宿主自动非空/空位查找 |
| container_id | 有的分支直接填当前窗口，有的从单值域取，均属外部参数填写 | 单值域也要求 effect 已完整带入，不以“唯一合法值”补参 |
| face、button/mouse_button、mode、equipment slot | 固定域及采样，EXTERNAL_FIXED_POLICY | 每个枚举/整数的构造来源明确 |
| duration/duration_ms、yaw/pitch 及其 delta | 固定候选值/LCG，EXTERNAL_FIXED_POLICY | 所有可变必需数值由当前项形成；原 codec 固定语义可保留，但不得新增默认填值 |
| amount 及其余 schema 必填项 | 相应现有 binder 或 debug 分支外部填写 | 每项有生产及应用来源；保持原正式域，不把 debug-only 宏新增为正式能力 |

已有体接口定义 code/schema 及数值合法域是能力机制/环境边界，不能直接推成答案。参数的组成方式与具体值作者分开核对。当前旧参数记录可作为历史事实参与构造，但字段被读取不证明未来使用关系由内部形成。

若新结构只形成 code，参数为空或缺失，结论为 no complete world-facing effect，不调 binder。effect 内的合法性失效同样不允许 repair。引用在当前世界已失效，真实结果就是 invalid；不会因为换一个新 ref 很容易就补它。

## 12. Partial、矛盾、非法与不输出

| 当前结构实际情况 | 允许的端口处理 | 返回到继续递归的事实 |
|---|---|---|
| 没有 world-facing effect | 不发送新 perform，不生成 NO_OP 事件 | 递归仍可继续，不能称 A 决定了等待 |
| 有部分 effect，必需项未形成 | 拒绝，不补值 | 原始缺项/类型事实；不奖励或惩罚 |
| 多个不相容值/效果仍未解决 | 不选第一个、不 FIFO/LWW/argmax/random/priority | 保留矛盾及其生成引用，作为当前未完成组织 |
| 完整但非法或引用过期 | 原接口验证拒绝，不换目标 | 原有合法通道可观察的拒绝/世界后果 |
| 完整、合法、此次新形成的 effect | 机械编译、按原接口传输，并审计执行次数 | 世界实际后果，不把 transport success 当达成目标 |

拒绝冲突是接口完整性边界，不等于矛盾已被解决。统一结构没有形成可执行组织时，外部不能替它制造答案。原有 held controls 仍可能持续作用；“不发送新命令”不等于世界静止、自动松键或停止身体。停止控制仍依赖原 primitive/外部安全边界。

还有一个不得隐藏的接口问题：同一 effect 在后续读周期被读到，是否再执行？持久存储的 effect 不自动意味着无限重放。未来须按具体因果版本/一次形成实例区分“此 effect 的一次传输”和“新结构再次形成作用”；去重、传输记账可以是 EXTERNAL_FIXED_MECHANISM，但宿主规定永久重放/固定重试属于 EXTERNAL_FIXED_POLICY。目前此接线也未实现，不借它制造新的选择器。

## 13. 候选四与候选三重新比较

| 问题 | 候选三：表达 + 控制图 + 提交 | 候选四：当前结构 + optional effect |
|---|---|---|
| 1. expression pool | 容易预设多个未来行为项，然后形成采用关系 | 不预设答案池；已有材料和未完成连接不是候选答案 |
| 2. 独立 selector | 虽要求内部作者，仍把“采用哪个表达”当主要问题 | 对外端口不需要 selector；读取已形成的唯一完整 effect |
| 3. control graph arbitration | 主缺口是控制关系/凭证如何分配 | 不再单列竞争图；构造过程仍须保留冲突，不能内部偷偷择一 |
| 4. 人为设计层 | 分开 producer、表达、控制、提交，容易新增人为层 | 一个持续结构及 inward/outward 两种作用面；类型/编译边界仍必要 |
| 5. 与本轮 Perfect Recursion 问题是否相符 | 容易沿用“过去答案中选择”前提 | 更直接研究现实与已有材料继续构造新的当前组织；不因此证明理论实现 |
| 6. 隐藏 selector/scheduler 是否完全消失 | 未解决控制内容生产与冲突取舍 | 端口层可消除；生成层的实例内容/更新应用/调度依赖仍 UNRESOLVED |
| 7. 隐藏选择具体位置 | active_ref、guard、提交凭证、访问顺序 | 构造操作的 opcode/operands/位置，结果更新如何改变 C_t，冲突是否被覆盖、effect 是否循环重发 |

候选四**在问题定义及接口分层上更干净**，不是已得到更强实验结果。它减少不必要的中间层，不能用 single-state 字段遮住生成内容的来源。无须另外外挂 selector 或候选三的 control graph；实际构造依赖关系仍须可表达和审计，不等于要求没有任何控制/依赖。

## 14. 最小缺失能力与是否要改 L0

针对用户提出的 A–E 缺口：

| 缺口 | 实际判断 |
|---|---|
| A：缺可递归写入的新结构构造空间 | 成立。现有字段能存记录，正式操作集不能构造任意新的有类型连接/参数组织；Python 可写不等于 A 可操作 |
| B：有空间但无具体构造实例 producer | 同时成立：即使定义空间，内容生产/应用因果边仍缺。当前 partial/integration 不产实例，未找到可直接复用的 producer |
| C：能构造局部结构但不能形成完整 effect | 现有能力仅为有限时间关联更新，没有本文生成意义的局部新组织；effect 路径当然缺，不能误称只差出口 |
| D：有 effect 但缺参数 | 当前甚至没有内部 code/effect producer；这是未来 partial 状态的可能情况，不是当前的唯一问题 |
| E：记录型而非生成型 | 更接近记录型反馈递归；保留历史形成关联及后续读取的真实作用，但未达到新当前组织构造 |

最小能力不是“再加行为模块”，而是让 **同一 L0 递归处理体能对当前组织进行有类型构造/连接/变换，并实际产生此次操作内容和新的实现态**。这要求扩展 `advance` 中 partial 形成及 integration 应用的基本操作模型；只改出口不能解决。

需要修改 L0 基本递归机制才能实现目标，但**本轮不改**。未来由实验者设计并替换这段机制，是新的实验条件，不是 A 自然重构或 upward recursion 的证据。固定 G0 可以从新条件初始化时提供更完整的构造能力；对 O0 内组织的持续构造仍可属于 L0。不开始 L1，不把程序员增加操作语言报告为自然升层。

无需修改或扩张冻结 Minecraft primitive 能力来回答这个缺口。未来若修改 `formal_l0.py` 等 manifest 覆盖文件，必须另行处理冻结证据的实现版本范围；本轮保留 `WORLD_ENTRY_FREEZE.json` 和组件原样，不虚称将来的新代码仍具有相同 hash。

## 15. 推荐下一步（只描述，不实施）

先完成**单一当前组织的具体更新机制规格**，而非启动新游戏测试或换 action selector：

1. 在纸面/审计表上固定 CurrentStructure 的可操作对象域、输入寄存器、bounded 记忆与原接口；不借 unlimited journal、不解锁旧 caps。
2. 给出一个具体的组织转移生产体：逐条说明如何从当前现实和已有内容形成操作实例或直接的结构变化，列清 opcode、operands、位置、值、连接与结果采用的来源。若最终仍是宿主填写当前该做什么，明确停在 UNRESOLVED，不实现。
3. 对同一个新结构要求 inward 的真实后次读取证据；若它形成 outward effect，再要求每项参数及世界后果证据。不把“每步必须动作”作为约束。
4. 在设计阶段检查输入/存储排列、未完成参数、矛盾、容量、过期 refs、重复读取 effect 的处理；不得安装默认值或 fallback。若须用 operation selector 才能运行，先审计该 selector，不继续往内新增选择器。
5. 只有生产体足够具体后，才考虑独立隔离的机制/反事实实验：验证能形成不只是过去完整命令复制的新组合，旧材料消融改变具体构造内容，未完成时保持无完整作用。人工填实例只能验证机制，不证明递归形成；新颖性也不作为评分。

不建议以 random mutation、genetic/beam/novelty search、planner、program synthesis、LLM、heuristic composition 或 reward-guided search 补洞。也不把“自动执行所有可用操作”当作已经审计的答案。这些方案均需自己的内容生产、筛选、保留和调度来源审计。

## 16. 最终分类与交付范围

主分类：**FORMAL_L0_IS_RECORDING_NOT_GENERATIVE**，特指本轮要求的新当前组织构造；不否认经验形成新关联和后续读取的有限生成事实。

候选四的设计分类：**GENERATION_MECHANISM_PROMISING_BUT_PRODUCER_UNRESOLVED**。

实现影响判断：**RECURSIVE_GENERATION_REQUIRES_DEEPER_MODEL_CHANGE**，限于此 FormalL0 实现需要扩展 L0 基本处理体，不是已经形成 L1，也不是理论层面的普遍不可能证明。

不使用 **CURRENT_STRUCTURE_GENERATION_PATH_IDENTIFIED**：尚未给出不含隐藏政策的具体内容 producer。

本轮只新增本文件；未修改旧审计、正式 runtime、配置、测试、WORLD_ENTRY_FREEZE、canonical 选择或 SQLite/Session/历史；未运行 A、测试载体或 Minecraft 联调。`WORLD_ENTRY_FREEZE=passed` 的原范围和 `BEHAVIORAL_CAUSAL_CLOSURE=failed` 均保持。没有实现推荐方案、增加能力或开始 L1。
