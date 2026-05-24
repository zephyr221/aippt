# Memory Policy

Use this reference before writing or recommending Hermes memory updates for
AIPPT.

## Purpose

Memory should make future PPTs better by preserving reusable preferences:

- Audience.
- Tone.
- Density.
- Preferred slide rhythms.
- Template/style dislikes.
- Feedback after accepted decks.

Memory should not become a hidden archive of private PPT content.

## Scopes

```text
template memory  AIPPT/SJTU style rules shared by the product
group memory     lab/course/team preferences
user memory      one user's private habits and feedback
```

Production should namespace memory by AIPPT user and group. Until that exists,
do not mix durable user-specific memories into global Hermes state unless a
human operator is intentionally doing research.

## Good Memory Updates

```yaml
user_prefers:
  density: dense
  tone: 学术克制
  components:
    - timeline
    - process_cards
  dislikes:
    - 纯 bullet 堆叠
    - 过度营销措辞
evidence:
  source: explicit feedback
  date: 2026-05-24
```

```yaml
group_prefers:
  audience: 计算材料研究生
  examples:
    - DFT
    - MD
    - HPC
  style: 组会分享，结论先行
```

## Bad Memory Updates

Do not store:

- Full outline text from a private deck.
- Uploaded confidential documents.
- API keys, cookies, server paths, or OAuth secrets.
- Raw job logs containing personal data.
- Another user's preference under the current user.

## Feedback Conversion

Convert feedback into durable preference only when it is explicit or repeated.

Examples:

```text
"这页字太多" -> prefer shorter bullets for this deck; durable only if repeated.
"以后都用这种时间线" -> durable user preference for timeline pages.
"我们组汇报要更学术" -> group preference if the user has group authority.
```

## Memory Note Template

```text
Preference:
Scope:
Confidence: low | medium | high
Evidence:
Do not apply when:
```

## Privacy Rule

When unsure, write the signal to the job review report instead of durable memory.
