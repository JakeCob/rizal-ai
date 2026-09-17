# UI References

Status: research complete, design direction proposed. Date: 2026-09-17.

Six apps were studied as references for the RizalAI web app: Duolingo, LingQ, 80 Days by Inkle, Brilliant, Bunpro, Memrise. Findings come from public HTML, shipped CSS and JS bundles, help centers, engineering blogs, and reviews. Logged-in screens were not rendered for any of them, so anything about live layout behind a login is marked as inferred. Nothing here licenses us to copy assets, fonts, mascots, or brand colors. Section 8 lists what to avoid.

## 1. Stack findings per app

| App | Framework (evidence) | Styling | Product fonts | Font license |
|---|---|---|---|---|
| Duolingo | React SPA, Redux, Emotion, webpack on CloudFront. No Next.js markers. | Custom "web-ui" CSS variables, colors as RGB triplets with light/dark pairs | "feather" (700, 900) for display, "duolingo-sans" for body, Noto Sans Math fallback | Feather is bespoke (Fontsmith for Johnson Banks). Body reported as DIN Next Rounded, a Monotype license. Neither usable. |
| LingQ | Marketing site is server-rendered Django. App reportedly React (2021 hiring post); not verified behind login. | Tailwind v4.1.18 with shadcn-style semantic tokens | DM Sans variable, Google Fonts | SIL OFL. Usable. |
| 80 Days | Native game on Unity plus the ink runtime | n/a | Light humanist sans in panels, condensed deco caps for status chips. Names not verified. | n/a |
| Brilliant | Next.js pages router, React 18.3.1, Apollo GraphQL, Rive for animation | Panda CSS tokens, KaTeX, light/dark via data-theme | CoFo Brilliant (custom CoFo Sans), CoFo Robert for marketing | Commercial, CoFo Brilliant proprietary. Not usable. |
| Bunpro | Next.js pages router, TypeScript, Tailwind, SWR, over a Rails API. Mobile apps in Flutter. | Tailwind v4 and Panda CSS coexist during migration | Noto Sans JP via next/font, CoFo Brilliant and CoFo Robert also declared | Noto is OFL. CoFo commercial. |
| Memrise | Marketing on HubSpot CMS with jQuery. App is Next.js pages router. | styled-components with a frozen theme object | Boing (A2-Type) for brand, Open Sans and Noto Sans body stack | Boing commercial. Open Sans and Noto OFL. |

Takeaway for us: four of six product apps run Next.js pages router on React, and the two that use Tailwind v4 also use shadcn-style tokens. Our approved stack (Next.js App Router, Tailwind, shadcn/ui) is squarely in the mainstream for this category. No app used a public component library we could detect; each has an in-house design system over primitive tokens.

## 2. Skill tree (path) patterns

Source of the strongest signal: Duolingo path CSS and Brilliant's gameboard data model.

Duolingo, from shipped CSS:
- Node is a 70 by 65 button. A 57px-high ellipse with an 8px solid "lip" drawn as a box-shadow in a 20 percent black tint over the unit color. Pressing translates the node down 8px and removes the lip.
- Active node has a 98px progress ring behind it. Locked nodes are gray. Completed nodes turn gold.
- Unit header is a full-width colored band with white uppercase 17px 700 text and the guidebook link.
- Tapping a node opens a popover with a 10px radius and a single "Start" button showing the XP reward. Locked popovers use a pale background and muted text.
- The route is a single vertical path with a floating "jump to current" button. Zigzag offsets are computed in JS.

Brilliant, from course page data:
- Gameboard, then Level (name, two description bullets, access status), then LessonNode (title, status such as NOT_STARTED, meter lock, premium lock), with a Level Review node closing each level. Paths are color-coded per topic.
- Free users move sequentially; the sequence is the gating rule.

