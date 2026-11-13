# Web presentation refinement — 13 November 2026

## Release scope

Source baseline: `f27c2556f1aa7efcd5915bdb251862d10305f96f` on main. This patch improves public navigation, editorial readability and account guidance while retaining the approved brand artwork, palette, risk examples and established authentication links.

- Public mobile navigation closes on Escape, outside pointer interaction and ordinary link selection. Escape restores focus to its summary. Both navigation variants identify the current page.
- Keyboard users can skip navigation to the landing, public research and anonymous workspace content.
- Mobile entry navigation uses two real grid columns; its account actions remain readable. Menu targets are at least 46 CSS pixels high and the panel scrolls within the viewport.
- Landing paragraphs have a steadier line height and readable supporting copy. Existing protocol calculations, evidence and limits remain intact.
- Signup and verification copy explains that an already verified account should log in or recover its password. The guidance supports the actual email instructions without promising delivery or granting verification from a query flag. Existing POST forms and document-navigation auth links remain in place.

## Validation before pull request

AST lint, TypeScript and the complete Next production build passed locally. The first production build exhausted local Windows memory with 11 generation workers. Repeating with a temporary one-worker configuration passed all 48 pages; the original config was restored byte for byte and is not changed by this patch. No dependency or lockfile changed; npm installation audit reported zero vulnerabilities.

Browser checks used the built-in browser against an isolated localhost build with external API forwarding blocked. Desktop and 390px mobile layouts were inspected. Escape/focus restoration, outside dismissal, Methodology navigation/current-page marker, verification guidance destination links and absence of horizontal overflow passed. The expected local service-status warning reflects the intentionally blocked API; it is not production availability evidence. CI remains the required broader fixture and bundle gate.

Regression coverage adds meaningful menu and skip-link interactions; verification expectations follow the revised text. No customer records, production credentials or mail were used in these preview checks. Record actual post-merge CI and public build identity separately before claiming deployment.

## Existing Wix portfolio

The existing Harmony editor was used through its native editor tools. A before snapshot was retained outside source. Fifty-two applied entrance/scroll effects were removed, including 1.2-second fades and additional delays; exact readback found none of those effects on desktop or mobile. The shared Heading 2 theme changed from 64spx to 52spx, retaining its font and navy palette. Save and publish succeeded on 13 November. The live mobile page subsequently showed all section headings visible and no horizontal overflow. Existing site, pages, identity, content, domains and navigation were retained.

## Remaining boundaries

This presentation release is not a new live financial-model or fresh email-delivery certification. Previous security exceptions and owner-only recovery-code work remain separate. Recheck actual main, public `rivexis-build` and `/health` after release; retain the original Worker host and custom hostname.
## First CI follow-up

The first protected run passed 350 of 352 Chromium browser cases, including the new navigation and skip-link regressions. Two assertions still expected the replaced signup/helper copy; those expectations were corrected without weakening the generic-conflict or pre-verification session checks. The complete CI gate must pass on the follow-up commit before merge.

