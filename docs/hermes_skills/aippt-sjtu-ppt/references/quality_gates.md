# Quality Gates

Use this reference when reviewing an AIPPT deck, QA report, or repair proposal.

## Non-Negotiable Gates

- The PPTX must open.
- Page count must match the accepted outline contract.
- User A must never see User B files or paths.
- The worker must not expose raw filesystem paths to browser clients.
- Builder validation must pass after any Hermes repair.
- Production jobs must not depend on unreviewed generated scripts.

## Slide-Level Checklist

Each non-cover slide should have:

- A specific claim, teaching goal, or action takeaway, not just a topic.
- A layout that matches the content type.
- No more than five supporting points.
- No paragraph that should have been split into cards.
- Short enough text to survive PowerPoint rendering.
- Large enough text for classroom projection: prefer 2-3 cards or process
  steps per slide, with 2-3 short points each.
- A clear visual hierarchy at thumbnail size.

## Contact-Sheet Checklist

At thumbnail size, the deck should show:

- Different rhythms across adjacent slides.
- A restrained SJTU red/gold visual system.
- Enough whitespace.
- No repeated "large rounded rectangle full of bullets" pattern.
- Distinct cover and thanks pages.

If the active model run has no image input, do not present these as direct
visual observations. Use deterministic preview checks, Deck IR structure, and
`logs/vision_review.md` if a separate vision provider produced one.

## Layout Suggestions

Use these repairs:

```text
too many dates         -> timeline
too many arrows        -> process cards
many key-value facts   -> fact cards
core terms feel abstract -> concept_diagram
long prose             -> lead takeaway + 3 cards
dense comparison       -> two_column or table
page feels empty       -> add support object, example, quote, or process structure
page feels crowded     -> shorten bullets or split page
```

## Tone Gate

For SJTU academic use:

- Prefer concrete dates, model names, tasks, metrics, and examples.
- Avoid marketing adjectives unless the audience is external.
- Avoid "AI is magical" framing.
- Keep claims, examples, and recommendations grounded and reproducible.
- Use Chinese punctuation consistently in Chinese decks.

## Repair Report Template

```text
# Hermes PPT Review

## Summary
- Overall status:
- Biggest risk:
- Recommended action:

## Must Fix
- Slide N:

## Nice To Improve
- Slide N:

## Memory Signals
- User seems to prefer:
- Group/template preference:
```

## Accept/Reject Rule

Accept a Hermes repair only when:

1. The repaired IR validates.
2. The PPTX builds.
3. The repaired deck preserves user-authored required pages.
4. QA risk is lower than before.

If these are not true, keep the deterministic deck and attach Hermes review as
advice rather than replacing the artifact.
