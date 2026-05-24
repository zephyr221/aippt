---
name: Markdown 转 SJTU 模板 PPT 
description: 将 Markdown 文稿转换为SJTU 模板风格 16:9 PPT（.pptx），使用 python-pptx 从零构建。
dependencies: python-pptx>=1.0.0
---

# 模板风格：SJTU Wine Red + Gold（上海交通大学模板）

## 概述

基于 `SJTU 模板.pptx` 模板文件，使用模板中预设的封面布局、红色顶栏内容布局和封底布局，在布局基础上叠加精品组件。Wine Red (#A62038) + Gold (#C5A46C) 配色。

## 何时使用

当用户要求：
- 使用 SJTU 模板风格的 PPT
- 红色+金色主题的机构报告
- 需要使用现有 .pptx 模板文件的布局

## 模板文件

`SJTU 模板.pptx` — 16:9 (13.333" × 7.5")

### 布局索引

| 索引 | 名称 | 用途 |
|------|------|------|
| 0 | 封面-01 | 封面页，红色背景+SJTU Logo+曲线装饰 |
| 7 | 常规样式（2） | 内容页，红色平行四边形顶栏（高度约0.9"） |
| 12 | 封底01 | 致谢页，红色背景+圆形装饰 |
| 14 | 空白（纯白） | 可选空白页 |

### 布局占位符映射

- **封面-01**: idx=0 (标题), idx=11 (副标题/作者)
- **常规样式（2）**: idx=11 (顶栏标题, 白色 22pt), idx=12 (页码, 清空不用)
- **封底01**: idx=11 (感谢文字)

### 模板加载与清理模式

```python
prs = Presentation(TEMPLATE_PATH)
# 删除模板中已有幻灯片，保留布局
while len(prs.slides) > 0:
    rId = prs.slides._sldIdLst[0].get(qn('r:id'))
    prs.part.drop_rel(rId)
    prs.slides._sldIdLst.remove(prs.slides._sldIdLst[0])
```

## SJTU 调色板

| 变量名 | 色值 | 用途 |
|--------|------|------|
| SJTU_RED | #A62038 | 主品牌色，顶栏、表头、badge、pill、bullets ▪ 标记 |
| SJTU_DEEP | #6B1525 | 深酒红，仅用于阴影色基准和 pill 文字色 |
| SJTU_ACCENT | #C00000 | 强调红，模板 accent1 |
| GOLD | #C5A46C | 第二品牌色，insight 竖线、card gold_top、gold_div 菱形 |
| GOLD_LIGHT | #D4BB8A | 浅金色，深底上的文字 |
| GOLD_PALE | #F0E6D2 | 极浅金，标签底色 |
| WARN_AMBER | #C47F17 | 风险/警告信号 |
| （其余灰度色与深蓝主题共用） | | |

## 设计禁忌

### 必须遵守

- **不使用中文斜体** — 所有组件禁用 italic，中文斜体渲染效果差
- **不添加底部横线** — 模板已有红色顶栏，底部保持干净
- **不在 header 下方叠加装饰** — 模板顶栏高度大（≈0.9"），装饰会被遮挡
- **不使用大面积 SJTU_DEEP 填充** — 深酒红大面积视觉效果差，改用 GOLD_PALE 浅底 + GOLD 边框
- **不使用繁体中文数字编号** — 避免壹贰叁肆伍，使用一二三四五或阿拉伯数字
- **不在 chevron_flow 中使用 SJTU_DEEP** — 太暗不好看，替代色序：SJTU_RED → GOLD → 褐色(#8B5C3E) → TEXT_PRIMARY

### 配色风格统一

- insight 默认 accent = GOLD（统一），风险页使用 WARN_AMBER
- 正面结论使用 SJTU_RED（而非 SUCCESS 绿色），保持暖色调

## 封面页规范

### 内容精简原则

- 标题行应精炼，**不超过 2 行**，留足行间距
- 副标题/描述与标题之间设置 `space_before = Pt(20)` 或更大
- **全部使用白色文字**，不使用金色（GOLD_LIGHT）— 金色在红色封面上辨识度差
- 日期单独一行，放在副区域（idx=11），不与标题挤在一起
- 不堆砌"对比框架""作者""单位"等信息 — 封面只保留标题 + 副标题 + 日期

## 目录页规范

### 少量条目（≤8 项）

两列竖向列表 + badge + 垂直连接线 + 页码标注

### 大量条目（>8 项）

使用 **主题分组卡片**（2×2 网格）：
- 每个卡片代表一个主题（如"核心引擎""智能管理""平台能力""工程基础"）
- 卡片顶部 pill 标签（accent 色底 + 白字），下方 badge 列表
- 每张卡片内 3-4 个条目，badge + 标题 + 页码
- 4 组不同颜色：SJTU_RED / GOLD / 褐色 / TEXT_PRIMARY

## 关键布局规则

### 表格高度计算

每行最小高度 ≈ 0.35"（13pt 文字 + 上下 padding 各 5pt）

```
最小表格高度 = 行数 × 0.35"
```

**表格在卡片内时**：`table.top + table.height < card.top + card.height - 0.1"`

### Insight 间距

insight 条与上方内容的最小间距：**≥ 0.35"**

```
insight.top ≥ 上方内容底部 + 0.35"
```

间距太小（<0.2"）会显得拥挤、不专业。

### step_flow 标签宽度

标签文本框宽度设为 **1.96"**（原 1.36" 会导致中英混排文字换行）。

### 卡片内容溢出检查

创建卡片时务必验证：

```
card_top + title_zone(~0.65") + content_height < card_top + card_height
```

如果内容放不下，优先增加卡片高度而非压缩内容。

## 垂直居中对齐（关键陷阱）

python-pptx 中 textbox 垂直居中必须设置 `<a:bodyPr anchor="ctr">`，**不是** `<p:txBody anchor="ctr">`。

```python
# ✅ 正确
bodyPr = tf._txBody.find(qn('a:bodyPr'))
if bodyPr is not None:
    bodyPr.set('anchor', 'ctr')

# ❌ 错误
tf._txBody.attrib['anchor'] = 'ctr'
```

## 连接箭头对齐

卡片间的连接箭头（线 + 三角形）：
- 线和三角形必须在**同一水平线**上
- 三角形 y 需要 offset 半个尺寸：`int(arrow_y) - int(tri_sz) // 2`

## 引言段落装饰

页面顶部的引言/导语文字应包裹在装饰容器中：
- 使用 `card(shadow=False)` + 左侧 3pt GOLD 竖条
- textbox 垂直居中（设置 bodyPr anchor='ctr'）

## SJTU Header 组件

`sjtu_header(slide, title, page)` — 最小化干预模板：

1. **仅填充模板占位符**：idx=11 设置标题（白色 22pt 粗体），idx=12 清空
2. **不在顶栏下方添加任何装饰元素**
3. 自动附加 `sjtu_footer()`

## SJTU Footer 组件

`sjtu_footer(slide, page)` — 极简页码：

- 仅在右下角显示：红色小菱形 ◆ + 两位数页码 (TEXT_CAPTION)
- 位置：y = SLIDE_H - 0.42"，右对齐

## 组件规范

### badge(slide, l, t, text, size, bg, fg, sz)
- 圆形编号/字母标记，默认 SJTU_RED 底 + WHITE 字
- 推荐作为 card 内部标题的标配元素

### insight(slide, left, top, width, text, accent)
- 灰底圆角矩形 (WARM_GRAY_1 + WARM_GRAY_2 边框) + 左侧 3pt accent 竖线
- 文字垂直居中，**不使用斜体**
- 高度固定 0.48"

### highlight_card(slide, left, top, width, label, text)
- 灰底 card + 4pt GOLD 左竖线 + pill 标签
- 高度固定 1.1"

### stat_callout(slide, l, t, w, h, number, unit, label, desc, accent, num_sz)
- KPI 大数字卡片：顶部 accent 色条 + 大号数字 + 单位 + 描述

### step_flow(slide, left, top, width, steps)
- 水平步骤流程：badge + 红色连接线 + 底部标签
- **标签文本框宽度 1.96"**（避免中文换行）

### quote_block(slide, left, top, width, text, source)
- 装饰引用卡片：灰底 + GOLD 左竖线 + 大号 " 引号
- 高度固定 1.5"

### icon_label_row(slide, left, top, width, items)
- 图标标签行：一排 0.7" 圆形图标 + 标题 + 描述

### chevron_flow(slide, left, top, width, items)
- V 形箭头序列，颜色轮转：SJTU_RED → GOLD → 褐色 → TEXT_PRIMARY
- 箭头高 0.55"

### card 内部标题对齐

```
card.top + 0.20"  badge center
card.top + 0.18"  title text top
card.top + 0.65"~ content start
```

### pill 与 badge 组合

```
badge.left = card.left + 0.2"
pill.left  = badge.left + badge.size + 0.1"
title.left = pill.left + pill.width + 0.2"
```

## 通用辅助函数

### add_shadow(shape)
12% 透明度 SJTU_DEEP 投影，blur=5pt, dist=1.5pt

### style_tbl(table, rows, cols)
清除默认表格样式，替换为：表头金色底边线 1pt + 数据行暖灰底边线 0.5pt

### gold_div(slide, left, top, width)
细分隔线 + 中心 SJTU_RED 菱形装饰

### _set_ea(run)
设置 CJK 字体为 FN（微软雅黑），所有 run 均需调用
