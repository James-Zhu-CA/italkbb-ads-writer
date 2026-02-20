# 广告洞察与文案提示词

按 `SKILL.md` 的单一流程执行：`Step 0 -> Step 7`。

## 执行总则

- 接到需求先做 Step 0 计划，未完成 Step 0 不得进行官网检索。
- Step 0 与 Step 7 为必选步骤，必须有对应文档文件。
- Step 1 到 Step 6 根据 Step 0 计划按需执行；执行了的步骤必须有对应文档。
- Step 7 必须二次抓取官网进行事实核查，不能只引用前面步骤文档。
- 对“点击套餐后才显示价格”的页面，必须执行变体遍历和变体级核查。

## 文档清单

- 必选文档：
- `workflow/<run-id>/step0-plan.md`
- `workflow/<run-id>/step7-fact-check.md`

- 条件文档（仅在对应步骤被 Step 0 选中时生成）：
- `workflow/<run-id>/step1-scope.md`
- `workflow/<run-id>/step2-facts.md`
- `workflow/<run-id>/step3-persona.md`
- `workflow/<run-id>/step4-pain-itch-delight.md`
- `workflow/<run-id>/step5-selling-points.md`
- `workflow/<run-id>/step6-platform-copy.md`

- Step 0 必须记录未执行步骤及原因，不要求为跳过步骤单独创建文件。

## 每步文档结构（统一）

每个 step 文件至少包含：

- `## Step`
- `## Status`
- `## Inputs`
- `## Method`
- `## Output`
- `## Fact Map`
- `## Tool Trace`

模板步骤额外包含：

- `## Template Called`

涉及价格的步骤应额外包含：

- `## Variant Context`

## 字段主键与一致性（强制）

- Step 3 到 Step 7 的人群主键必须统一为：
  - `persona_id`
  - `behavior archetype`
- `persona_id` 统一格式：`P01`、`P02`、`P03` ...，并在同一次 run 内保持稳定。
- `segment background`、`language & cultural background` 仅可作为补充维度字段，不能替代主键。
- 若发现字段漂移（例如只写 `segment background`），当前步骤不得标记 `completed`，必须先修正。

## Step 0 规划约束（强制）

- 在 `step0-plan.md` 明确：
  - 本次需求与目标
  - Step 1-6 中哪些要执行、哪些跳过、原因
  - 每一步需要读取的文档和依赖关系
  - 计划抓取的官网 URL 列表
  - 计划使用的工具/手段（search/open/curl 等）
  - 页面展示类型判断（`static` 或 `interactive-variant`）
  - 若为 `interactive-variant`，列出 Step 2 和 Step 7 的变体遍历方案
  - 执行队列（`Step 0 -> 选中步骤 -> Step 7`）
  - Step 0-7 状态表
- Step 7 必须标记为 mandatory，不能跳过。
- Step 0 选步决策矩阵（必须执行）：
  - 首次生成文案：Step 1 + Step 2 + Step 3 + Step 4 + Step 5 + Step 6 + Step 7
  - 修改已有文案：根据修改范围按需选择 Step 1-6 + Step 7
  - 核实给定文案：Step 1 + Step 7（其余步骤按需补充）
  - 其它需求：根据目标灵活选择步骤，但需满足依赖关系
- 非首次生成文案任务，禁止默认全选 Step 1-6。
- 页面类型在 Step 0 仅做 `pending` 标记，不做最终定稿。

## Step 1 边界约束（强制）

- Step 1 允许：
  - 确认平台、产品、canonical URL、目标人群、输出数量
  - 每个候选 URL 做一次可达性检查
- Step 1 禁止：
  - 价格抽取
  - 条款抽取
  - Nuxt chunk 反查
  - payload 解析
  - claim 级验证
- canonical 规则：
  - 产品投放任务 canonical 必须是产品页（例如 `.../chinese-tv-plans...`）
  - promotion/legal 页面仅作为 Step 2 辅助证据，不得在 Step 1 设为 canonical

## Step 2 输入分栏（强制）

