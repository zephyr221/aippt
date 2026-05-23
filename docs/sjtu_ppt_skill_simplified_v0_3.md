---
name: Markdown/Deck IR 转 SJTU 模板 PPT
description: 将 Markdown 或结构化 Deck IR 转换为 SJTU Wine Red + Gold 风格 16:9 PPTX。第一版采用少量稳定布局，不追求复杂装饰。
dependencies: python-pptx>=1.0.0
---

# SJTU PPT Skill v0.3：简化稳定版

## 1. 目标

将 Markdown 提纲或 Deck IR 转换为符合 SJTU 模板风格的 `.pptx` 文件。

第一版目标不是复杂炫酷，而是：

- 正式
- 清爽
- 稳定
- 可编辑
- 不斑驳
- 不爆框
- 符合 SJTU Wine Red + Gold 风格

## 2. 模板文件

使用：

```text
SJTU 模板.pptx
16:9，13.333" × 7.5"
```

布局索引：

| 索引 | 名称 | 用途 |
|---|---|---|
| 0 | 封面-01 | 封面页 |
| 7 | 常规样式（2） | 内容页，红色顶栏 |
| 12 | 封底01 | 致谢页 |
| 14 | 空白（纯白） | 备用 |

占位符：

```text
封面-01：idx=0 标题，idx=11 副标题/日期
常规样式（2）：idx=11 顶栏标题，idx=12 页码清空
封底01：idx=11 感谢文字
```

模板加载后清空默认 slides，保留 layouts。

## 3. 核心配色

```python
SJTU_RED   = "#A62038"
SJTU_DEEP  = "#6B1525"
GOLD       = "#C5A46C"
GOLD_PALE  = "#F0E6D2"
TEXT_MAIN  = "#2B2B2B"
TEXT_MUTED = "#666666"
BG_LIGHT   = "#F7F5F2"
LINE_GRAY  = "#D9D9D9"
WHITE      = "#FFFFFF"
```

使用原则：

- `SJTU_RED`：顶栏、编号、重点标记
- `GOLD`：细线、左侧强调线、小面积点缀
- `BG_LIGHT`：内容卡片浅底
- `TEXT_MAIN`：正文
- `TEXT_MUTED`：说明文字

不要大面积使用深酒红填充。不要使用过多颜色。

## 4. 设计禁忌

必须遵守：

- 不使用中文斜体
- 不在 header 下方叠加装饰
- 不添加底部横线
- 不做整页图片化 PPT
- 不使用繁体中文数字编号
- 不使用复杂多色渐变
- 不堆叠过多卡片、图标、箭头、阴影
- 不临时发明新组件
- 不修改模板文件

## 5. 页面网格

内容页默认区域：

```text
slide_w = 13.333"
slide_h = 7.5"
header_h ≈ 0.9"
content_top = 1.25"
content_left = 0.75"
content_right = 0.75"
content_bottom = 0.55"
content_w = 11.83"
content_h ≈ 5.65"
```

双栏：

```text
col_gap = 0.35"
col_w = (content_w - col_gap) / 2
```

三栏：

```text
col_gap = 0.28"
col_w = (content_w - 2 * col_gap) / 3
```

横向卡片：

```text
item_gap = 0.25"
item_w = (content_w - (n - 1) * item_gap) / n
n 建议 3 到 5
```

## 6. Layout 白名单

第一版只允许：

```text
cover
section
toc
one_column
two_column
three_column
horizontal
comparison
table
summary
thanks
```

暂缓支持：

```text
quote_block
icon_label_row
chevron_flow
复杂 stat_callout
复杂 highlight_card
复杂 timeline
复杂 dashboard
```

## 7. 文本硬约束

```text
标题：不超过 26 个中文字符，最多 1 行，特殊情况 2 行
每页 bullet：不超过 5 条
每条 bullet：不超过 30 个中文字符
双栏每栏：不超过 4 条 bullet
三栏每栏：不超过 3 条 bullet
横向卡片：3-5 个 item，每个 desc 不超过 18 个中文字符
表格：最多 5 行 × 4 列
insight：最多 1 条，不超过 45 个中文字符
```