What RizalAI borrows:
- Vertical single path, one unit header band per unit, nodes in three states (locked, active with ring, done). This is a generic pattern used by both apps and predates both.
- Node press-down with a solid lip. The lip is a 4px box-shadow in our own palette, not 8px, and our node shape is a rounded square, not Duolingo's ellipse.
- Popover under a node with the lesson title, estimated minutes, and one Start button showing XP.
- Data shape: our units and lessons tables already match the Gameboard, Level, LessonNode structure. Add a computed node status to the tree endpoint: locked, active, done.

## 3. Lesson runner patterns

Duolingo, from shipped CSS:
- Fixed top bar, 40px tall, flex with 8px gaps: close, progress bar, hearts. Progress track 16px tall with 8px radius. Hearts 32 to 48px.
- Buttons: 12px radius, 48px common height, lip as a 4px box-shadow in a darker shade, active state removes the lip and translates down 2px over 0.1s. Labels uppercase 15px 700 with wide tracking.
- Feedback sheet: fixed to the bottom, padding 24px 16px, slides up with a 0.4s slide and 0.3s fade. Correct is a green sheet with a sound and short praise. Incorrect is a red sheet showing the correct answer, with the Continue button recolored.
- Correct state: pale green background, 2px darker green top border, dark green text. Incorrect: pale red background, pink border, red text.

Brilliant, inferred from help docs and reviews:
- One question per screen, progress bar on top, Check then Continue, explanation reveals after answering, a hint button per problem, and a "Start over" reset on drag interactions.

Memrise, from the session bundle:
- Exercise type ids: multiple_choice, audio_multiple_choice, tapping, typing, speaking, video. Tapping replaces multiple choice when the answer has three or more words. Number-key shortcuts select tiles.
- Instruction strings such as "Choose the answer you hear" and "Place the words in the order you hear them".

What RizalAI borrows:
- Top bar of close, progress, hearts. Single bottom call to action with a lip. Bottom feedback sheet in semantic green or red. These are the runner grammar every learner already knows.
- One exercise per screen with the answer key local, which our thin-client design already requires.
- Exercise instruction strings in the Memrise style, written in English, with the Tagalog prompt below.
- Word tiles for sentence_assembly and listen_tap: wrapping row of tiles, an answer row above, tap to move, number-key shortcuts on desktop, a reset. Tiles are 44px minimum touch targets.
- Hint button per exercise. In RizalAI the hint is the English gloss of one tapped word, served from the lesson's target_vocab, never from the LLM in the request path.

## 4. Story vignette patterns

Duolingo Stories, from Redux action names in the bundle:
- Element types: HEADER, LINE, MULTIPLE_CHOICE, SELECT_PHRASE, POINT_TO_PHRASE, ARRANGE, MATCH, FREEFORM_WRITING. Lines reveal one at a time, audio auto-plays per line, Continue advances, replay is available and slows on repeat. Tap-word hints are tracked. Questions are interleaved and must be answered to proceed. The story ends with a match-pairs exercise.

80 Days, from a screenshot in the ink repository and interviews:
- Short conversational bursts, tap to continue, no auto-scroll. A slight pause before choices appear.
- Already-read paragraphs stay on screen dimmed to gray. The current paragraph is bright.
- Choices are inline sentence completions beginning with an ellipsis, rendered in a lighter tint inside the paragraph.
- Text sits in a rounded translucent dark panel over a mostly static scene. Attribution is in prose, not name labels. A status chip carries money, day, and time.
- The ink authoring format is plain text with knots, choices, diverts, and per-line tags. The runtime yields one line at a time with its tags.

What RizalAI borrows:
- Vignette is an ordered list of beats. Each beat has speaker, tl, en, audio_url, and an optional exercise reference. This is the ink idea (one line per beat, tags for presentation) in our YAML, without the ink dependency, because our vignettes are linear.
- Line-by-line reveal with tap to continue, history dimmed, current line bright, audio auto-play per line with a replay control that slows on the second replay.
- Interleaved exercises between beats, in the Duolingo Stories manner, so the learner cannot skim the passage.
- A small status chip on the vignette screen: place and year ("Maynila, 1880s"). Atmosphere comes from the chip and a muted scene tint, not from illustrations we do not have.
- Speaker labels in small caps as a RizalAI addition, because a zero-knowledge learner cannot parse "sabi ni Kapitan Tiago" yet.