Step 2 前半段必须完成并落盘：

- 页面类型最终判定（`static` 或 `interactive-variant`）
- 判定结果一旦写入 `step2-facts.md`，后续步骤不得改口径

进入 Step 3 前，Step 2 必须把官网事实分为：

- `Value Features`（可用于卖点）
- `Restrictions and Fees`（仅用于合规披露）

若页面为 `interactive-variant`，Step 2 必须新增 `Variant Price Matrix`，字段至少包括：

- `variant key/name`
- `promo price`
- `original price`
- `conditions`
- `capture method`（`UI-state` / `payload` / `endpoint`）
- `source URL`
- `capture timestamp`

Step 2 必须新增 `Fetch Dedup Log`，字段至少包括：

- `URL`
- `fetched_at`
- `purpose`

同一步内不得对同一 URL 以同一 purpose 重复抓取；若因超时或 5xx 重试，需在日志写明原因。

Nuxt/JS 反查仅在以下条件同时满足时允许：

- 页面已确认为 `interactive-variant`
- 价格或条件无法从 DOM 可见内容取得

`Restrictions and Fees`（如合约、额外费用、解约费用）不得作为 Step 5 卖点或 Step 6 说服文案。

## 受众分层与语种锁定（强制）

- Step 1 目标客群可选填；若指定，只作为 Step 3 的优先候选，不得直接锁定为最终核心人群。
- Step 3 必须基于业务与市场情况输出行为分群（动机/习惯/场景/决策路径/JTBD），不得使用笼统“华裔”单类替代。
- 语言与文化背景是画像维度之一（例如香港移民、台湾移民、大陆移民等），但不得作为分群主键。
- 人群命名应采用行为特征（如“远程看护刚需型家庭”），不应仅用背景标签命名。
- Step 3 必须产出本次执行的 `Target Segment List`（本次要继续处理的人群全集）。
- Step 4 到 Step 6 必须覆盖 `Target Segment List` 的全部人群，不得跳过。
- 若用户未明确要求只做单人群，Step 3 默认将评分前 3 名纳入 `Target Segment List`。
- `core audience` 仅表示优先级，不表示“其他不做”。
- 语种锁定按人群主要语言使用习惯确定：
  - 繁体中文主导 -> 繁體中文
  - 简体中文主导 -> 简体中文
  - 英文主导 -> English
- Step 3 每类人群都要明确“常用语言 + 文案字体系（繁/简/英） + 语言与文化背景 + 语气提示”。
- 不得在同一客群输出中混用繁体、简体、英文。
- Step 3 到 Step 7 的跨步骤引用必须使用 `persona_id` 回链，不得仅按背景标签回链。

## 1) 建立用户画像提示词（Step 3）

仅当 Step 3 被 Step 0 选中时执行。  
文档产出：`workflow/<run-id>/step3-persona.md`

文档要求：

- `## Inputs` 必须包含 Step 1 产品信息（产品/服务名称、平台、canonical product page URL）与 Step 2 官网事实及 URL 证据。
- `## Output` 覆盖本次任务相关的行为型细分人群（按产品覆盖范围选择，不得笼统为单一“华裔”）。
- 若 Step 1 指定了目标人群，须在输出中标注为“优先候选”并纳入比较。
- 每类画像必须标注常用语言、文案字体系、语言与文化背景、语气风格提示。
- 必须标注核心人群和语种锁定。
- 人群入选规则：若用户未明确要求“只做单人群”，`Target Segment List` 默认纳入 `Core Audience Scoring` 前 3 名；若有效候选不足 3，则纳入全部有效候选。
- `core audience` 仅表示执行优先级，不表示“其他人群不做”。
- 核心人群判定必须包含：
  - 候选人群规模
  - 产品需求强烈度（JTBD）
  - 转化准备度
- `## Output` 必须使用表格，并至少包含以下三个子区块：
  - `### Target Segment List`
  - `### Persona Candidate Matrix`
  - `### Core Audience Scoring`
