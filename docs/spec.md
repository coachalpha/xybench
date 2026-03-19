# xybench

> **Eval framework for AI applications, starting with HITL.**
> 让技术团队和非技术团队之间的 AI 质量判断变得结构化、可追溯、可迭代。

---

## 为什么做这个

### 问题

企业在上 agentic 应用时，普遍面临三个没有解决好的问题：

1. **没有明确的方法判断 AI 输出质量好坏**
2. **HITL 审批流程靠自建，重复造轮子，且自建的都不完整**
3. **人工反馈无法结构化地影响 AI 行为**

现有方案的共同缺陷：

- LangGraph `interrupt()` 只解决了框架内的暂停，没有解决审批 UI、通知、状态持久化
- HumanLayer / gotoHuman 是单向的（Agent → 审批人），没有闭环
- 纯 eval 工具（Braintrust、Confident AI）跟 Agent 运行时完全脱节
- 各家都在自建，重复造轮子

### 洞察

**HITL 是 eval 的特例。**

```
Eval 本质：对 AI 输出做判断，产生结构化反馈
HITL：     实时的、阻塞的、有副作用的 eval
           判断结果直接触发 Agent 下一步行为
```

每次 HITL 审批天然产生人工标注数据，这些数据可以：
- 训练 LLM judge
- 改进 prompt
- 追踪 prompt 变更的效果
- 构建数据飞轮

---

## 是什么

**xybench = Eval framework，从 HITL 切入**

```
现在：HITL eval（实时，阻塞，驱动重新生成）
未来：LLM judge eval（异步，批量，自动化）
最终：数据飞轮（人工审批 → 训练 judge → 减少人工介入）
```

核心价值主张：

> **让技术团队 30 分钟接入 HITL，让非技术团队的反馈真正影响 AI 行为。**

---

## 目标用户

### 采用方（Adoption）：技术团队

- 正在做 AI 应用的工程师 / MLE
- 需要给内部用户上线 HITL 审批功能
- 不想花两周自建

**他们的痛点：**
- 自建要搭 UI + 状态管理 + 回调，工程量大
- LangGraph `interrupt()` 坑多，生产环境不稳定
- 没有开箱即用的方案

### 留存方（Retention）：非技术团队

- 产品、运营、合规、法务等审批人
- 需要审批 AI 生成的内容
- 不是工程师，不会用开发者工具

**他们的痛点：**
- 不知道 AI 在做什么
- 给了反馈不知道有没有被用上
- 审批工具难用，变成走形式

**核心设计原则：**
- 技术团队决定采用
- 非技术团队决定留存
- 留存靠闭环感：「我说了话 → 有人听了 → 有结果 → 结果告诉我了」

---

## 竞品对比

| | xybench | HumanLayer | gotoHuman | LangSmith |
|--|--|--|--|--|
| HITL | ✓ | ✓ | ✓ | 部分 |
| 重新生成闭环 | ✓ | ✗ | ✗ | ✗ |
| 对比视图 | ✓ | ✗ | ✗ | ✗ |
| Eval 数据 | ✓ | ✗ | ✗ | ✓ |
| 开源本地优先 | ✓ | ✗ | ✗ | ✗ |
| 数据不出内网 | ✓ | ✗ | ✗ | ✗ |
| LLM judge | 后续 | ✗ | ✗ | ✓ |

**核心差异化：**
1. 重新生成闭环 + 对比视图（审批人看到自己的反馈产生了效果）
2. 开源本地优先（数据不出内网，企业友好）
3. HITL 数据天然变成 eval 数据集

---

## V1 产品形态

### 范围

```
必须有：
├── Python SDK（pip install xybench）
├── LangGraph 集成（5 行代码接入）
├── Streamlit 审批组件
├── approve / reject / need_change / new_idea + reason
├── 提交确认（反馭没有消失）
├── 异步通知（Slack webhook 或邮件）
├── 对比视图（原版 vs 新版）
└── JSON 存储（output_id 做文件名，零依赖）

不做：
├── React 组件（等有人要）
├── 托管审批页（不需要跳转）
├── Dashboard（等有企业客户）
├── LLM judge（数据量不够时意义不大）
├── 权限管理（内网场景不需要）
├── PostgreSQL（JSON 够用）
└── 框架无关抽象（先只支持 LangGraph）
```

### 开发者体验

```python
# 安装
pip install xybench

# Agent pipeline 里加两行
from xybench import review

result = await review(
    content=agent_output,
    session_id=thread_id,
    actions=["approve", "reject", "need_change", "new_idea"],
    notify="slack:#review-channel"
)

if result.action == "need_change":
    new_draft = agent.regenerate(
        original=agent_output,
        feedback=result.reason
    )
```

### 审批人体验

