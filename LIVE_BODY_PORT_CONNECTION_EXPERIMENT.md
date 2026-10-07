# BPC-LIVE-1 — Live Body-Port Connection Formation, Persistence and Later Read

**阶段状态：DEFINED / NOT_IMPLEMENTED。**

日期：2026-10-07。定义基线：`codex/bpc-r2-real-execution`，
`70e3ec476cc370a2d9974e381d9bdc8d4cd3aaf7`。
依据：`LIVE_CURRENT_STRUCTURE_INTEGRATION_AUDIT.md`。
本文件仅冻结研究问题及验收/证伪边界；没有实现、运行或验收结果。
编号 LIVE-1 是实验阶段编号，不表示 recursive layer L1。

## 1. Research question

在一次不中断的正式 live A 运行中，A 能否把实际观察到的原生身体端口 O
作为自己递归形成空间中的独立可引用端点，在当前真实经历产生 C 后，
于同一 live 状态链中形成并保存 C ↔ O，随后由实际 live recursive processing
再次读取此前保存的这条连接，而不是重建连接或依赖外部选择？

固定被测对象为同一次运行中形成、持久保存、后来读取的同一连接，
不是 capability metadata、历史事件、导出图或 detached organization。
O 的原生身份是实际观察能力所属的 catalog version 与 numeric code；
端口本来存在，本阶段不声称内部结构创造了身体能力。
C 的具体内容必须来自本轮连续运行中新到达的真实输入/变化，并成为当前内部状态。
本文件不规定应形成哪个具体 C、选择哪个 code 或哪条解决路径。

## 2. Exact causal chain

```text
A starts / 同一 individual、同一不中断的运行
→ 实际观察原生 body capability
→ O 成为 live recursive formation space 的独立可引用端点
→ 新的真实 ObservationFrame / 当前经历到达
→ live current structure 形成 C
→ 同一 live formation process 形成有直接支持的 C ↔ O
→ connection 写入并提交到 A 的持续 live state
→ 至少一个后续真实输入 / recursive cycle
→ 该 cycle 沿自身递归访问路径读取此前保存的同一 C ↔ O
→ 可核对的后续 internal-processing read/effect
```

形成、提交和后续读取必须有可区分的时间/状态边界：先形成并提交，后读取。
保存身份、端点、直接支持及形成来源，必须足以识别后来读到的是原连接。
identity/digest 相同本身不能证明没有重建，还须核对实际写入与读取路径。

后续访问根必须来自运行中的当前输入、内部状态或递归推进；实验者只记录
其来源，不在事后指定 C/O/query root 来使读取发生。
不要求访问根由自主目标产生，也不借此新增目标形成研究。

数据库对本次运行中新连接的正常提交属于持久化，不属于历史重放。
后续处理读取这个已提交的内部连接是目标能力；扫描 event history 来重新
formation，或把审计导出重新装成图，不是目标能力。

`O → expression → perform()` 不属于本阶段验收链。BPC-R2 的限定证据保持冻结，
不为本阶段重复真实执行，不将它扩大解释为 live A 的连接形成证明。

## 3. PASS criteria

以下八项必须全部由 canonical PASS 主链及其预注册负对照支持。
“同一次连续 live 运行”只约束 canonical PASS 主链；NC1–NC6 可以分别在
基于同一冻结实现、同一预注册判据的独立 live controlled runs / instances 中执行，
不要求与 canonical PASS 主链置于同一次运行。不得把不同运行中的主链片段拼成 PASS。

1. **Native endpoint entry：** 实际观察来源可核对；O 以原生 version/code 身份
   成为形成机制实际可引用的独立端点，不能只有 metadata 或字符串中的 code。
2. **Current C：** C 源于本次运行中新产生的真实 frame/change/experience，
   具有明确输入来源，并属于该 A 当前内部状态；不是旧 witness 的重建。
3. **Online formation：** C ↔ O 在 live recursive processing 中实际形成，
   有端点与直接支持证据；实验代码没有直接写入目标连接作为答案。