- 所有表格均写在 `step3-persona.md` 的 `## Output` 下，便于 Step 4 到 Step 6 直接引用。
- 三个表中的 `persona_id` 必须一一对应；`Target Segment List` 仅保留本次需要继续处理的 persona。
- 禁止用 `segment background` 列替代 `persona_id` 或 `behavior archetype`。

提示词：

假如你是一个资深营销洞察专家，基于加拿大华裔市场的真实消费环境，针对【请填写具体品类】与【产品信息：产品/服务名称、核心功能、价格与限制条件、适用场景】先生成候选行为人群并比较，不要提前锁定单一目标人群。若 Step 1 已指定目标人群，请把它作为优先候选加入分析，但不得直接判为核心人群。

输入约束：
- 必须引用 Step 1 产品信息（产品/服务名称、平台、canonical URL）与 Step 2 官网事实，不能脱离产品信息做泛化画像。
- 必须使用 Step 2 官网事实（价格/功能/限制条件）作为依据。
- 分群主轴必须是行为特征（动机、习惯、场景、决策路径/JTBD），而非语言或文化背景。
- 语言与文化背景（例如香港移民、台湾移民、大陆移民）必须作为画像维度体现，但不能作为首要分群依据。
- 禁止输出笼统的单一“华裔”画像结论。
- 表格设计参考：
  - 横坐标：每一类用户行为特征的概括化描述（动机、习惯、场景、决策路径）。
  - 纵坐标：年龄、婚姻、收入、职业、生活方式、消费现状、核心特征、语言与文化背景。

请把结果严格写在 `## Output` 中，并按以下结构输出：
1. `### Target Segment List`（表格）  
字段至少包含：`persona_id`、`behavior archetype`、`priority candidate (yes/no)`、`core audience (yes/no)`、`language/script lock`、`processing priority`。  
`processing priority` 仅表示执行优先顺序，不改变后续是否处理。  
2. `### Persona Candidate Matrix`（表格）  
字段至少包含：`persona_id`、`behavior archetype`、`priority candidate (yes/no)`、`motivation`、`habit`、`scenario`、`decision path`、`age`、`marital`、`income`、`occupation`、`lifestyle`、`consumption status`、`core trait`、`common language`、`language & cultural background`、`script lock (繁/简/英)`、`tone guidance`。
3. `### Core Audience Scoring`（表格）  
字段至少包含：`persona_id`、`behavior archetype`、`segment size (1-5)`、`demand intensity (1-5)`、`conversion readiness (1-5)`、`weighted score`、`rank`、`core audience (yes/no)`、`reason`。  
`weighted score` 默认公式：`size*0.3 + demand*0.4 + readiness*0.3`。

要求：
1. 每一类画像需基于真实可感知的消费行为，而非泛泛而谈的人口标签。  
2. 各类人群之间需要具备清晰区分度，避免高度重叠。  
3. 请标注哪一类为当前最具消费价值的【核心人群】，并简要说明其成为核心人群的关键原因。  
4. 核心人群选择需给出至少三项判定因素：候选人群规模、该产品需求强烈度、购买转化准备度。  
5. 每一类画像必须标注常用语言、文案字体系（繁体/简体/英文）与语言文化背景（如香港移民、台湾移民、大陆移民等），并给出语气风格建议。
6. 若用户未明确要求单人群，`Target Segment List` 默认使用评分前 3；若用户明确要求单人群，则仅保留该人群。  
7. `core audience` 仅作为处理优先级标记，不得用于排除其他已入选人群。  
8. `Target Segment List` 中的人群必须在 Step 4 到 Step 6 全部被处理，不得因优先级被跳过。
9. 若输出单人群，也必须保留完整字段并仅输出 1 行 `persona_id`。

## 2) 挖掘目标用户痛点、痒点、爽点的提示词（Step 4）

仅当 Step 4 被 Step 0 选中时执行。  
文档产出：`workflow/<run-id>/step4-pain-itch-delight.md`

文档要求：

