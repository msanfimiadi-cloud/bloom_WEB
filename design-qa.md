# Bloom Club editorial redesign — design QA

- Source visual truth: `/workspace/scratch/eaf87f0b7f60/generated_images/exec-ac8c6f24-604d-42d0-b153-befe03793449.png`
- Browser-rendered implementation screenshot: `/workspace/scratch/eaf87f0b7f60/bloom-editorial-final.jpg`
- Normalized side-by-side comparison: `/workspace/scratch/eaf87f0b7f60/editorial-final-comparison.jpg`
- Browser viewport: 1363 × 936 CSS px; full-page capture: 1348 × 4157 px
- State: public landing, default state, dynamic statistics using the local API fallback values

## Full-view comparison evidence

The selected reference and the browser-rendered implementation were normalized to the same visible width and placed in one side-by-side comparison image. The implementation preserves the reference's editorial ivory canvas, wine accent, high-contrast serif typography, split hero, blossom photography, three-step rhythm, six-category image strip, blush subscription block, and restrained document footer.

The implementation is intentionally longer after the core reference composition because it retains the production login flow, city selector, complete contacts, and all required legal-document links. These are functional product requirements rather than visual drift.

## Focused region comparison evidence

- Hero: split proportions, heading scale, burgundy italic emphasis, dual CTA hierarchy, statistics, blossom crop, and testimonial overlay match the source direction. Live values replace illustrative mock values.
- Partner categories: all six image subjects and the warm editorial treatment are present. Cards are taller than the source to keep labels legible and make the category buttons easier to use.
- Subscription: two-column blush composition, still-life image, 349 ₽ / 30-day price hierarchy, manual-renewal copy, and offer link are present.
- Footer: required support channels and four legal documents remain readable; the private registration address is absent.

## Required fidelity surfaces

- Fonts and typography: Cormorant Garamond is bundled locally for display text and Manrope for interface/body copy, with Cyrillic and Latin subsets. Hierarchy and line breaks were checked in the browser.
- Spacing and layout rhythm: no horizontal overflow at the captured desktop viewport. The hero, three-step grid, partner gallery, price block, access section, city selector, and footer remain aligned to a consistent frame.
- Colors and visual tokens: ivory, blush, charcoal, muted taupe, and wine tokens follow the selected reference. Focus and selected states maintain contrast.
- Image quality and asset fidelity: all visible editorial photography is real generated raster imagery sized for its slot; UI symbols use the bundled Phosphor icon library. No placeholder imagery is present.
- Copy and content: service explanation, partners, 349 ₽ subscription price, 30-day term, no automatic renewal, support hours, contacts, operator identity, offer, privacy policy, terms, and personal-data consent are present.

## Primary interactions tested

- Opened a featured partner category and confirmed the partner dialog, loading/error state, controls, and CTA render correctly. The local static preview cannot serve the production partner API, so real partner records will populate after normal deployment behind nginx/backend.
- Closed the partner dialog.
- Expanded the participant login flow and confirmed the client tab and credential fields appear.
- Verified both city selection cards and the selected-state contrast.
- Opened `/offer/`, `/privacy/`, `/terms/`, and `/personal-data-consent/`; all four pages rendered, contained the operator details, and did not contain the removed private address.
- Checked browser console errors. No application errors were recorded; only unrelated Chrome-extension metadata errors were present.

## Comparison history

### Iteration 1

- P2: the login anchor participated in the grid and forced the access section onto an extra row.
- P2: the active city inherited white text while its background was overridden to ivory, reducing contrast.
- Fixes: removed the anchor from grid flow, aligned the access copy and login card in one row, restored the wine active-state fill, forced readable login button text, rebuilt, reloaded, and recaptured.
- Post-fix evidence: `bloom-editorial-final.jpg` and `editorial-final-comparison.jpg`.

## Findings

No actionable P0, P1, or P2 findings remain.

## Follow-up polish

- P3: the partner cards are deliberately taller than the concept mock so category names remain legible and easy to click.
- P3: production API data may alter partner counts and card content length; the layout is designed to absorb those changes.

final result: passed