4. **Live persistence：** 形成的连接及必要支持已经提交进 A 的持续内部状态，
   不能只存在于工作对象、报告、事件审计 payload 或独立 TEST_ONLY 图中。
5. **Later cycle：** 提交之后至少发生一个后续实际 live recursive cycle，
   individual identity 和运行连续性不变。
6. **Exact later read：** 后续实际 processing 从 A 保存的结构读取原连接，
   核对相同端点、连接身份、形成/提交版本及支持来源；不重新 formation，
   不直接扫描原始经历取得答案，不由实验者事后指定 query root。
7. **Connection dependence：** 保持后续输入与非目标状态一致的预注册阻断/消融
   表明：该已保存连接不可访问时，对应读取消失或变为明确不可用，且后续
   processing 有可观察差异；不能只比较日志数量或总 digest。
8. **No substitute path：** 形成和读取链不使用 detached BPC organization、
   historical replay、sampler、binder、value-to-action mapping 或 fallback
   代替原生 O、连接形成、访问根或消费结果；所有必要负对照通过。

后续读证据必须记录真实消费者、实际访问来源和读结果/processing effect。
仅打印、存档或通过外部查询看到连接，不足以满足第 6、7 项。
本轮只定义条件，不因已有 BPC PASS 而给本阶段任何 PASS。

## 4. FAIL criteria

出现以下任一情况，候选链直接 FAIL：

- O 仅是可被 Core 读取的 capability metadata/code，没有成为 live formation endpoint。
- C 或 O 在实验结束后由历史记录重构，或目标连接直接由实验者作为答案写入。
- C ↔ O 只存在于独立 TEST_ONLY/BPC 图、导出文件或报告，未进入 live A 内部状态。
- 连接未提交持久保存；所谓后续读取只是同轮临时对象传递。
- later read 重新计算/重建连接，或绕过连接从 raw experience、缓存答案取得 O。
- 后续 query root 由实验者事后指定，而不是由 live recursive path 实际产生/使用。
- 取得 O 或读结果必须经过 sampler、binder、人工动作映射或 fallback。
- 为完成链条中途重启 A、重新载入历史、切换到第二个独立运行或 detached 分支。
- 必要负对照不成立，或缺少证据却把已有离线结果替代为本阶段成功。

运行未能提供必要真实输入、没有到达后续 cycle，或测量材料不完整时，
不得宣称 PASS；须说明未能检验的项，不把未执行当作已经证伪理论。
本文件不授权补样、替换 witness、重跑后改变判据或自动重启。

## 5. Negative controls

NC1–NC6 是基于同一冻结实现和同一预注册判据的独立 live controlled runs / instances，
不要求与 canonical PASS 主链置于同一次运行。每个控制必须通过自身真实 live 路径执行，
只作用于本阶段声明的 live 端点/形成/保存/读取边界；仍禁止 historical replay、
offline reconstruction 和 detached BPC organization。
主链的单次连续性要求及其中途重启/切换运行的 FAIL 条件不因独立控制而放宽。
控制条件须在实施前固定，不得在看到结果后修改。
记录作用时间、目标身份、状态版本及非目标输入；不删除或改写 canonical history。
因执行路径本身变化而产生的后续状态差异属于测量结果，不应被伪造为相同。

| 控制 | 固定与阻断范围 | 必须观察到的结果 |
|---|---|---|
| NC1 O endpoint exclusion | 保留真实观察来源及 C，只阻断原生 O 成为本次形成端点 | 不能形成目标 C ↔ O；metadata 不得成为替代端点 |
| NC2 current C exclusion | 保留已观察 O，只阻断当前目标 C 参与形成 | 不能形成目标连接；旧历史 C 不得替补 |
| NC3 persistence exclusion | 保留形成结果及真实来源，阻断目标连接进入 A 的持久内部状态 | 后续 cycle 无法读取该连接；临时引用/审计记录不得替补 |
| NC4 persisted connection ablation | 原连接已经提交；在后续真实读边界阻断其访问，保留输入、来源及非目标状态 | 对应读取消失/不可用，后续 processing 有可核对变化；不得重新形成或 fallback |
| NC5 detached artifact exclusion | 禁止 live 路径读取旧 BPC 报告、导出图、validation artifact 或 detached organization | 主链不依赖这些材料；任何偷用均 FAIL |
| NC6 old-history source exclusion | 禁止本阶段 producer 从运行前数据库事件、旧 witness 或重放历史取得 C/O/连接 | 形成只由本次在线输入与本次在线状态推进支持；偷用旧材料均 FAIL |