超出时：

1. 压缩文字
2. 拆分 bullet
3. 拆成两页
4. 从三栏降级为双栏或单栏

## 8. 保留基础组件

只保留 5 个基础组件：

```text
header：填充模板顶栏
footer：右下角页码
card：浅灰/白底内容卡片
badge：小圆编号
insight：核心观点条
```

## 9. Layout 规范

### 9.1 cover

封面只保留：

```text
标题
副标题
日期 / 汇报人
```

标题不超过 2 行。全部使用白色文字。

### 9.2 toc

目录页使用两列列表。

条目超过 8 个时，按主题分组，但不要做复杂装饰。

### 9.3 one_column

用于普通正文页。

结构：

```text
标题在模板顶栏
正文卡片占主要区域
bullet 列表
底部可选 insight
```

### 9.4 two_column

用于：

```text
问题 / 方案
现状 / 目标
输入 / 输出
方法 A / 方法 B
理论 / 实践
```

结构：

```text
左右两个等宽 card
每个 card：heading + bullets
底部可选 insight
```

### 9.5 three_column

用于：

```text
三个模块
三个阶段
三个贡献
三类问题
三项能力
```

结构：

```text
三个等宽 card
每个 card：badge + heading + 2-3 bullets
```

### 9.6 horizontal

用于流程、阶段、路线。

结构：

```text
3-5 个横向 card
每个 card：label + title + desc
card 之间可选细线连接
不使用复杂 chevron
```

### 9.7 comparison

comparison 是受控双栏，本质上等同 two_column，但语义更明确。

要求：

```text
左栏和右栏 bullet 数量尽量一致
标题短
不要超过两栏各 4 条
```

### 9.8 table

用于小表格。

要求：

```text
最多 5 行 × 4 列
表头小面积使用 SJTU_RED 或 GOLD
行高最小约 0.35"
表格下方可选 insight
```

### 9.9 summary

总结页使用 3 条以内核心结论。

推荐：

```text
三张横向或纵向 card
每张 card 一句话
```

### 9.10 thanks

使用模板封底。只写：

```text
谢谢！
欢迎批评指正
```

## 10. 垂直居中关键规则

python-pptx 中 textbox 垂直居中必须设置 `<a:bodyPr anchor="ctr">`。

```python
bodyPr = tf._txBody.find(qn('a:bodyPr'))
if bodyPr is not None:
    bodyPr.set('anchor', 'ctr')
```

不要设置到错误节点。

## 11. Agent 规则

Agent 不负责计算坐标。Agent 只输出或修正 Deck IR。

允许 Agent 做：

```text
修正标题
压缩 bullet
选择 layout 白名单中的布局
调整 columns/items/rows
根据 QA 错误修 deck.json
```

禁止 Agent 做：

```text
安装依赖
联网搜索
修改模板
创建新组件
写新的 PPT 生成脚本
访问任务目录外文件
把整页做成图片
```

## 12. 推荐 Deck IR 示例

```json
{
  "deck": {
    "title": "多模态大模型在医学影像诊断中的应用",
    "subtitle": "组会汇报",
    "organization": "上海交通大学",
    "template": "sjtu_wine_red_gold",
    "language": "zh-CN"
  },
  "slides": [
    {
      "id": "s01",
      "layout": "cover",
      "title": "多模态大模型在医学影像诊断中的应用",
      "subtitle": "组会汇报",
      "date": "2026 年 5 月"
    },
    {
      "id": "s02",
      "layout": "two_column",
      "title": "方法思路：从单模态识别到多模态融合",
      "columns": [
        {
          "heading": "输入信息",
          "bullets": ["医学影像", "病历文本", "临床指标"]
        },
        {
          "heading": "融合目标",
          "bullets": ["提升上下文理解", "增强解释能力", "支持辅助决策"]
        }
      ],
      "insight": "双栏页应表达结构关系，而不是堆砌文字。"
    }
  ]
}
```

