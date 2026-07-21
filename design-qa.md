# Design QA — subscription and readability refinement

- Source visual truth: `/workspace/scratch/eaf87f0b7f60/upload/01-image.png`, with the user's explicit instruction overriding the visible secondary offer link and requiring its removal from the subscription block.
- Implementation screenshot: `/workspace/scratch/bloomclub-updated-subscription.jpg`
- Combined comparison: `/workspace/scratch/bloomclub-design-qa-comparison.jpg`
- Viewport: 1363 × 936 desktop browser viewport. The supplied reference is 1783 × 765, so the comparison uses the same subscription section and state but preserves the implementation's responsive crop.
- State: public landing page, subscription section in view, unauthenticated.

## Full-view comparison evidence

The two-column image/content composition, blush background, editorial typography, price hierarchy, benefit list, primary burgundy CTA, image subject, crop, and section rhythm remain consistent with the supplied visual. The requested secondary “Условия оплаты и возврата” link has been removed without leaving a layout gap. The public offer remains available through the footer document list.

## Focused region comparison evidence

The subscription action row was inspected at rendered size because it is the changed region. The primary CTA remains aligned with the price and list; removing the secondary link does not introduce imbalance or clipping. The updated image alternative text now describes the visible vase, flowering branches, cup, and table. Small navigation, metadata, subscription-list, and footer typography were increased while preserving hierarchy and line wrapping.

## Findings

- No actionable P0, P1, or P2 differences remain.
- P3: the source and implementation were captured at different desktop aspect ratios, resulting in an expected responsive crop difference. This does not affect hierarchy, image quality, or interaction.

## Required fidelity surfaces

- Fonts and typography: Cormorant Garamond and Manrope hierarchy retained; small UI and supporting copy increased for readability without unintended wrapping.
- Spacing and layout rhythm: two-column section, content offsets, CTA placement, and vertical rhythm retained; no horizontal overflow at 1363 px.
- Colors and visual tokens: ivory, blush, wine, muted text, and border tokens unchanged.
- Image quality and asset fidelity: original production WebP asset retained with sharp rendering and matching crop; alternative text corrected.
- Copy and content: offer link removed only from the subscription block; support hours no longer claim daily availability; price and subscription terms unchanged.

## Primary interactions tested

- Subscription navigation and section anchor.
- Partner category opening and modal closing.
- Participant login expansion and labelled login/password inputs.
- Footer still exposes all four required legal documents.
- Browser console checked; no site-origin errors or warnings.

## Comparison history

- Initial audit findings: inaccurate subscription image alternative text, potentially unverified “Ежедневно” support claim, and small secondary/navigation text.
- Fixes: corrected alternative text, changed support wording to neutral working hours, increased small text sizes, and removed the subscription-block offer link requested by the user.
- Post-fix evidence: `/workspace/scratch/bloomclub-updated-subscription.jpg`; no P0/P1/P2 issues remain.

## Implementation checklist

- [x] Remove secondary offer link from subscription block only.
- [x] Preserve offer and other legal documents in the footer.
- [x] Correct subscription image alternative text.
- [x] Remove unsupported daily-availability wording.
- [x] Improve small-text readability.
- [x] Build, render, inspect interactions, and check console.

final result: passed