NC3/NC4 不允许先删历史再重新运行 producer。NC4 针对已形成并保存的连接，
不以重建出的另一条内容相同连接充当原连接。消融本身属于实验者测量干预，
不是 A 的自主删除能力，也不应作为递归输入或行为策略。
具体干预实现不在本文件设计；不能实现上述同源 live 控制时，不得降级为离线控制后判 PASS。

## 6. Explicit nonclaims

即使通过，也只说明本次连续 live 运行中的形成、保存和后续消费链成立。
不证明：

- 身体端口或 primitive capability 由内部结构创造；
- 本阶段连接已经作者化动作，或已调用真实 `perform()`；
- O 导致了 C 所记录的世界变化，或建立了 world-effect causal law；
- 一般参数形成、自主目标、自主动作选择或多方案选择；
- behavioral causal closure；
- L1 / upward recursion 或 universal generative dynamics；
- 该 candidate realization 是 Perfect Recursion 的唯一/普遍生成机制。

BPC-0、BPC-R1、BPC-R2、Successor-0、FROI、GSC、CEC 的冻结判据和结果不变。
本阶段不要求重做 BPC-R2 已验证的后半链，也不自动开启下一阶段。

## 7. Allowed / forbidden evidence sources

**允许：** 本次不中断运行实际接收的 body capability observation、真实
ObservationFrame/ChangeSet/experience；同期 live formation 的 facts/supports；
A 内部状态的真实提交和后续实际读取；预注册 live 控制的执行记录。
原生身份来自实际能力观察及其经验证的 catalog version，机械表示不得加入语义答案。

只读快照、日志、trace 和报告可作为外部核对证据，但只能记录已经发生的
live 因果链，不能把离线计算结果喂回该链。既有历史可供背景审计，不能作为
本阶段 formation source、connection source 或 query source。
本阶段不沿用已有 individual 或已有数据库；其隔离规则见第 9 节。
已有 identity/lineage 与旧数据库保持原样，仅保留为旧阶段历史证据 / audit material。

**禁止：** 旧数据库/旧 witness reconstruction、同轮导出后再 formation、
offline replay/query、detached BPC artifact、预写 C ↔ O、从 action record 事后
人工构造 O、value-to-action mapping、semantic action lookup、外部 selector、
sampler/binder/fallback、reward/ranking/nearest/best/top-k，以及事后指定读取根。
能力目录可验证实际观察到的原生身份，不能替代“本次 A 确实观察到 O”的证据。

本文件不改变现有 sampler/binder；它们不得成为本阶段形成/读取链的作者。
已有行为来源若出现在真实输入 provenance 中必须披露，不能借该来源直接选定
目标 O、写连接或返回答案。本阶段没有授权新的身体执行或 bootstrap 策略。

## 8. Minimum runtime boundaries — description only

**最早边界：实际观察到的 native capability identity → live 递归形成域中的
独立可引用 O endpoint。** 当前观察并非完全没有 O 信息；缺的是其递归端点身份。

当前代码位置：`individual/observation.py` 的 `FrameEncoder.encode` 保存
body action-space 元数据；`individual/action_space.py` 的 `provision` 验证/保存
原生 catalog 能力；`individual/core.py` 的 `ACore.accept_observation` 将帧交给
`FormalL0.advance` 或 `FormalFROI.prepare_read_checkpoint`，但能力 provision
实际在 `_commit_observation`、解释器处理之后进行。它仍然只保存 metadata。
需要改变的是观察身份进入 live formation 的接口边界，不是动作 dispatch，
也不是把 provision 提前就可宣称已形成连接。