## 5. Passage reader patterns for the "In Rizal's voice" card

LingQ, from support docs and the 5.0 announcement:
- Three word states: new (blue), learning (yellow), known (plain). Blue words become known when the learner pages forward. Keyboard shortcuts mark known or ignore.
- Tapping a word opens a bottom sheet on mobile with the most popular meaning first, expandable to more dictionaries, with word audio auto-played.
- Sentence mode shows one sentence at a time with a "Translate Sentence" button. A known bug: the translation overlays the sentence and covers it when the sentence wraps.
- Whole-lesson translation shows line by line inside the reader. Karaoke highlight requires timestamped audio.
- Reader typography is user-adjustable: twelve fonts, line spacing 1.0 to 3.0, highlight or underline style.

Bunpro, from shipped CSS:
- Furigana is native ruby markup at 46 percent font size, toggled by a root data attribute (show on hover, forced, or hidden). Font size is a root data attribute at 12, 16, or 20px.
- Grammar point page order: title with level badge, structure panel, details, prose, synonyms, antonyms, related grammar cards with a one-line contrast, examples with the target bolded, resources with offline citations, discussion.

What RizalAI borrows:
- The card shows the passage in three stacked layers: Spanish (Rizal's own words, labeled), Poblete 1909 Tagalog (labeled as a 1909 translation), Derbyshire English (labeled). Each layer is collapsible. The generated reflection sits below in its own visually distinct block, with the toggle for Tagalog and English and quoted spans styled as citations linking to the passage layer.
- Tap a Tagalog word in the vignette to open a bottom sheet: gloss first, then part of speech, then the modern spelling if the word came from the 1909 text. Word audio auto-plays.
- Show translation as a toggle that expands below the line, never as an overlay, to avoid LingQ's wrap bug.
- Root data attributes for reading aids: data-gloss (inline glosses on or off) and data-font-size (small, medium, large). Same mechanism Bunpro uses for furigana, applied to Tagalog glosses.
- Grammar focus display follows the Bunpro order: structure first, explanation, examples with the target bolded and a citation line, related patterns.

## 6. Review session patterns

Bunpro, from community threads and reviews:
- Cloze card, Space reveals a short hint, Space again reveals the full translation with the target in blue. Three question modes: fill-in, translate, reveal and self-grade with Hard and Good.
- Grading is typo tolerant: a near miss prompts a retry before counting as wrong. Politeness mismatch warns without failing.
- After answering, the SRS stage change shows as a colored badge top right. Grammar info opens in a drawer on mobile.
- Dashboard shows reviews due count, a forecast of upcoming reviews, a past-review chart, and streak. Summary is a rolling 24 hour view with accuracy and wrong answers linked back to their grammar points.

Memrise, from help docs and session strings:
- Learn New Words moves a word to learned after six correct tests. Classic Review resurfaces learned items by spaced repetition using the same four test types. Summary strings include words fully learned, started learning, and points earned.

What RizalAI borrows:
- Review session reuses the four exercise types rather than introducing a cloze format at MVP. FSRS decides the queue.
- Typo tolerant retry for typed answers when typing arrives; at MVP all answers are tile-based so this is deferred.
- After each review answer, a small stage badge shows the FSRS state change (new, learning, review).
- Practice-to-refill hearts flow is a review session with a fixed length of 10 items.
- Session summary: accuracy, XP earned, items that moved state, wrong items linked to their lesson.

## 7. Proposed design direction for RizalAI

This is a proposal, to be approved before implementation.

Typography:
- Body and UI: Nunito (OFL), the common open substitute for rounded learning-app faces. Weights 400, 600, 700, 800.
- Passage layers on the card: a serif for the Spanish and 1909 Tagalog to mark them as historical text. Candidate: Source Serif 4 (OFL) or Literata (OFL). Modern Tagalog vignette lines stay in Nunito so the drilled text reads as contemporary.
- Base 16px on mobile, line-height 1.5, vignette lines at 18px, labels uppercase 13px 700 with 0.04em tracking.
- Diacritics (ñ, á, é, í, ó, ú) are in Latin-1 for all three candidates. Preload only the Latin range, as Bunpro does.

Color:
- Own palette, not any reference app's primary. Direction: deep indigo as the primary (the color of Rizal-era ink and the Philippine flag's blue), warm ochre as the XP and completed accent, and a paper cream surface for the passage card. Semantic feedback green and red are independent of the brand hue.
- Tokens as RGB triplets on data-theme light and dark with color-scheme set, following Bunpro and Duolingo. shadcn's semantic token names (background, foreground, primary, muted, destructive) map cleanly.