```
┌─────────────────────────────┐
│  待审批内容                   │
│  ┌─────────────────────┐    │
│  │ AI 生成的内容...     │    │
│  └─────────────────────┘    │
│                             │
│  [✓ Approve] [✗ Reject]    │
│  [✎ Need Change]            │
│  [💡 New Idea]              │
│                             │
│  原因：___________________   │
└─────────────────────────────┘

// need_change 之后，对比视图

┌─────────────────────────────┐
│  原版本          新版本       │
│  ┌──────────┐  ┌──────────┐ │
│  │ 原内容   │  │ 新内容   │  │
│  └──────────┘  └──────────┘ │
│                             │
│  [✓ 好多了]  [还需要修改]    │
└─────────────────────────────┘
```

### Streamlit 集成

```python
# 审批人的 Streamlit app
from xybench.streamlit import ReviewComponent

ReviewComponent(session_id=st.query_params["id"])
```

### 存储结构

```
/reviews
    /gen_abc123.json    ← output_id 做文件名
    /gen_def456.json
    /gen_ghi789.json
```

```json
{
  "review_id": "rev_001",
  "output_id": "gen_abc123",
  "content": "原始草稿...",
  "new_content": "重新生成的草稿...",
  "action": "need_change",
  "reason": "第三节格式不符合要求",
  "status": "completed",
  "created_at": "...",
  "reviewed_at": "..."
}
```

### 完整流程

```
AI 生成内容
    ↓
SDK：await review(content)      ← 开发者只写这一行
    ↓
JSON 存储 + 发通知（Slack/邮件）
    ↓
审批人收到通知，打开 Streamlit 组件
    ↓
看内容，选操作，填原因
    ↓
提交确认：「反馈已收到，AI 正在重新生成」
    ↓
（如果 need_change）Agent 重新生成
    ↓
通知审批人：「新版本已生成，点击查看对比」
    ↓
审批人看对比视图，再次判断
    ↓
SDK 收到结果，Agent 继续执行
```

### 判断标准

> **从 `pip install xybench` 到审批人收到第一条通知，不超过 30 分钟。**

---

## 技术演进路径

### Phase 1：能用（现在）

```
Python SDK + LangGraph 集成
Streamlit 组件
JSON 存储
Slack/邮件通知
```

**里程碑：** 3 个真实用户在生产环境跑起来

### Phase 2：好用（3-6 个月）

触发条件：用户开始抱怨具体问题

```
新增 React 组件
新增 LangChain / CrewAI 支持
JSON → SQLite（有并发需求时）
轮询 → Webhook（用户觉得响应慢时）
Slack Block Kit（在 Slack 内直接审批）
```

**里程碑：** 有用户问「有没有托管版」

### Phase 3：可靠（6-12 个月）

触发条件：企业客户问合规和部署

```
托管版后端（Supabase + Railway）
基本 Dashboard（通过率、审批时长、常见 reject 原因）
审计日志
PostgreSQL 支持
Docker 私有部署
```

**里程碑：** 第一个付费客户

### Phase 4：智能（12-24 个月）

触发条件：数据积累够了，用户问自动化

```
LLM judge（用历史审批数据训练）
置信度路由（自动决定送人工还是自动通过）
数据飞轮（人工审批 → 训练数据 → judge 更准）
Prompt 影响追踪（对比不同版本通过率）
```

**里程碑：** 人工审批比例开始下降

---

## 开源策略

### 证书

**Apache 2.0**

- 企业引入无顾虑
- 保留专利权保护
- 可以同时做商业版
- LangChain、LlamaIndex 同款

### 开源 vs 付费边界

```
开源（永远免费）：
├── Python SDK
├── Streamlit 组件
├── React 组件
├── LangGraph / LangChain 集成
└── 自托管完整功能

付费（托管版）：
├── 不用自己维护服务器
├── 多项目统一管理
├── 审批人统一入口
├── 审计日志
└── SLA 保障
```

### 早期成本

```
GitHub 托管    $0
PyPI 发布      $0
基础设施       $0（用户自己跑）
你的成本       时间
```

---

## 第一步验证

### 场景

自己公司的医疗监管文件生成项目：

```
AI 生成监管文件草稿
    ↓
xybench 拦截，通知审批人
    ↓
审批人接受或不接受
    ↓
不接受 → 填原因 → 触发重新生成 → 看对比
    ↓
接受 → 文件上线
```

### 路径

```
写 v1 代码（1-2 周）
    ↓
pip install xybench（自己公司项目）
    ↓
让审批人用一周
    ↓
记录所有卡点
    ↓
迭代打磨
    ↓
发布到 GitHub + PyPI
    ↓
写 README quickstart
    ↓
找外部第一批用户
```

---

## 北极星指标

**短期：** 从 `pip install` 到审批人收到第一条通知，≤ 30 分钟

**中期：** 3 个真实团队在生产环境持续使用

**长期：** 成为 agentic AI 应用的标准 eval/HITL 层

---

## 一句话

> **xybench 把「AI 生成 → 人工审批 → 重新生成」这个非正式流程，变成一个有结构、可记录、可迭代的系统。从 HITL 切入，以 eval 为终点。**