- `## Inputs` 必须包含 Step 3 与 Step 2。
- `## Output` 必须覆盖 Step 3 的 `Target Segment List` 全部人群。
- 每条痛/痒/爽需标注 `source URL` 或 `inference`。
- 若选择多类人群，需有跨人群对比总结。
- 输出建议采用表格，至少包含：`persona_id`、`behavior archetype`、`language/script`、`JTBD`、`pain`、`itch`、`delight`、`evidence type`。
- 必须追加 `### Segment Coverage Check`，逐项确认 `Target Segment List` 全部人群已处理。
- `### Segment Coverage Check` 至少包含：`persona_id`、`behavior archetype`、`in Target Segment List`、`processed in Step 4`、`status`。

提示词：

假如你是一位资深营销洞察专家，擅长从加拿大华人细分族群的真实生活片段中提炼情绪动因，挖掘尚未被清楚表达的潜在需求。请基于 Step 2 官网事实与 Step 3 已选目标人群，逐类输出洞察，不得脱离事实编造。

请按以下步骤分析：
1. 先为每一类已选人群明确一个高频使用场景与对应 JTBD。  
2. 再从该场景中提炼痛点、痒点、爽点。  
3. 最后把每个维度压缩成一句可用于文案转化的表达（避免空泛口号）。

请覆盖 Step 3 `Target Segment List` 的【全部目标人群】，并从以下三个维度进行拆解：

- 痛点：用户在此情境中最担忧或想解决的问题是什么？
- 痒点：用户希望呈现出的理想状态/角色投射是什么？
- 爽点：用户在哪一瞬间获得了情绪上的短暂满足或被理解的感受？

要求：
1. 所有洞察要体现与 JTBD 相关的实际行为。  
2. 每一类已选人群分别产出痛点、痒点、爽点的一句话表达。  
3. 每一类输出必须标注 `source URL` 或 `inference`，并与 Step 2 事实保持一致。  
4. 用词需符合该人群在 Step 3 中的语言/字体系设定（繁体/简体/英文），不得混写。  
5. 若存在多类人群，输出核心人群与其他人群的关键差异；若仅单一人群，标注 `cross-segment: not applicable`。  
6. 禁止使用笼统描述（如“华裔都在意”），必须落到具体行为类型与具体场景，并结合语言文化背景说明。  
7. 不得遗漏 `Target Segment List` 中任何人群；如信息不足也要输出并标注 `inference`。  

## 3) 挖掘产品卖点的提示词（Step 5）

仅当 Step 5 被 Step 0 选中时执行。  
文档产出：`workflow/<run-id>/step5-selling-points.md`

文档要求：

- `## Inputs` 必须包含 Step 2、Step 3、Step 4。
- 卖点列表不得包含合约、额外费用、解约费用等限制条件。
- 必须单独列出“不可作为卖点”的限制条件清单。
- `## Output` 必须包含以下三个子区块：
  - `### Selling Point Mapping Matrix`
  - `### Non-sellable Restrictions`
  - `### Step6 Handoff`
  - `### Segment Coverage Check`
- `### Selling Point Mapping Matrix` 必须使用表格，字段至少包含：  
  `selling_point_id`、`persona_id`、`behavior archetype`、`language/script`、`JTBD`、`pain/itch/delight ref`、`step2 fact ref (url)`、`variant binding`、`competition edge`、`market size`、`use in step6 (yes/no)`。
- 硬性丢弃规则：  
  - 没有 `step2 fact ref (url)` 的卖点不得保留；  
  - 涉及价格/优惠但没有 `variant binding` 的卖点不得保留。
- `### Step6 Handoff` 必须覆盖 Step 3 `Target Segment List` 的全部人群；不得遗漏。
- `### Step6 Handoff` 每条至少包含：`handoff_id`、`persona_id`、`behavior archetype`、`language/script`、`recommended usage`、`approved claim text (draft)`、`required compliance note`、`variant binding`。

提示词：

