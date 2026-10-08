# Native Parameter Binding Extension — conversation handoff

Repository: iking-i/beca-minecraft-experiment.
Branch: codex/operative-connection-correction.
Closeout anchor: separate commit introducing this handoff and closeout.

**NATIVE_PARAMETER_BINDING_EXTENSION_TEST_ONLY = PASS / COMPLETED / FROZEN**（2026-10-09）。
实现/验证锚点：`7cdd14c337ee3d47233873b9e179403904b728e9`；BX-T1～BX-T10 全部 PASS。
专项 **21 passed**、相关 **148 passed / 13 subtests**、完整回归
**649 passed / 114 subtests**；原 13 项冻结哈希 MATCH。实际证据来源：
`experimental/native_parameter_binding_extension/VALIDATION.json` 中原始命令、返回码、
stdout/stderr 及其哈希；本次收口仅核对已有证据，不重跑实验。

经历形成的数值连接，可以通过外部给定的通用组合规则，产生原始 receipt 中没有的参数绑定候选，并参与普通递归。

独立 TEST_ONLY BindingCore / 合成观察 / FakeBridge 中，外部 synthetic receipt 给出槽→0；
普通经历 integration 形成 0→1 或 0→2；外部通用 exact-endpoint composition 形成
receipt 未给出的槽→1 / 槽→2。后续未修改的 TC Pair 构造消费连接，产品进入实际
expected operands。S1-only 消融：Pair 产品 **4 → 3**、实际操作数 **16 → 15**；恢复后
内容恢复。同材料、不同历史改变候选；ON/OFF 各自同 A / 数据库跨真实进程恢复和复用，
不依赖 Full Audit History replay。S0/S1 同表示、同执行语义，provenance 不授予权限。

**候选不等于因果绑定证明或采用。** ObservedValue identity 仅含精确类型和值、不含 channel；
不同通道同值可共享端点并产生额外候选。原通道 provenance 保留，但执行不据此筛选。
通道级因果归属未证明，未声称通过跨通道同值排除测试；多候选全部保留，无宿主仲裁。
无关 disconnected 材料不改变相关构造，不能据此宣称已排除共享数值的因果歧义。

不证明新引用绑定传播、动作选择、执行适用性、完整 `{code, parameters}`、表达采用权、
身体执行权、Minecraft 因果闭环、自主目标或 L1。初始槽→值和 receipt execution 标签
是外部 synthetic 前提，不是内部动作作者权；真实 body receipt 适配尚未验证。
Core 仅增加两行只读模式准入检查；默认计算、TC/NBO、caps、body、sampler/binder、
理论、旧数据库及冻结 evidence 不变。旧 CE / Expression Binding / Native Parameter Binding
NOT_READY 和初次失败原样保留，不追溯升级；unrelated untracked 不纳入提交。
见 [closeout](NATIVE_PARAMETER_BINDING_EXTENSION_CLOSEOUT.md) 与
[handoff](NATIVE_PARAMETER_BINDING_EXTENSION_CONVERSATION_HANDOFF.md)。

下一步只记录问题：已形成的连接内容能否构成一个合法的最小原生身体表达，并经原有
身体接口实际执行？不要求覆盖所有动作类型或引用参数。下一阶段 **NOT_STARTED**。
本次未设计、实现或运行该实验，未运行 Minecraft；理论仍为 v0.9
`0917f695d5452c5b890de6d7e9c366503b051797`。

## Continuation boundary

Preserve the original synthetic receipt attribution and all earlier scoped evidence.
Do not treat extra candidates from cross-channel numeric identity as causal binding
proof or silently select one. Do not copy a historical command, use a missing-value
binder or create a separate decision system. Initial assignment, generic mechanism,
new candidate content, later adoption and body execution remain distinct.
Original failures and NOT_READY records stay unchanged. Original reports describing
uncommitted status belong to the pre-closeout verification point.

NEXT_STAGE = NOT_STARTED.
NEXT_DESIGN_STARTED = NO.
NEXT_IMPLEMENTATION_STARTED = NO.
NEXT_EXPERIMENT_STARTED = NO.
MINECRAFT_RUN = NO.

Stop after this closeout/push. No next implementation is authorized here.