后续必须接通的最小边界仅为：

- live formation result → A 自身持久内部状态及真实事务提交；不能只写审计事件。
  对应承载/提交位置为 `InternalState`、`ACore._transition` 与 `EventStore.transition`。
- 已提交 connection → 后续 live recursive processing 的真实读入口；访问来源必须
  来自该运行的递归路径，消费者读取原连接及支持，不能重算或从旧 relation fallback。
  对应需核对的边界为 `FormalL0.advance` / `FormalFROI` 的实际处理与消费入口。
- 外部测量 → 上述端点、保存及读取边界的预注册阻断与因果记录；不得形成替代答案，
  不得成为 A 的输入记忆或行为策略。

这里只定位边界，不选择数据 schema、生成算法、consumer query 策略或代码方案。
不修改冻结 FROI/GSC/BPC 实现来套用本定义，不预设哪套旧图可以直接写回。
实现尚未开始；本阶段停在 **DEFINED / NOT_IMPLEMENTED**。

## 9. Database and individual isolation — frozen rules

### Canonical PASS run

BPC-LIVE-1 canonical PASS 必须使用：

- 全新初始化的实验数据库；
- 全新的 individual identity；
- 当前冻结 runtime / implementation；
- 不导入任何旧数据库内容、旧 witness、旧 BPC artifact 或旧 relation。

从 canonical run 启动开始，到以下完整链结束：

```text
O enters live formation space
→ current C forms
→ C ↔ O forms
→ connection persists
→ later recursive cycle
→ later read
```

全过程必须使用同一个数据库、同一个 individual，并保持同一次连续 runtime。
中途不得重建数据库、切换数据库、重启后重载历史或替换 individual。

### Existing databases

已有数据库保持原样，不清空、不覆盖、不迁移进 BPC-LIVE-1。
不得作为本阶段 C、O、connection 或 query source；仅保留为旧阶段历史证据 / audit material。
任何从运行前旧数据库读取并参与本阶段 formation 或 later read 的路径，
直接违反本阶段定义。

### Negative controls

NC1–NC6 各自使用独立初始化的 fresh experimental database 和 fresh individual identity，
并与 canonical run 隔离。例如：

```text
canonical → fresh DB / individual A
NC1       → fresh DB / individual B
NC2       → fresh DB / individual C
NC3       → fresh DB / individual D
...       → 各自独立的 fresh DB / fresh individual
```

所有控制必须：

- 使用同一冻结实现和同一预注册判据；
- 除对应控制变量外，不主动改变其他实验条件；
- 不使用 historical replay、offline reconstruction 或 detached BPC artifact；
- 不复用 canonical run 已形成的连接；
- 在看到结果前固定控制条件，不得事后修改。

每个 control run 内部仍必须保持同一个 fresh database、同一个 fresh individual
和连续 runtime，直到该控制所需观测完成。NC1–NC6 的既有控制语义不变；
独立控制不得用于拼接或替代 canonical PASS 主链。

### Clarification

“fresh database”只表示实验开始前为空、专用于本次 run 的新数据库，
不表示运行过程中可以重置数据库。
运行开始后，数据库本身就是 A 当前 live state persistence 的一部分，必须连续保留。

### Isolation nonclaim

使用 fresh database 只用于消除旧历史污染和 provenance 歧义，不证明：

- A 在已有长期历史的数据库中也一定能形成相同连接；
- persistence 与数据库实现无关；
- fresh individual 与已有 individual 的行为等价。

这些不属于 BPC-LIVE-1 当前研究问题。上述规则只冻结数据库与 individual 隔离边界，
不改变既有 research question、exact causal chain、PASS/FAIL 判据、负对照语义或其他 nonclaims。
本阶段仍为 **DEFINED / NOT_IMPLEMENTED**；implementation **NOT_STARTED**。