假设你是一位经验丰富的品牌营销专家，擅长把“官网事实 + 人群洞察”转化为可投放卖点。我现在有一款面向【输入目标用户】的【输入品类】产品。请你基于 Step 2、Step 3、Step 4 的材料，按以下步骤输出：

步骤 0：先识别限制条件（如合约、额外费用、解约费用等），建立 `### Non-sellable Restrictions` 清单。  
步骤 1：列举候选卖点，并为每条卖点建立映射：对应哪类人群、哪条 JTBD、哪条 pain/itch/delight、哪条 Step 2 官网事实 URL。  
步骤 2：形成 `### Selling Point Mapping Matrix`，并执行硬性校验：无 URL 证据或无变体绑定（价格类）即删除。  
步骤 3：评估保留卖点的市场大小与竞品优势，按优先级排序。  
步骤 4：输出 `### Step6 Handoff`：给 Step 6 提供可直接使用的 Top 卖点列表（按人群分组），每条含一句“可改写为 headline/description 的买点表达”与“必须披露条件”。  
步骤 5：输出 `### Segment Coverage Check`：逐项核对 `Target Segment List` 各人群是否均有 Step6 可用交接项。

多人群任务要求：  
- 卖点必须按 `persona_id` 分组输出；  
- 每组遵循该人群 `language/script`，不得混写。  
- 不得跳过 `Target Segment List` 中任何人群。  

输入材料：
1. 产品资料：产品说明、技术参数、核心功能。  
2. 消费者洞察：用户画像、痛点、痒点、爽点。  

## 4) 文案创作提示词（Step 6）

仅当 Step 6 被 Step 0 选中时执行。  
文档产出：`workflow/<run-id>/step6-platform-copy.md`

文档要求：

- `## Inputs` 必须包含 Step 2、Step 3、Step 4、Step 5。
- `## Fact Map` 覆盖全部可验证主张。
- `## Output` 声明目标分层与语种锁定。
- 必须覆盖 Step 3 `Target Segment List` 全部人群；若输出多类人群文案，必须按人群分别输出独立语种版本，不得混写。
- 每条价格主张必须绑定到明确 `variant`。
- 不得把不同变体价格混写在同一条主张里。
- 不得把合约、额外费用、解约费用包装成卖点或正向利益。
- 必须包含 `### Step5 Handoff Consumption`，逐条记录 Step 5 交接项是否被采用及原因。
- 必须包含 `### Visual Creative Pack`，图文一体输出，不得只给文案不配图提示。
- 必须包含 `### Claim Inventory`（供 Step 7 直接复核），且使用表格输出。
- `### Claim Inventory` 字段至少包含：  
  `claim_id`、`claim_text`、`asset_location`、`persona_id`、`behavior archetype`、`language/script`、`variant key/name`（如适用）、`source URL(s)`。
- 必须包含 `### Claim to Variant Binding`，与 `### Claim Inventory` 的价格类 claim 一一对应。
- 必须包含 `### Segment Coverage in Assets`，字段至少包含：`persona_id`、`behavior archetype`、`asset package generated (yes/no)`、`language/script match (yes/no)`、`notes`。
- `### Step5 Handoff Consumption` 至少包含：`handoff_id`、`persona_id`、`status`、`used in asset`、`note`。
- `### Visual Creative Pack` 必须按人群分组，且每组包含：
  - `图片风格总指令`
  - `图片清单（4-6张）`
  - 每张图字段：`visual_id`、`slot`、`purpose`、`prompt`、`negative`、`overlay_text(<=10字建议)`、`claim_ref`
- 必须包含 `### Image Prompt Variables`，字段固定为：`[产品] [核心卖点] [关键动作] [痛点] [目标人群画像] [使用场景] [结果状态] [犹豫点参数]`。
- 平台微调规则（必须执行）：
  - Xiaohongshu：默认 `3:4` 竖图，采用 `封面/痛点/过程/对比/结果/细节(可选)` 槽位。
  - Facebook：默认 `4:5` 竖图（可补 `1:1`），采用 `hook/场景/证据/优惠/CTA` 槽位。
  - Google：默认输出 `1:1 + 横版` 概念图，采用 `offer/feature/trust/CTA` 槽位，文字更克制。

