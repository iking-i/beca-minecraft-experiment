# BECA-V0：L0 持续递归与当前极限反馈实验

本仓库是 [beca-architecture](https://github.com/iking-i/beca-architecture) 的独立 Minecraft 实验实现，当前理论引用为 **Perfect Recursion / BER v0.9**，已核对理论 `main` 提交 [`c494892ba12382b2f2d07cce330176257130626c`](https://github.com/iking-i/beca-architecture/commit/c494892ba12382b2f2d07cce330176257130626c)（2026-10-08）。现有实现及本地同步的 v0.8 文档仍保留原来源和历史结果。此次理论元数据更新不改变运行行为，不等于实验结果、行为验证或 L1；v0.9 将 `Continuity(A) != 0` 区分为实验延续条件，不能提升为通用核心公理。机器可读来源见 [THEORY_REFERENCE.json](THEORY_REFERENCE.json)。

非穷尽 realization 边界已进入上述正式 theory `main`：理论不要求穷尽组合、枚举全部 possible structures 或完成 global enumerative least-fixed-point closure 后才允许递归或现实行动继续。本次只同步正式理论引用，不改变已记录的研究结论或历史结果。

行为因果闭合审计见 [BEHAVIORAL_CAUSAL_CLOSURE.md](BEHAVIORAL_CAUSAL_CLOSURE.md)。当前内部历史可影响后续递归证据读取，**尚不能成为正式动作代码及参数的作者**。该历史审计只验证了限定的内部效应与独立对照，未宣称行为闭合通过。WORLD_ENTRY_FREEZE 的既有身体验收保持不变。

当前范围是 **L0 层内持续递归和当前有效极限反馈**，不声称已经验证向上递归、L1 或无限递归。正式 runtime 保留既有 V0-A / V0-B 基线边界；详情见 [BASELINE_CORRECTION_REPORT.md](BASELINE_CORRECTION_REPORT.md)。真实 A 的数据库、本机配置、凭据和运行日志保留在本地，不上传；完整清单见 [REPOSITORY_CONTENTS.md](REPOSITORY_CONTENTS.md)。

## 当前研究状态

**TYPED_OPERATIVE_CONNECTION_TEST_ONLY = PASS / COMPLETED / FROZEN**（2026-10-08）。
实现/验证锚点：`95d54d5b60783ace18eee8399ae3068158011379`；TC-T1～TC-T10 全部 PASS。
已记录专项 **24 passed**、相关 **124 passed / 13 subtests**、完整回归
**628 passed / 114 subtests**；13 项冻结源码哈希 MATCH。本次核对保存的代码、测试与机器证据，不重新运行实验。

在独立 TEST_ONLY ConnectionCore、合成观察和 FakeBridge 范围内，普通 integration
依据同通道精确 before→after 形成 **ObservedValue → ObservedValue** 定向连接。
后续普通递归实际使用已形成连接的端点构造 Pair，并将产品作为实际 expected operands。
两组不同历史形成相反连接，在材料与当前输入相同的检查点产生不同内容；
S1-only ablation：Pair 产品 **2 → 1**，实际操作数 **13 → 12**，重新插入恢复原内容。
连接与内容进入权威 Current State，ON/OFF 各自同一个 A / 数据库跨真实进程恢复并复用，
不依赖 Full Audit History replay，不重新形成 S1。S0/S1 表示和执行语义相同，来源标签不授予权限。

观察值、类型和身份来自环境/编码器；通用形成与 Pair 法则由外部给定。
不证明任意 typed-operand 连接、参数槽绑定、完整身体表达、表达采用权、身体执行权、
自主目标、真实世界因果律、behavioral causal closure、L1 或通用生成规律。
旧 CE NOT_READY、Operative Expression Binding NOT_READY 和初次失败记录原样保留，
不追溯升级；既有 unrelated untracked 材料不加入本次收口提交。
本次不修改 runtime、测试、caps、理论引用或冻结 evidence，不运行 Minecraft。
见 [closeout](TYPED_OPERATIVE_CONNECTION_CLOSEOUT.md) 与
[conversation handoff](TYPED_OPERATIVE_CONNECTION_CONVERSATION_HANDOFF.md)。

下一步首先独立审查并补充 `iking-i/beca-architecture` 的**个体／环境角色相对性及实际边界说明**。
理论更新必须有独立理论层依据，不得追溯修改本阶段验收结果；本次不更新理论仓库或理论引用。
理论更新之后，再研究实际形成的 typed connection 如何参与原生参数槽和值／引用绑定。
这里只记录交接顺序，不设计机制；下一实验阶段 **NOT_STARTED**。

### 历史 closeout — Native Body Operands TEST_ONLY

以下保留该阶段的冻结状态及当时下一问题，不作为当前实施授权。

**NATIVE_BODY_OPERANDS_IN_OPERATIVE_RECURSION = PASS / COMPLETED / FROZEN**（2026-10-08）。
实现/验证锚点：`257789144740d1e6468f00d7b7e380b4d45ba34c`；NBO-T1～NBO-T9 全部 PASS。
已记录专项 **20 passed**、相关 **104 passed / 13 subtests**、完整回归
**604 passed / 114 subtests**；13 项冻结源码哈希 MATCH。本次只核对既有代码与机器证据，不重新运行实验。

在独立 TEST_ONLY NativeCore、合成观察和 FakeBridge 范围内，环境声明的原生端口、
参数槽/合法域以及观察值/感知引用，成为普通 typed UnitRef 操作数。
经历形成的 S1 因果性地影响其进入普通 operative 读取和同一通用 Pair 构造；产品进入
实际 expected operands，材料与内容保存于权威 Current State，并在 ON/OFF 各自独立的
同一个 A / 数据库生命周期内跨真实进程恢复及复用，无需 Full Audit History replay。
S1-only ablation：可达原生材料 **12 → 0**，新增 Pair **15 → 0**，实际操作数 **32 → 4**；
恢复 S1 后构造内容恢复。全部可达材料并存，没有外部择一、sampler、binder 或专门 consumer。

能力身份与类型域来自环境，输入表示和通用 Pair 法则由外部机制给定。
本阶段**不证明完整表达、参数绑定关系、动作/参数作者权、表达采用权或身体执行权**。
历史引用不等于当前可执行目标；重复 channel/kind 模式保留首建输入 incidence。
最终 witness 为 16 Units + 47 content nodes = **63/64**，容量不变，不代表无限增长能力。

完整表达阶段原有 **CE NOT_READY** SPEC / VALIDATION.md/json 原样保留；
CE-T1～CE-T10 未改变、未通过。这些既有本地 untracked 材料不纳入本次收口提交。
旧实验和初次失败不改写；默认执行行为不变，既有 Core 修改仅为只读实验模式 admission guard。
见 [closeout](NATIVE_BODY_OPERANDS_CLOSEOUT.md) 与
[conversation handoff](NATIVE_BODY_OPERANDS_CONVERSATION_HANDOFF.md)。

下一问题仅冻结：**在身体端口、参数槽、合法值和感知引用已经成为可达递归操作数之后，现有普通递归构造能否形成具有完整参数绑定关系的原生身体表达？**
区分环境材料/类型约束、内部形成内容/绑定关系，以及尚未建立的采用/执行权。
优先复用现有递归构造，不预设固定动作策略，不将外部合法性校验当作内部作者权。
下一阶段 design / implementation / experiment **NOT_STARTED**；不接通身体、不运行 Minecraft。

### 历史 closeout — Generic Operative Content Construction TEST_ONLY

以下保留该阶段收口时的状态与下一问题，不作为当前实施授权。

**GENERIC_OPERATIVE_CONTENT_CONSTRUCTION_TEST_ONLY = PASS / COMPLETED / FROZEN**（2026-10-08）。
实现/验证锚点：`89f116798ef7f7251822199fdb4f665988fc28fa`；GC-T1～GC-T10 全部 PASS。
已记录专项 **24 passed**、相关 **80 passed / 13 subtests**、完整回归
**584 passed / 114 subtests**；13 项冻结源码哈希 MATCH。本次核对既有证据，不重跑实验或测试。

在独立 TEST_ONLY A 中，历史形成的 operative structure S1 能够通过已给定的通用 Pair
构造机制，因果性地参与新有类型内容 T1 的形成；形成内容进入权威 Current State，
跨真实进程恢复并再次参与普通构造。Pair 操作由外部提供，实际构造操作数与产品内容
受当前经历和 S1 影响；不证明构造操作本身由 A 自主创造。
S1-only ablation：新增 Pair **3 → 0**，实际 expected operands **8 → 4**；
重新插入 S1 恢复内容。总构造输出为 5 → 2，与新增产品数分别记录。
ON/OFF 两个独立生命周期均在同一个 A / 数据库内跨进程保存并复用全部 3 个新 T1 引用，
不依赖 Full Audit History replay。使用 synthetic observations / FakeBridge，没有运行 Minecraft。

初次专项失败、首轮完整回归失败和修复记录原样保留；Tk 初始化失败的具体宿主触发原因
仍 NOT_ESTABLISHED。旧冻结 FormalL0、测试、历史证据及理论引用不变。
默认执行行为不变；实现中的 Core 修改仅为实验状态 admission guard。
仍不证明任意内容生成、完整表达、动作与参数作者权、表达采用关系、身体执行权、
自主目标、自主动作选择、behavioral causal closure、L1/upward recursion 或通用生成规律。

见 [closeout](GENERIC_OPERATIVE_CONTENT_CONSTRUCTION_TEST_ONLY_CLOSEOUT.md) 与
[conversation handoff](GENERIC_OPERATIVE_CONTENT_CONSTRUCTION_TEST_ONLY_CONVERSATION_HANDOFF.md)。

下一问题仅冻结：**已经形成并可继续参与构造的 T1，能否通过同一套普通 operative 机制，
进一步形成包含动作 code、必要参数及引用关系的完整表达内容，而不由宿主固定策略替 A 填写或选择？**
只记录核对现有 typed Pair / 构造机制是否可复用的研究边界，不预设其足够。
不得另造独立决策系统、硬编码 Pair-to-action 映射或把 sampler/binder 结果冒充内部生成。
下一阶段 design / implementation / experiment **NOT_STARTED**；不接通身体、不运行 Minecraft。

### 历史 closeout — Formal A Continuous Operative Reentry TEST_ONLY

以下保留先前阶段收口时的状态与下一问题，不作为当前实施授权。

**FORMAL_A_CONTINUOUS_OPERATIVE_REENTRY = PASS / COMPLETED / FROZEN**（2026-10-08）。
实现/验证锚点：`1e28a00a401681efb304ec518ed672a12cea901f`；CR-T1～CR-T10 全部 PASS。
已记录专项 **28 passed**、相关 **161 passed / 23 subtests**、完整回归
**560 passed / 114 subtests**；13 项冻结源码哈希 MATCH，默认运行行为保持不变。
本次仅核对既有证据并收口，不重跑实验或测试。

在独立 TEST_ONLY ACore 生命周期中，同一个 A 的合成输入实际经历形成了 operative structure S1；S1 被原子写入权威 Current State，跨真实进程恢复后无需重新形成，即可在正常 ACore 状态转换中成为实际运行依赖。S0 与 S1 使用相同表示和执行机制；S1-only ablation 改变实际计算，来源标签不赋予执行特权，完整回归通过。
输入为 synthetic observations，使用 FakeBridge；不是正式 mainline A 或 Minecraft 实验。
每个 ON/OFF witness 各自保持同一个测试个体、同一数据库和递增 state version；
OFF 同样恢复 S1，不依赖 Full Audit History。进程重启后的首帧有既有 carrier gap，
后续普通 advance 实际使用 S1；不将 gap 改写为成功处理。

原始 **NOT_TESTABLE** 报告和 Tcl/Tk 失败日志保留；`ttk/utils.tcl` 读取错误的
具体触发原因仍 **NOT_ESTABLISHED**，独立验证环境通过不等于根因已查明。
默认 FormalL0 adoption、正式 mainline A adoption、身体表达作者权、自主动作选择、
自主目标、behavioral causal closure、L1/upward recursion 仍未证明。
旧 FormalL0 adoption / OH / BPC / FROI / GSC / CEC / Successor 和持久化结果不改写。

见 [closeout](FORMAL_A_CONTINUOUS_OPERATIVE_REENTRY_CLOSEOUT.md) 与
[conversation handoff](FORMAL_A_CONTINUOUS_OPERATIVE_REENTRY_CONVERSATION_HANDOFF.md)。

下一研究问题仅冻结：**已经由同一个 A 的实际经历形成、持续保存并正常重入的内部 operative structure，能否进一步参与 A 对外表达内容的形成，并通过结构消融证明其因果作用？**
下一阶段首先核对 ACore 身体表达准备路径、外部 selector、action code/参数绑定、
冻结 BPC 身体接口边界以及内部结构能否成为实际表达操作数。
不得预设固定 S1-to-action 映射；内部计算受影响不等于动作内容已由内部形成。
下一阶段 design / implementation / experiment **NOT_STARTED**；不要求直接运行 Minecraft。

### 历史 closeout — FormalL0 Operative Adoption TEST_ONLY

以下为先前隔离派生引擎阶段的冻结状态，包括其当时的下一问题；不作为当前工作授权。

**FORMALL0_OPERATIVE_ADOPTION_TEST_ONLY = PASS / COMPLETED / FROZEN**（2026-10-08）。
实现/验证锚点：`8b33097b746931b788ab5e72de66dd483af18edc`；FA-T1～FA-T10 全部 PASS。
已记录专项 **30 passed**、相关 **99 passed / 24 subtests**、完整回归
**532 passed / 114 subtests**；冻结 FormalL0 源码哈希 MATCH，默认 runtime 不变。
本次收口核对既有证据，不重跑实验或测试。

最强结论仅限隔离派生 FormalL0 引擎：S0 与历史形成的 S1 在真实测试 InternalState
中使用相同 representation / execution，S1 持久恢复并自然改变后续 ordinary advance
的实际操作数和比较；S1-only ablation、provenance neutrality 与重复复用均成立。
这不证明 canonical FormalL0、连续真实 A 或 Core/EventStore 已接入；不证明
Minecraft 作者权、behavioral causal closure 或 L1。迁移前 FA-T9 FAIL 与源码哈希
冲突原样保留，所有旧冻结结果不改写。

见 [closeout](FORMALL0_OPERATIVE_ADOPTION_TEST_ONLY_CLOSEOUT.md) 与
[conversation handoff](FORMALL0_OPERATIVE_ADOPTION_TEST_ONLY_CONVERSATION_HANDOFF.md)。

下一研究问题仅冻结：在不改变原有冻结 FormalL0 的前提下，如何让已经通过 TEST_ONLY 的 operative adoption 通过明确版本化的实验执行路径进入 ACore 和权威 Current State，使同一个实验个体在连续状态转换中真正使用后来形成的 operative structure？
边界：`ACore → authoritative Current State → versioned operative engine → formation + persistence → next ordinary advance → formed operative dependency`。
下一实现/实验 **NOT_STARTED**；本轮不设计、不实施、不运行 Minecraft。

### 历史 closeout — Operative Handoff TEST_ONLY

**历史 closeout（2026-10-08）：OPERATIVE_HANDOFF_TEST_ONLY = PASS / COMPLETED / FROZEN。**
实现与结果冻结提交：`7ca0ccdfd73c7c5132d7f3de54571b21c9e9d279`。
OH-T1–OH-T8 全部 PASS；专项 19 passed，冻结 GSC-0 controls 23 passed，
完整回归 502 passed / 114 subtests passed；diff-check / JSON / report reproduction PASS。

在最小 TEST_ONLY witness 中，初始提供与后来内部形成的同类型 operative edge
进入同一非特权执行机制；形成的边成为普通递归依赖，并通过 normal reentry、
edge-only ablation 和 structural reuse 验证。执行器不读取 provenance，也不依赖
specialized consumer。**TEST_ONLY M 不是已证明 FormalL0 应采用的最终机制。**

这不证明正式 A / CurrentStructure 接入、FormalL0 generic operative reentry、
真实 A 内部 operative 作者权、身体/动作/参数作者权、behavioral causal closure、
真实 Minecraft operative handoff、自主目标、生存目标、L1/upward recursion 或通用
Perfect Recursion。下一实验阶段仍为 **NOT_STARTED**；只允许已授权的只读接入审计。

见 [closeout](OPERATIVE_HANDOFF_TEST_ONLY_CLOSEOUT.md) 和
[conversation handoff](OPERATIVE_HANDOFF_TEST_ONLY_CONVERSATION_HANDOFF.md)。
原 BPC/FROI/Successor/GSC/CEC 及 Current State / Full Audit History 证据保持冻结。


**历史 closeout（2026-10-08）：Current State / Full Audit History 解耦与 Full History 可选记录真实验收已完成，PASS / COMPLETED / FROZEN。**
基础设施冻结提交 `0f8bf05a84ae68bd9aed66f738f9c4d3009edbe3`；完整回归
**483 passed / 114 subtests passed**，`git diff --check` PASS。独立真实验收使用同一测试 A：
**OFF A163→A200；OFF 恢复 A200→A243；ON 恢复 A243→A281**。OFF 期间完整审计历史不追加，
恢复后仍为同一 A；重新 ON 后从 **A244** 起记录，未回填 OFF 期间缺失历史，audit gap 被保留且不误判为损坏。
三次真实运行均受控结束，Core / Bridge exit code 均为 0。

该结果验证的工程边界是：**authoritative Current State 必须持续保存；Full Audit History 是可选的外部观察者记录，不是 A 连续存在的必要记忆。**
正式 selection、主线 A 状态及历史、FROI、sampler/binder、body 均未因验收改变。此前 sandbox `EACCES`
尝试保留为 **NOT_TESTABLE**；第一段真实 OFF 在固定预算内取得 8 次输入，12 次仅为辅助目标，未延长预算。
本地原始证据位于 `storage/recording-option-validation/run-20261007-63745/`，不随仓库发布。
见 [Current State / Full History handoff](CURRENT_STATE_FULL_HISTORY_CONVERSATION_HANDOFF.md)。
本 closeout **不自动开始下一研究阶段**。

### 历史 closeout（2026-10-07）：memory/runtime boundary long-run validation

**memory/runtime boundary long-run validation 已完成。**
运行实现 `ed88877535375f42a51cd479518cbb5673f28db2`；Individual
`A-24f4fd0f-e83a-4ea2-9db6-2c351c9cfe05`，Session
`S-f4a2c0a1-b26e-4503-974c-ea9cf27e1834`；最终 A6327 / event 62646。
已记录运行跨度 59 分 39.216 秒：2727 observations、920 条逐条核对的真实完整闭环；
Core sampled peak 86.39453125 MiB，未复现 512 MiB `core_ram_limit`。
`MEMORY_RUNTIME_BOUNDARY = PASS`、`LONG_RUNNING_REAL_BODY_WORLD_LOOP = PASS`；
`FULL_HISTORY_RAM_REGRESSION = NOT_OBSERVED`、`CORE_RAM_LIMIT_REGRESSION = NOT_OBSERVED`。
2722 个 formed organization 均记录 `external_history_loaded=false`，初始化
`raw_history_retained=false`；完整 EventStore 仍作为外部实验审计历史保留。

用户主动关闭承载实验的终端窗口：`STOP_REASON = USER_CLOSED_TERMINAL`，
不是程序内 Ctrl+C / controlled shutdown。没有 SESSION_ENDED 或完整 Core/Bridge
退出证据，故 `TERMINATION_OBSERVABILITY = NOT_VALIDATED`，不判 PASS 或 FAIL。
这不证明世界效果因果律、内部行为作者权、L1 或 Perfect Recursion 全部成立。
完整归档与交接见 [长程运行 handoff](LONG_RUN_CURRENT_STRUCTURE_CONVERSATION_HANDOFF.md)。
下一方向仅记录为 initial-constraint / A0 constraint audit：
**NOT_STARTED / NOT_IMPLEMENTED / NOT_YET_SPECIFIED**；本轮不开始审计或实现。

### 历史 BPC-LIVE-1 closeout 与解释纠正

以下保留此前阶段的状态、范围与证据，不替代上面的最新 FormalL0 Operative Adoption TEST_ONLY closeout。

**研究解释已纠正（2026-10-07）：** BPC-LIVE-1 仍为历史限定范围内的
**PASS / COMPLETED / FROZEN**，冻结提交为
`916ccf4f83243346341ea3e3cbf5e41e06991cff`。但 `Shared(C,O)` 的准确分类是
**REPRESENTED_RELATION**，不是已验证的 **OPERATIVE_CONNECTION**。
已验证的是关系形成、保存及专用 consumer 的读取/记录输出效应；尚未建立
generic operative structural mutation 或内部行为作者权。
见 [正式解释纠错](OPERATIVE_CONNECTION_ERRATUM.md)。后文历史 “connection”
是阶段/对象命名，不能作为 operative topology 已成立的证据。
BPC-R2 的 fixed-witness 机械执行链与 BPC-LIVE-1 的 live 保存/读取链不能自动
拼成未实际发生的 operative live loop。所有旧 PASS、失败记录和 evidence 保留；
下一实验阶段仍为 **NOT_STARTED**。

**BPC-LIVE-1 = PASS / COMPLETED / FROZEN。**
真实观察到的原生 O 进入连续运行 A 的递归形成空间；当前真实输入形成 C，
在线形成并保存 represented C ↔ O，后续真实轮次由专用 consumer 从同一 A
的内部状态读取原 relation；该结果进入记录的 processing/output，未建立普通
FormalL0 经 C 自然运行到 O 的 operative dependency。
Canonical 在 A7/E3 提交 47 条连接，A8/E4 实际消费这些连接；NC1–NC6 全部 PASS。
没有 perform、sampler、binder、mapping、fallback、historical replay 或 detached BPC。

A8 成功读取旧的 COMPLETE 组织后，新形成尝试返回 `RESOURCE_LIMIT`。
该限制完整保留，不影响本阶段已验证的目标链；没有提高 cap，不证明无限持续能力。
两次先前 NOT_TESTABLE 记录不被最终 PASS 覆盖。

实现证据提交 `68b8ad64b5f68edd5151c7ce73af8f3657281027`；
[最终验收](experimental/live_body_connection/LIVE_VALIDATION.md)、
[JSON](experimental/live_body_connection/LIVE_VALIDATION.json)、
[收口](experimental/live_body_connection/CLOSEOUT.md) 和
[handoff](BPC_LIVE_1_CONVERSATION_HANDOFF.md)。
专项 41 passed，已有相关回归 377 passed / 90 subtests passed，收口专项 41 passed。
不证明 live 连接已作者化动作、世界效果因果律、一般参数形成、自主目标/动作选择、
behavioral causal closure、L1 或普遍生成律。下一阶段 **NOT_STARTED**；本次不定义下一问题。

### 历史 BPC-R2 收口检查点

以下 BPC-R2 的 nonclaims / 下一边界是当时的历史状态；不改写旧证据，也不作为当前工作指令。

**BPC-R2 已完成并冻结：COMPLETED / FROZEN，PASS。**
限定结论：固定 TEST_ONLY witness 中，受支持的真实历史形成 `C ↔ O` 为后续无参数
primitive expression 提供原生 action code；该 exact expression 经既有身体通道完成
恰好一次真实执行并收到匹配回执，未调用 sampler、binder、value-to-action mapping、fallback 或 retry。
O 为既有 `(catalog version=2, code=0)`，parameters 为 `{}`，并非内部创造的新能力。
BPC-R1 已形成的 S/C 被直接读取，未更换 witness、重算 formation 或改写旧证据。
独立 TEST_ONLY body 使用端口 61875；不是正在运行的正式 A CurrentStructure 接入。

实现/结果提交：`386e50eb26803ffe61a9cd863403b9c9468e4958`；收口提交为包含
[BPC-R2 handoff](BPC_R2_CONVERSATION_HANDOFF.md) 的独立提交。
见 [规格](experimental/body_port_real2/SPEC.md)、
[原验收](experimental/body_port_real2/VALIDATION.md)、
[机器报告](experimental/body_port_real2/VALIDATION.json) 与
[收口核对](experimental/body_port_real2/CLOSEOUT_VALIDATION.json)。
专项 **15 passed**；8 项负对照 PASS；相关回归 **336 passed / 90 subtests passed**；
Successor-0 未重新运行。closeout 只核对可信执行记录及源码/证据哈希，没有再次执行 Minecraft。

不证明 `C ↔ O` 在持续运行的 A CurrentStructure 内形成，也不证明 live A 后续当前输入
实际消费了连接；不证明 world effect causal law、一般参数形成、自主目标、自主动作选择、
behavioral causal closure、L1/upward recursion 或 universal generative dynamics。
正式 runtime、catalog、caps、BPC-0/BPC-R1 及其他冻结阶段和理论均未修改。

下一阶段 **NOT_STARTED**，只记录边界：
`live current input → A's continuously running CurrentStructure → history-formed C ↔ O inside that same structure → later recursive processing actually consumes that C ↔ O`。
`O → expression → real body execution` 已在 BPC-R2 限定范围内验证，后半链不是下一阶段需重新验证的问题。
本轮不设计或实现下一阶段。

BPC-R1 保留真实历史 formation PASS：实现 `5fd85389e39801a0899eb0b1a4296796c2427783`，
收口 `822ee5d05ba83c68b9a9a76e7be049f2be12c031`；29 项专项、12 项负对照及
321 passed / 90 subtests 的历史回归不改写。见 [BPC-R1 handoff](BPC_R1_CONVERSATION_HANDOFF.md)。

BPC-0 继续保留 synthetic TEST_ONLY witness PASS：实现 `996b6fab6d055159f1336085ec80e5a7a4f07613`，
收口 `ebdcbc73d060ce894513f35853ed01c5d47836ef`；原 synthetic 身体输出证据、17 项专项测试和
292 项历史回归结果不改写。见 [BPC-0 handoff](BPC0_CONVERSATION_HANDOFF.md)。
后文 Successor-0 阶段及其下一阶段说明是该历史收口检查点，不能替代上面的当前状态。
正式 runtime 仍无已验证的内部行为作者链。

当前权威状态索引是 [RESEARCH_STATUS.md](RESEARCH_STATUS.md) / [RESEARCH_STATUS.json](RESEARCH_STATUS.json)。研究证据已经越过早期 `CURRENT_STRUCTURE_GENERATION_AUDIT.md` 的“尚未找到新组织 producer”检查点：在冻结的 CO-WAC-1 下，后续 [CURRENT_ORGANIZATION_SCOPE_AUDIT.md](CURRENT_ORGANIZATION_SCOPE_AUDIT.md) 将对象边界拆开后，`O-G0-1 derived structural graph` 在有限 TEST_ONLY GSC-0 范围内取得 **C1–C5 全部 PASS**，可作为“新因果有效组织实例”的有限正例；这不等于新的组织方式、行为作者权、L1 或 Perfect Recursion 的普遍生成律。

随后 [GSC0_RECURSIVE_RESULT_DEPENDENCE.md](GSC0_RECURSIVE_RESULT_DEPENDENCE.md) 对两个有限 fixture 做 `A_FULL_PREVIOUS / B_DERIVED_ABLATION / C_FRESH_RECOMPUTE` 反事实，实际得到 `A=B=C`，分类为 `DERIVED_RESULT_NOT_CAUSALLY_NECESSARY`：前轮已物化派生结果在这两个案例中不是下一轮结果的独立必要条件，保留的原始历史材料足以由固定机制重算同一组织。该结果不表示历史无关，也不推翻 O-G0-1 的组织效力。

FROI-1 已实现：`implementation = IMPLEMENTED`。历史验收 **v2 = PARTIAL**，冻结提交 `9f7a8b7a4186ff58b7ed279f9f64071999644814`，结果保留不变；当前验收 **v3 = PASS**，冻结提交 `326dbb165f41c2ff32c43230810148990fbf0daf`，**T1–T5 全部 PASS**。原 [FROI-1 spec](FORMAL_RECURSIVE_ORGANIZATION_INTEGRATION_SPEC.md) 保持冻结；测量边界见 [v3 harness](FROI_ACCEPTANCE_HARNESS_V3.md) 和 [v3 freeze](FROI_ACCEPTANCE_FREEZE_V3.json)。

已建立的限定因果链为：

```text
real accumulated history + current structural read input
→ fixed GSC-0
→ formed COMPLETE O-G0-1 organization
→ actual FormalL0 internal consumer
→ measurable causal internal-processing difference
→ read-failure consequence can enter later FormalL0 processing
```

v3 T4 使用 **TEST_ONLY HISTORICAL COUNTERFACTUAL WITNESS**：原 A16 T2 的固定真实历史前缀 15 / 12、已保存的 COMPLETE / UNRESOLVED_REFERENCE 分支及其 detached continuation，下一输入来自已记录的真实 WORLD_OBSERVATION。它不是 formal-live natural failure、不是新的 Minecraft run 或新的 A，也不证明 world-facing behavioral authorship。v3 复用并核验已有执行证据，没有重新执行 producer 或 continuation；所有实际用于验收的组织均 COMPLETE。v2 PARTIAL 未被追溯改写。原运行 commit 仍为 `MATERIAL_UNAVAILABLE`。

本机报告为 `storage/acceptance/froi-v3-326dbb1/report.md` / `report.json`；原数据库和 v2 报告保持不变，运行数据不随仓库发布。

`CEC0_MINIMAL_REAL_WITNESS = PASS`：独立 TEST_ONLY 个体采集的 10 条 T0-valid 真实 Minecraft experiences 中，按事前冻结的最小子集规则选出的 2 条真实 witness 已通过原 CEC-0 T1–T6，形成并消费 `opaque control ↔ exact experienced consequence`。其范围是原 UnitRef/change-shape identity 的 temporal association，不证明 causal law、generalization、parameter semantics、action selection、action authorship 或 imitation。原正式 session 的 `INSUFFICIENT_CLEAN_HISTORY` 与完整 10-record batch 的 `RESOURCE_LIMIT` 均保留，不被最小 witness 的 PASS 覆盖。本机证据见 `storage/validation/CEC0-REAL-MINIMAL-WITNESS-001/validation.json`。

Cross-actor saved-real-data 中有 588 条 external change、39 条 self change 和 4 对 exact axis/signed-delta pair，`REPRESENTATION_ONLY_REIFICATION_POSSIBLE = YES`。但同一选定真实 witness（包含负对照）需要 17 个不可约 node：GSC-0 在 16-node 条件下返回 `RESOURCE_LIMIT`；独立 GSC-0C 仅将 nodes 固定倍增至 32 后，在 composition workspace `300002 > 300000` 处返回 `RESOURCE_LIMIT`。两者 CR-T1/CR-T2 为 PASS，CR-T3–T6 为 NOT_TESTABLE，cross-actor correspondence 的完整形成与消费保持 **UNRESOLVED**，不能判为 FAILED 或 validated。

`CURRENT_COMBINATORIAL_EXPLOSION_CLASS = GSC0_REALIZATION_LIMIT`；`NEW_GENERATIVE_MECHANISM_REQUIRED = UNRESOLVED`；`GSC2_REACHED = NOT_YET`。GSC-0 保持有限 TEST_ONLY prototype PASSED，并已完成**本研究线中作为有限穷尽闭包原型的当前角色**；这不排除未来实验用途。Exhaustive composition、global enumerative closure、flat all-composite generation 和 full logical provenance enumeration 属于该 realization 的具体实验选择，不是普遍理论要求；必要因果来源仍须可核对。当前不继续扩容或优化其 exhaustive closure，也不替换正式运行时。

**Successor-0 已独立实现并验收 PASS**：冻结实现提交 `91eac86632af528251d73ecf4c80f283c87fe019`，状态收口 `13337f47a44ace65cb1704978dee01f82791c22d`，维护回归提交 `e207c655e065f075a3235669bc6ce428b5140667`（完整 Python suite **291/291 PASS**），单元测试 **16/16 PASS**，**S0-T1–T10 全部 PASS**。范围严格为 TEST_ONLY、externally supplied opaque `RequireBound`、unique producer、typed `Transfer`、acyclic fixture、requirement-rooted local formation。证据见 [Successor-0 报告](experimental/successor0/SUCCESSOR0_VALIDATION.md) / [JSON](experimental/successor0/SUCCESSOR0_VALIDATION.json)。

| 条件 | 实际证据 |
|---|---|
| A | activated=2，derived bindings=2，formed supports=6；consumer `RESOLVED(q,V)` |
| B | 无 requirement root；activated=0，derived bindings=0；无 S |
| C | 移除必要 relation；activated=1，derived bindings=0；consumer `UNRESOLVED` |
| D10 / D100 / D1000 | S 内容与 identity 均与 A 相同；distractor activation / derived facts 均为 0 |
| Consumer / necessary support ablation | 均 PASS；屏蔽形成组织或必要支持后 `UNRESOLVED`，不重跑 formation |

限定结论：在冻结 Successor-0 TEST_ONLY 范围内，外部提供的 opaque requirement 能通过 exact structural incidence 因果地驱动局部形成，产生随后被实际消费的组织，无需全局穷尽结构枚举。这证明一个具体候选 realization，不证明 Perfect Recursion 唯一或通用生成机制；不改写 GSC-0、CEC-0 或 FROI 历史结果。GSC-0 继续保留为已验证的 finite exhaustive-closure prototype，Successor-0 是独立的非穷尽局部形成候选，不修改正式 runtime。

**历史 Successor-0 收口检查点：当时阶段已完成、下一阶段尚未开始。** 非穷尽局部形成已有具体候选 realization 的 scoped PASS，不再笼统标为 `SUCCESSOR_REALIZATION_DIRECTION = UNRESOLVED`。FROI-1 也已完成其限定实验角色。

该历史检查点的下一候选研究边界记录为 **formed internal organization → complete primitive body expression**：当前尚缺内部组织到 action code 与全部 required parameters 的已验证因果边；此边界 **not yet designed / not started**，本次没有设计或实现新机制。Multiple producer、internal requirement origin、relation/mechanics recursive formation 保持开放，不规定优先级。

Successor-0 不证明一般 requirement origin、“enough”、“executable” 或所有 realization 的 selector leakage 已解决；这些 `successor_unresolved_boundary` 是开放研究问题，不自动成为已确认 blocker。它也不证明 world-facing 链或普遍生成律。旧规格中的 READY、旧报告的 next step 和旧测试数量仅描述当时的实验/提交；其时间与对象范围见 [当前历史索引](RESEARCH_STATUS.md#14-historical-evidence-policy)，原文与冻结结果保留。

`INTERNAL_REQUIREMENT_ORIGIN`、`MULTIPLE_PRODUCER_FORMATION`、`CYCLIC_LOCAL_FORMATION`、`RECURSIVE_FORMATION_OF_RELATIONS_OR_MECHANICS` 均为 `UNRESOLVED`；`INTERNALLY_AUTHORED_COMPLETE_BODY_EXPRESSION`、`MINECRAFT_WORLD_FACING_SUCCESSOR` 均为 `NOT VALIDATED`；`UNIVERSAL_GENERATIVE_DYNAMICS = NOT ESTABLISHED`。外部提供 requirement 不等于内部目标形成，单 producer 不等于多方案自主选择，本轮未运行 Minecraft。

`BEHAVIORAL_CAUSAL_CLOSURE = FAILED / NOT YET PASSED`；formal action sampler 和 parameter binding 仍为 `EXTERNAL_FIXED_POLICY`；internally authored Minecraft action、L1 / upward recursion 均 `NOT VALIDATED`；Perfect Recursion universal generative law 仍 `NOT ESTABLISHED`。冻结规格及所有历史 PASS / RESOURCE_LIMIT / PARTIAL 结果不改写。

旧的 `CURRENT_ORGANIZATION_CRITERION.md` / `CURRENT_ORGANIZATION_AUDIT.md` 机制级矩阵作为历史证据保留；其中“共同最早未解决 C3”已经被后续对象一致性审计取代，不能再作为当前总状态。后续工作也不得预设 Closure、Composite、OutwardPort、Role、一对多或多对一就是 Perfect Recursion 的普遍答案。

## 新克隆的首次安装

需要 Python 3.11 或更新版本、Node.js 22 或更新版本，以及与锁定 Mineflayer 版本兼容的 Minecraft Java 世界。现有测试使用 Java 26.1。

在克隆后的仓库根目录运行（Windows PowerShell）：

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
npm --prefix minecraft ci
Copy-Item minecraft/config.example.json minecraft/config.json
```

首次编辑生成的 `minecraft/config.json`，填写服务器地址和独立身体账号即可。局域网当前端口可以在启动时输入或通过 `--port` 指定。模板的 `25565` 是常见服务器示例端口，不是当前电脑的运行端口。

安装后直接打开图形启动器。在窗口中选择已有 A；**仅在需要新个体时**点击“新建个体 A”并输入名称：

```powershell
.\.venv\Scripts\python.exe main.py
```

“新建个体 A”复用正式初始化，生成 `individual/lifetime.json` 和 `storage/individuals/A-<uuid>/`，保留旧历史。`individual/lifetime.example.json` 只说明格式，**不要复制成运行身份**。已有 A 的电脑正常重启只执行 `main.py`，不要为每次 Session 重新初始化。Linux/macOS 使用 `python3` 创建环境，并把后续 Python 路径改为 `.venv/bin/python`；无图形环境使用显式 CLI 参数。

在第一、二阶段的身体接口、唯一实验身份、连续状态链、SQLite 和外部 Supervisor 上增加最小内部递归。正常运行路径不使用原来的固定前进脚本。没有引入 LLM、语言知识、Minecraft 攻略、高级任务、自我修改、自我复制或自主联网。

当前是外部初始化 k_actual=1 的单过程正式基线，容量 N 并不提供自主分化能力，不能称为 A 自主选择不分化。该正式 runtime 基线目标仅为 V0-A / V0-B：L0 内的结果反馈和真实有限记忆后果进入递归；architecture-limit recognition=not_observed，不进入 V0-C。正式路径已经禁用旧的固定分化、分辨率减半、淘汰和探索评分，能力接口保留。完整审计与能力边界见 [FORMAL_L0_EXPERIMENT.md](FORMAL_L0_EXPERIMENT.md)。

程序、进程、数据库、游戏角色都是承载或能力结构。`individual_id` 是工程标记；`A0 → A1 → A2` 表示同一个体的连续状态变化。数据库属于 A 的生命周期，Experiment Session 是其中一段运行记录。当前 A 的身份和数据库由 `individual/lifetime.json` 固定。

## 启动和验收

完成上述安装后，无需重复安装依赖或 Minecraft。在 Java 26.1 测试世界开放局域网，然后正常启动项目。无参数运行会显示中文启动器：选择已有 A 或新建 A，填入聊天栏显示的端口，点击“启动实验”。局域网重新开放后端口可能改变，**无需修改配置文件**。不要同时启动使用同一个身体账号的其他工具。

```powershell
# 在仓库根目录运行
.\.venv\Scripts\python.exe main.py
```

启动器默认勾选 **FROI-1**，端口默认读取 `minecraft/config.json`。本次端口不会写回配置。列表显示名称、身份、角色、最新 A 状态版本、Session 数量、创建时间和路径；★ 表示当前已固定选择。切换只改变外部选择指针与目录索引，不初始化或改写目标数据库。有活动个体锁时拒绝切换；FROI 已锁定的个体不能取消 FROI 后启动。取消窗口不会启动 Core；此前明确点击新建所创建的 A 仍会保留。

数据库缺失时，创建新 A 需要单独确认，不自动替换原身份。这些 GUI 操作均属于实验者管理，不是 A 的递归或自主决策。详情与验证见 [WINDOWS_LAUNCHER_REPORT.md](WINDOWS_LAUNCHER_REPORT.md)。

也可以直接指定本次端口，省去启动询问（把示例数字替换为游戏显示的端口）：

```powershell
.\.venv\Scripts\python.exe main.py --froi --port 50102
```

任何显式 CLI 参数均跳过 GUI，保持原命令行为：`--port` 与 `--minecraft-port` 等价，`--use-config-port` 使用配置端口，显式 `--froi` 仍可走原终端端口询问。无图形环境请使用这些显式参数；无参数且无法打开 GUI 时会报错退出，不等待不可见窗口。CLI 不传 `--froi` 仍是原 FormalL0，已锁定 FROI 的生命周期需保留该选项。端口覆盖只用于当前启动及其身体重连，原配置和 A 的身份、状态版本不重置。Session 环境记录实际连接端口及 `minecraft_port_override`；`configuration_hash` 仍是原配置文件的哈希。当前运行中再次开放局域网改变端口时，应结束当前运行，再以新端口启动并沿用同一 A。

默认持续运行并记录完整历史，没有 1000 次状态变化的停止门槛。每个 A 的数据单独放在 `storage/individuals/A-<uuid>/`，同一 A 的多个 Session 共用该文件夹。当前路径由本地生成的 `individual/lifetime.json` 指定，结束 Session 或重启沿用同一身份和全局版本。本地目录索引为 `storage/index.json`，不随 GitHub 发布；说明见 [storage/README.md](storage/README.md)。

如果要从零开始测试另一个 A，先退出正在运行的项目，再执行以下命令。它创建新身份和独立文件夹，保留旧 A 的全部历史，不会覆盖或继承旧结构：

```powershell
.\.venv\Scripts\python.exe -m individual.lifetime initialize --label "新一轮测试"
.\.venv\Scripts\python.exe main.py
```

如果旧数据库已被移走或删除，但 `individual/lifetime.json` 仍指向它，普通启动会拒绝，默认初始化也会提示缺失。只有明确要创建**新的 A**时，使用：

```powershell
.\.venv\Scripts\python.exe -m individual.lifetime initialize --replace-missing-selection --label "新一轮测试"
```

这个显式入口把旧选择文件原样备份到新 A 目录的 `previous-selection.json`，记录原数据库缺失，创建新身份；不会宣称恢复了旧 A。其他已有数据保持原样。该选项不绕过已有数据库的身份校验或正在运行的写入租约。之后只运行 `main.py`，不要每次初始化。

默认启动使用 formal_l0。只读审计本阶段证据：

```powershell
.\.venv\Scripts\python.exe -m individual.experiment_audit --session-id latest --sample
```

审计输出层内递归、真实容量失败、行为上绑定的极限、后果重入、外部策略影响和内部关系证据变化。`baseline_goal_observed` 只验收 V0-A / V0-B，并要求容量锁、raw 分离和动作归属检查有效；`--verify-loop` 使用此基线判据。`recognition_status=not_observed`、`formal_stage_goal_observed=false` 和 `upward_recursion_observed=false` 保留，明确更强理论目标未验证。信息整合不算升层。

| 命令 | 作用 |
| --- | --- |
| `pause` | 停止新动作，观察、核心运行和记录继续 |
| `resume` | 恢复当前实验的动作调度，ID 不变 |
| `status` | 查看状态、CPU、RAM 和存活情况 |
| `end_session` / `begin_session` | 在同一 Core 内结束或开启 Session，内部结构保留 |
| `new_session` | 切换到下一 Session，Core、个体 ID 和全局版本持续 |
| `terminate` / `exit` / Ctrl+C | 结束当前 Session 并关闭载体；下次仍读取此生命周期 |

正常退出先停止新动作，追加 SESSION_ENDED 并保留内部结构与递归过程，随后关闭 Bridge 和 Core。`--duration` 是实验者设定的 Session 时间限制，默认 0（无限制）。`--verify-loop` 只检查当前 Session 的证据，不拿以前的闭环直接验收新 Session。`--smoke-policy` 才会使用第二阶段的调试脚本；其余路径不加载该策略。

## 正式条件锁与旧历史

第一次正式 Session 会把七项逻辑容量保存到 `InternalState.l0_state.locked_caps`，并保存 `locked_resource_caps`、`formal_condition_id`、`baseline_version=formal_l0_v0_ab_2`。正常启动由 Supervisor 提供四项 CPU/RAM/磁盘阈值及四项身体采样容量，一并锁定。默认采样值与 Mineflayer 配置校验一致。端口变化不改变这些容量。

重启和切换 Session 必须沿用这些条件。修改容量会在开启 Session、记录中断恢复或 Supervisor 日志前被拒绝，不自动迁移、扩容、缩容、删数据或创建替代 A；请恢复原配置后继续。尚未保存新锁的旧正式历史保留并明确拒绝自动升级，本轮不会替你改变主线选择。另设条件应由实验者明确安排；当前没有同一 A 解锁条件的运行接口。

原始容量后果与审计解释严格分开，字段清单见 [FORMAL_L0_EXPERIMENT.md](FORMAL_L0_EXPERIMENT.md)。游戏能力属于 A 可用载体能力，但正式动作代码和参数仍由外部初始采样规则选择；因此 `initiator=external_fixed_policy`，不能称为自主形成策略。

## A0 的最小结构

`AState` 保留第二阶段所有字段，并新增 `observation_frame`、`internal_state`。A0 中单元、关系、过程、经历窗口为空，只有初始解释机制需要的少量参数和动作试探状态。

```text
AState
  individual_id / state_version / started_at / last_update_at
  session_id / carrier_epoch
  environment_sequence / status / continuity_required = true
  latest_observation / latest_action
  health / hunger / position / inventory_summary
  observation_frame
  internal_state
    units / relations / active_processes
    observation_history_window / action_history_window
    detected_changes / resource_state
    generation_parameters / exploration_state
    latest_integration / latest_feedback / latest_generation
    latest_structure_changes / continuity_incidents / process_archive
    policy_registry / parameter_sources / policy_migration_status / body_capabilities
```

原始 Mineflayer 观察和人工调试映射只供记录、检查；正常结构引擎收到的是数值帧，不读取原始对象名称。没有敌人、食物、房屋、夜晚等预设概念。

## ObservationFrame

```text
frame_id / sequence_id / timestamp
encoding_namespace / body_epoch
self_channels                 # 数值通道 ID → 数值
spatial_data                  # 位置、朝向数值
nearby_data                   # 对象 ID、类型编码、相对位置、数量
numeric_channels              # 全部数值通道
coverage                      # 未加载、截断等采样边界
 delta
   change_id / previous_frame_id / frame_id
   changes                    # 增加、减少、出现、消失或未观测到
   maintained_channels / cochanged_channels
   after_action_ids / sample_gap
```

通道 ID 来自固定编码布局，方块/物品/实体使用游戏协议的类型编号，协议版本作为编码命名空间。缺编号的兼容输入只在编码边界被转换为无意义符号，不解释名称含义。人类名称单独存入 `SENSOR_DEBUG_MAPPING` 事件，不进入递归的判断条件。名称改为“food”或“enemy”而编号不变时，测试中的帧、结构参数和动作选择完全一致。

视野来自 Mineflayer 的已加载世界数据，不是屏幕图像。身体采样半径、数量、空气过滤和协议编码仍是外部接口条件。存在采样截断时，缺失通道保守记录为“未观测到”，不冒充对象真实消失。重连/死亡造成的采样断层不用于建立连续动作因果关系。

## RecursiveProcess（旧调试路径；不作为正式分化策略）

正式实现见 `individual/formal_l0.py`：一个持久过程接收每次连续观察，读取前次整合返回的关系引用，并进行新的证据核对。容量不足拒绝写入，原记录保留，原始失败进入下一输入；不会依据新结果、稳定性或压力改变数量。下面保留旧引擎的数据说明，只有独立调试夹具或显式 `--legacy-policy-debug` 才使用它。正式历史禁止重新进入旧适应引擎。

```text
process_id / origin_state_version / input_pattern
question                      # 数值条件通道、当前分辨率、分支编号
hypothesis                    # 结果计数及条件区间内的结果计数
attempts / observations / output / status
last_information_sequence
```

变化模式尚不能被当前关系稳定描述时产生问题过程。每次收到与其问题相关的新经历，立即 `publish_partial_result()`，不等待最终答案。不同分支实际检查不同数值通道；分辨率用于计算条件区间，并进入条件证据，不能只改一个展示字段。

生命周期支持 `ACTIVE / PAUSED / MERGED / SUPERSEDED / TERMINATED`。充分的暂时信息、没有新信息、等价问题合并、条件变化、容量不足和外部结束都会形成事件。已暂时稳定的问题不因“需要永久递归”而无限重新启动，监测到反例则重新提出问题。

## 内部结构怎样变化（旧固定策略；正式路径禁用）

数值差异形成描述性单元，单元随重复观察强化，未重复的单元衰减，工作容量不足时归档。提供单元合并操作；当前自动整合记录候选关系条件、合并等价递归问题。`split` 操作标签本身不代表已经生成高层结构，不声称已经发现了跨模式的概念等价。

过程提出暂时的 `X + action_code → Y`。整合对同一经历去重：多个过程上传同一条经历只增加一次关系证据。重复结果强化证据；出现 `X → Z` 时保留 Y、Z，降低无条件关系的适用性，记录候选条件并保持 unresolved。关系容量不足时归档整个关系，连同罕见结果保留在事件历史中，不筛掉少数结果。

向下反馈修改当前 `default_quantity`、按模式的数量、条件分辨率。下一次生成从这些内部参数读取数量，并记录源整合 ID、源状态版本、请求数量和实际获配数量。实际数量还受外部容量制约，不能把配额不足造成的减少误认为内部策略变化。

正式 Minecraft 身体清单现登记 47 项：39 项低层通道及 8 项保留的调试便利接口。包括独立保持/释放按键、主副手、挖掘开始/中止/结束、手动重生、原生槽位输入及条件性离床/下坐骑。旧编码 0、1、2 保留原义；新增能力通过数字槽位和当前对象引用调用，全部标记 BODY_CAPABILITY，能力清单和底层对应见 [BODY_CAPABILITIES.md](BODY_CAPABILITIES.md)。World-entry 保真边界、启动阻塞及真实验收见 [WORLD_ENTRY_AUDIT.md](WORLD_ENTRY_AUDIT.md)，尚不能宣称覆盖全部普通玩家条件界面。该评分说明仅适用于历史 legacy_policy_debug：未解程度和尝试次数参与评分，平分用随机序列。正式 formal_l0 使用 uniform available capability sampling（既有 LCG 模运算），不读取 attempts / unresolved，也不根据 limit 决定动作。参数取样明确登记为 INITIAL_EXTERNAL_POLICY，不冒称为学习结果。没有对象名称规则、健康奖励、死亡扣分、配方查询或高级任务。

完整链路记录帧 ID、变化 ID、动作 ID、过程 ID、部分输出 ID、整合 ID、生成 ID、源状态版本。记录的是时序关联和候选条件，当前不自动宣称发现了因果定律。

## 实际日志和验证

第三阶段旧版曾在固定玻璃区域通过真实 Java 26.1 验收；历史数据与日志样例见 [VALIDATION_STAGE3.md](VALIDATION_STAGE3.md)，数据库为 `storage/individuals/A-2eb28d2a-d5f6-4ef3-9ade-91e24f803eab/stage3-final.db`。这些独立 ID 的旧实验保留，不合并成新 A 的过去。这些是历史记录位置，不能据此判断本机当前主线或文件仍存在；当前选择只以本机 `individual/lifetime.json` 为准。

```powershell
.\.venv\Scripts\python.exe -m individual.inspect --db storage/individuals/A-2eb28d2a-d5f6-4ef3-9ade-91e24f803eab/stage3-final.db --history --limit 40
.\.venv\Scripts\python.exe -m individual.experiment_audit --db storage/individuals/A-2eb28d2a-d5f6-4ef3-9ade-91e24f803eab/stage3-final.db --sample --output storage/individuals/A-2eb28d2a-d5f6-4ef3-9ade-91e24f803eab/reports/stage3-final-report.json
```

查看完整状态历史和某次整合的输入：

```sql
SELECT state_version, snapshot FROM states ORDER BY state_version;
SELECT event_sequence, state_version, event_type, payload
FROM events ORDER BY event_sequence;
SELECT state_version, payload FROM events
WHERE event_type IN ('RECURSIVE_PARTIAL_OUTPUT', 'INTEGRATION_COMPLETED',
                     'DOWNWARD_FEEDBACK_UPDATED', 'RECURSION_GENERATED',
                     'COUNTEREXAMPLE_RETAINED')
ORDER BY event_sequence;
```

每次对外可见状态更新均在同一 SQLite 事务中追加状态、原因事件、各子事件和 `STATE_UPDATED`。事务失败不会让内存状态越过已提交历史。三个历史表禁止更新和删除。运行中的检查使用同一只读事务，避免将两个时间点的数据混成一个结果。

## 外部固定机制与 A 的可变结构（旧实现审计）

| 分类 | 实际内容 |
| --- | --- |
| CORE_MECHANISM | 身份记录、事件循环、Bridge、动作执行器、数值编码、差异检测、问题解释器、证据去重、SQLite |
| ENVIRONMENT_CONSTRAINT | 身体采样、可用接口、最大工作容量、测得资源、Supervisor 权限与人工停止 |
| INITIAL_EXTERNAL_POLICY | 探索评分、选择方式、暂时稳定判据、数量/分辨率更新规则、通道排序、资源使用与淘汰、强度更新与归档顺序 |
| 经历形成的可变数据 | 单元、关系、证据、候选条件、问题假设、尝试次数、当前数量与分辨率及其历史来源 |
| INTERNAL_VARIABLE_POLICY | 当前尚无已验证的来源迁移；固定规则改变参数不能算作自主策略形成 |

部分参数（例如窗口和暂时稳定阈值）已经作为数据保存，但本阶段没有实现它们全部自动改写。不要把“存成数据”说成“已经发生递归修改”。数量、条件分辨率和问题选择的变化已经接入真实执行路径。

默认物理工作上限：8 个过程、64 个单元、96 个关系、每关系 64 种结果、6 帧工作窗口、4 条近期证据引用、16 个数值条件通道。完整观察和输出留在日志中，这些数目不是理论上限，也不是 A 从一开始就知道了所有环境限制。

Supervisor 不属于 A。它单向送入实际 CPU/RAM 样本，A 仅获得数值资源压力；Core 输出只能作为遥测，不能修改外部限额。仍使用监测与超限终止，不是 OS 硬配额/容器隔离。

## 连续性和当前 TODO

`Continuity(A) != 0` 保留为个体级实验约束，不转换为普通奖励函数。记录身体死亡、连接中断与近期观察/动作的关联，标记为局部承载事件，不自动等同于 A 死亡。

SQLite 保存 A 的全生命周期状态链，Session 重启读取已提交的当前状态，不重建身份。完整载体停止造成的间隙会记录为中断；数据库标记本身不证明物理连续。保存历史快照与复制分支均可执行，分支必须标记为不同身份、不是原始主线。详情与操作见 [LIFETIME_STORAGE.md](LIFETIME_STORAGE.md)。

实际运行中完整 JSON 快照的磁盘开销较大：第一轮 647 个状态版本约占 389 MiB。当前没有压缩/长期归档，默认持续运行会继续增长。保留历史同时降低冗余写入、长期磁盘管理、更多物理条件下的反例检验、自动发现单元等价仍是后续工程工作。本阶段没有继续增加语言、长期知识、高级游戏行为或自我修改。

## 项目结构和检查

```text
main.py / requirements.txt / README.md
STAGE2.md / VALIDATION.md / VALIDATION_STAGE3.md
individual/
  identity.py / state.py / events.py / core.py / bridge.py / lifetime.py / lifetime.json
  observation.py / change_detection.py / internal_state.py
  formal_l0.py / l0_audit.py / experiment.json（当前正式路径）
  recursion.py / integration.py / structure.py / actions.py / action_space.py / policies.py
  inspect.py / experiment_audit.py / policy_audit.py / policy.py（调试兼容导入）
debug/
  smoke_policy.py / run_fixture.py
  world_probe.mjs / prepare_arena.mjs
supervisor/
  supervisor.py / limits.yaml
bridge/
  server.js / package.json
minecraft/
  action-space.json / src/capabilities.js（新增正式动作；既有接口保留）
storage/
  index.json / individuals/A-<uuid>/（此 A 的数据库、监控和 reports/）
  environments/（共享环境记录） / admin/（整理与校验记录）
tests/
  test_core.py / test_supervisor.py / test_structure.py / test_policies.py / test_lifetime.py / test_action_space.py / fixtures/
```

```powershell
.\.venv\Scripts\python.exe -m unittest discover -v
npm --prefix minecraft test
```

上述历史测试数量不表示当前基线结果；历史维护检查点完整 Python suite 为 291/291 PASS，各历史阶段的基线结果保留在 [BASELINE_CORRECTION_REPORT.md](BASELINE_CORRECTION_REPORT.md)。当前 Formal A Continuous Operative Reentry 实现锚点记录 560 passed / 114 subtests passed；本次文档收口未重跑测试。身体扩展的测试与能力边界见 [BODY_CAPABILITIES.md](BODY_CAPABILITIES.md)。数值模拟和 Node 测试适配器只作为测试证据；真实游戏验收单独标明，未用模拟结果替代游戏运行。

## 外部策略边界修正（历史 legacy_policy_debug）

本轮新增 PolicyRegistry、参数来源和 policy_migration_status；将初始策略复制到 A0，由当前 InternalState 提供运行参数，分别记录动作评分四部分和递归数量的资源/状态/初始策略三项来源。

真实 Java 26.1 联调使用端口 53335 和独立配置 `storage/environments/legacy/policy-boundary.minecraft.json`，保留原 Minecraft 配置。`storage/individuals/A-ee858dbd-002b-4cdb-a8ff-c1de059614f9/policy-boundary-live-002.db` 记录 A0→A64；A45 的数量 2→3 被 A48 读取并实际用于创建三个过程。共 5 次参数变化、0 次策略来源迁移；固定更新规则仍标为 INITIAL_EXTERNAL_POLICY。

完整策略清单、逐事件实例、局限和运行方法见 [POLICY_BOUNDARIES.md](POLICY_BOUNDARIES.md)。查看本轮证据：

```powershell
.\.venv\Scripts\python.exe -m individual.policy_audit --db storage/individuals/A-ee858dbd-002b-4cdb-a8ff-c1de059614f9/policy-boundary-live-002.db
```

本轮没有实现新策略的自主生成与采纳，没有据此宣布理论结构升阶。


## World-entry 身体验收

当前阶段允许明确创建独立新测试生命周期，每个个体仍单独存储；新测试 A 不是原主线延续。原主线的数据库、选择记录与容量锁不自动重置。实验者验收入口如下（TEST_ONLY，不是自主策略）：

```powershell
.\.venv\Scripts\python.exe -m debug.world_entry_validation --new-test --port 当前端口
```

报告在新个体目录的 reports/，独立测试选择记录为 storage/world-entry-selection.local.json；不会覆盖 individual/lifetime.json。正式系统仍以数字 code 和低语义感知交互，动作采样策略未改。

六条基础身体交互已完成真实因果验收，当前 `WORLD_ENTRY_FREEZE = passed`。范围、条件性未验收项和载体限制见 [WORLD_ENTRY_AUDIT.md](WORLD_ENTRY_AUDIT.md)；冻结版本/哈希见 [WORLD_ENTRY_FREEZE.json](WORLD_ENTRY_FREEZE.json)。身体、ActionSpace、正式采样与递归实现均未因本轮验收改变。

需要重新验收时，可显式运行独立 TEST_ONLY 测试（会在小区域布置材料；测试世界需允许命令）：

```powershell
.\.venv\Scripts\python.exe -m debug.world_entry_live --new-test --port 当前端口
```

入口使用 `BECA_Validate` 及独立测试选择/配置/数据库；原 canonical A 不进入运行。源帧、数字动作、真实服务器包和更新后的帧均保存。编排、等待时机与材料用途属于实验者，不是 A 的策略；服务器包仅供审计，正式 A 没有查询接口。

后续仅允许为补齐原生基础交互或修复因果保真 bug 进行带版本记录的载体修正；不要因为 A 遇到困难随意增加身体能力，也不要将修正记为自主能力增长。