Shape and motion:
- Radii 12px on buttons and tiles, 16px on cards. 2px borders on outlined elements. Button lip as a 4px solid box-shadow that collapses on press over 0.1s.
- Feedback sheet slides up 0.3s. Line reveal on the vignette fades in 0.2s. Respect prefers-reduced-motion by disabling slides.

Component plan on shadcn/ui:
- Button (extended with a lip variant), Progress, Sheet (feedback and word gloss), Popover (tree node), Badge (SRS stage, XP), Toggle (translation reveal), Card (passage layers), Collapsible (language layers), Dialog (hearts empty).
- Custom: PathNode, WordTile, TileBank, VignetteLine, StatusChip, PassageLayers, ReflectionBlock.

## 8. Trade dress and licensing: avoid list

- Duolingo: the owl and named characters (registered marks), the green #58cc02 plus gold-node winding path silhouette, Feather-like letterforms, the animal color names, the bouncy rounded illustration style.
- Brilliant: CoFo fonts, the pear yellow-green call-to-action and streak color, the Koji mascot and illustration style, Rive gameboard art, "Level Review" naming with their level bullets.
- Memrise: Boing, yellow #FFBB00 on navy #001122 as a primary pair, the blooming flower mastery meter, the Ziggy mascot, "Learn with Locals".
- 80 Days: the deco condensed header chips combined with black silhouette art, the globe with route lines, the exact look of ellipsis options inside a dark panel.
- LingQ: nothing distinctive beyond the three-color word states, which are a generic reader convention. DM Sans is OFL if wanted.
- Bunpro: nothing distinctive found. Their SRS stage color tokens are a structure, not a look.

Generic patterns that are safe because they predate all six apps: top progress bar with close and lives, a single bottom call to action, green and red feedback, vertical node path with locked, active, and done states, line-by-line story reveal, tap-word glosses, inline sentence-completing choices, tile reordering, cloze with staged hints, per-item mastery indicator of our own form.

This is not legal advice. If the product ships publicly with revenue, have the visual identity reviewed.

## 9. Sources

Each research report cited its sources inline; the primary ones were:
- Duolingo shipped CSS and JS on d35aaqx5ub95lt.cloudfront.net, blog.duolingo.com posts on the home screen redesign, character visemes, and shape language, fontsinuse.com entries for Feather Bold and the app body face.
- LingQ static CSS bundles on static.lingq.com, lingq.com blog on 5.0, the LingQ support center and forums.
- inkle press kit, Game Developer postmortem and interview on 80 Days, the ink documentation and issue 292 screenshot on GitHub.
- Brilliant homepage and course page __NEXT_DATA__, Panda CSS bundle, the Koto brand refresh writeup, Rive blog, Brilliant help center.
- Bunpro homepage CSS bundle, the community tech stack thread, Reviews 2.0 thread, SRS interval threads, Tofugu review.
- Memrise app shell and Next.js chunks, Memrise help center, A2-Type Boing page, community forum mirrors.