提示词：

假如你是一个金牌文案，擅长把 Step 5 的卖点交接清单转成可投放的平台资产包。请以“平台资产包优先”输出，而不是只输出泛化买点句子。

请按以下步骤执行：
1. 读取 `Step5 Handoff`，逐条判断采用与否，输出 `### Step5 Handoff Consumption`。  
2. 基于已采用卖点，按 `Target Segment List` 逐人群生成 `### Platform Asset Package`（按本次平台需求输出对应资产，如 Google/Facebook/Xiaohongshu 文案与图视频提示词）。  
3. 为每个人群输出 `### Visual Creative Pack`：图文一体，不少于 4 张图，按平台槽位组织，每张图都给出 Prompt + Negative + 叠字建议。  
4. 对所有可验证主张建立 `### Claim Inventory`，用于 Step 7 定向复核。  
5. 对价格与优惠主张输出 `### Claim to Variant Binding`，确保每条价格 claim 有唯一变体归属。  
6. 输出 `### Segment Coverage in Assets`，确认 `Target Segment List` 全部人群均有对应文案与视觉资产。  
7. 输出 `### Image Prompt Variables`（可替换占位变量）。  
8. 若用户本次仅要求“买点文案”，可在末尾附加 `### Optional Buy-point Lines (10)`。

约束：
- 文案语言/字体系必须遵循 Step 3 对应人群设定（繁/简/英）。  
- 多人群任务必须分人群独立输出，不得混写。  
- 每个事实主张都必须能追溯到 Step 2 官网 URL。  
- 限制条件（合约/额外费用/解约费用等）只可放在合规说明，不得包装为卖点。  
- 不得遗漏 `Target Segment List` 中任何人群。  
- 视觉提示词必须与文案主张一致；若图中文字包含价格/条件，必须进 `Claim Inventory`。  
- 小红书视觉默认写实手机随手拍、低广告感；Facebook 与 Google 需按平台微调，不可直接复制同一套构图语法。  

## 5) 小红书种草爆文生成提示词（Step 6 平台专用）

文档补充要求：

- 平台为 Xiaohongshu 时，Step 6 必须在文件中追加 `## Xiaohongshu Template Output`。
- 文案默认 `<= 400` 字（用户另有要求除外）。
- 必须同步输出 `## Xiaohongshu Visual Creative Pack`，默认 4-6 张图，建议槽位：`封面/痛点/过程/对比/结果/细节(可选)`。
- 每张图必须包含：`Prompt`、`Negative`、`叠字建议(<=10字)`，并标注 `claim_ref`（若出现可验证主张）。

Role: 小红书种草爆文生成器

Goals:
通过精准捕捉真实生活场景与用户情绪痛点，生成高度原生、低广告感、具备高完读率与高转化潜力的小红书种草爆文，400字以内。

Skill:
- 用户场景洞察能力：将产品卖点转译为具体可感的生活场景，识别用户在真实使用过程中的隐性痛点、情绪触发点与决策阻力。
- 原生种草内容构建能力：遵循小红书高互动表达方式与叙事节奏，用个人经历、过程描述与细节感受承载产品价值，语言自然口语化，弱化品牌与广告痕迹。
- 信任感与真实感塑造能力：通过真实对比、使用前后变化、犹豫与踩坑过程建立可信度，避免直接夸赞产品，以“分享体验”替代“推荐产品”。
- 情绪驱动的转化引导能力：识别并激活关键下单情绪（错过焦虑、对比心理、自我奖励），在结尾通过价格锚点、使用时机或稀缺信息自然促成决策。

Attention:
- 避免生硬广告与品牌话术，不使用明显营销语句。
- 以生活化、社交化、情绪化表达为主，符合小红书阅读与传播习惯。
- 结合高频痛点，精准击中目标受众真实需求。
- 卖点必须通过体验与细节呈现，不直接罗列。
- 图片风格默认：写实手机随手拍、生活方式、自然光、轻微颗粒、低广告感、3:4 竖图优先。
- 默认图片槽位建议：
  - 封面图：场景+情绪+结果暗示
  - 痛点图：问题现场，不摆拍
  - 过程图：关键动作细节
  - 对比图：同场景 Before/After
  - 结果图：情绪落点与生活改善
  - 细节图（可选）：尺寸/材质/适配信息

## 6) 官网事实复核提示词（Step 7 必选）

文档产出：`workflow/<run-id>/step7-fact-check.md`

文档要求（强制）：

- 必须重新抓取官网最新页面内容进行比对。
- 不得仅引用 Step 2 到 Step 6 文档作为最终证据。
- 复核清单来源采用弹性规则：
  - 若 Step 6 存在且有 claim 清单，则按 Step 6 清单复核。
  - 若 Step 6 不存在或无清单，则根据待复核文案内容直接抽取 claim 复核（可参考 Step 2 的 claim inventory）。
- 根据 claim 清单构建“定向复抓 URL 集”，仅抓取核验该批 claim 所需 URL。
- 禁止在 Step 7 做全站扩散搜索。
- 证据冲突时使用统一优先级：`产品 canonical 页 > 产品变体 payload/endpoint > promotion 页 > legal/其他页`。
- 必须输出 `### Step7 Fetch Dedup Log`，字段至少包含：`URL`、`fetched_at`、`purpose`、`retry_count`、`retry_reason`。
- 同一步内不得对同一 URL 同一 purpose 重复抓取；若超时/5xx，可重试但需入日志。
- 重试策略：超时或 5xx 最多重试 2 次。
- 逐条核查复核清单中的每个事实主张。
- 增加语种一致性核查：文案语种/字体系必须与 Step 3 对应人群的语种锁定一致。
- 对 `interactive-variant` 页面，必须先切到对应变体状态，再核查该条主张。
- 必须增加 `### Segment Coverage Audit`：核对 Step 3 `Target Segment List` 的每个 persona 在 Step 6 是否存在对应资产包且语种匹配。
- 若 Step 6 含视觉提示词，必须增加 `### Visual Prompt Audit`：逐条核查视觉提示中的事实主张与叠字文案。
- 表格输出字段：
  - `claim_id`（若 Step 6 存在，需与 `Claim Inventory` 对齐）
  - `claim`
  - `variant key/name`
  - `variant evidence`（`UI-state` / `payload` / `endpoint` + 状态键）
  - `claim source`（`step6` / `input-copy` / `step2-inventory`）
  - `source priority used`
  - `language/script check`
  - `latest official URL`
  - `fetched_at`（含时区）
  - `fresh evidence extract`
  - `mismatch reason code`（`price_conflict` / `condition_missing` / `variant_mismatch` / `language_mismatch` / `not_found`）
  - `status` (`verified` / `not found` / `mismatch`)
  - `action taken`
- `### Segment Coverage Audit` 表格字段至少包含：
  - `persona_id`
  - `behavior archetype`
  - `in step3 target list` (`yes/no`)
  - `step6 asset package present` (`yes/no`)
  - `language/script match` (`yes/no`)
  - `status` (`pass` / `fail`)
  - `action taken`
- `### Visual Prompt Audit` 表格字段至少包含：
  - `visual_id`
  - `slot`
  - `persona_id`
  - `language/script check`
  - `factual text/overlay`
  - `mapped claim_id`
  - `latest official URL`
  - `fetched_at`（含时区）
  - `status` (`verified` / `not found` / `mismatch`)
  - `action taken`
- 禁止以 `segment background` 替代 `persona_id` / `behavior archetype` 作为核查主键。
- 若存在 `not found` 或 `mismatch`：
  - 有 Step 6 时：先修改 Step 6，再重新执行 Step 7。
  - 无 Step 6 时：输出修正文案建议，并基于修正后 claim 重新执行 Step 7。
- Step 7 自动复核回路最多执行 2 轮；仍未解决的条目标记为 `manual review required`。
