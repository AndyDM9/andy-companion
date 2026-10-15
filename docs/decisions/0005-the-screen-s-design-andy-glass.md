# 0005: The screen's design, "Andy Glass"

**Date:** 2026-10-13. **Status:** accepted.

## Context

Andy's screen is a TV beside the robot, read from across a room by an older adult. It should look as
current as anything in the home, and it must stay readable. Apple's design language since 2025,
Liquid Glass (iOS 26, tvOS 26), is what "current" looks like to most people. It also drew the
sharpest usability criticism of the year, for text that disappears into what is behind it.

Research, true on 2026-10-13, read from Apple's own pages and talks:

- **Apple's glass:** [Human Interface Guidelines: Materials](https://developer.apple.com/design/human-interface-guidelines/materials),
  [Color](https://developer.apple.com/design/human-interface-guidelines/color),
  [Layout](https://developer.apple.com/design/human-interface-guidelines/layout),
  [Typography](https://developer.apple.com/design/human-interface-guidelines/typography),
  [Motion](https://developer.apple.com/design/human-interface-guidelines/motion),
  [Accessibility](https://developer.apple.com/design/human-interface-guidelines/accessibility);
  WWDC25 [Meet Liquid Glass](https://developer.apple.com/videos/play/wwdc2025/219/) and
  [Get to know the new design system](https://developer.apple.com/videos/play/wwdc2025/356/).
- **Apple TV:** Apple's [tvOS 26 announcement](https://www.apple.com/newsroom/2025/06/apple-tv-brings-a-beautiful-redesign-and-enhanced-home-entertainment-experience/).
- **The criticism:** Nielsen Norman Group, [Liquid Glass Is Cracked, and Usability Suffers in iOS 26](https://www.nngroup.com/articles/liquid-glass/)
  (2025-10-10).
- **Browser support:** MDN's compatibility data.

## Decision

The screen takes Apple's glass where it helps and leaves it where it hurts reading. Every text colour
must stay at 7:1 (WCAG AAA) against the worst case behind it, tested.

**Taken from Apple:**

- **Frosted panels over a living scene.** The panels are frosted glass ("regular" glass, the kind
  meant for text, never "clear"). The scene behind them is three soft lights in the time of day's
  colours, or the family photo, blurred. The scene moves over minutes, never seconds.
- **A specular edge lit from where the light is.** On Apple's devices the light responds to the
  device's motion. Andy's TV doesn't move, so here the light follows the sun's path through the day:
  from the left in the morning, from above at noon, from the right in the evening, and dimmer at
  night.
- **Bigger glass is thicker.** The finding card and the photo frame are thicker, with more blur and a
  deeper shadow. The state pill is thinner.
- **Concentric corners.** An inner radius is the outer radius less the padding (WWDC25 356), so a
  photo sits in its frame the way a screen sits in a phone.
- **Glass lights up from within when something arrives.** A new card's edge glows and settles. The
  state pill flexes a little when Andy's state changes.
- **tvOS safe margins.** About 60 px top and bottom and 80 px at the sides at 1080p.
- **When a setting asks for it, the screen becomes plain:** reduce transparency or Calm screen gives
  solid panels; Increase Contrast gives solid panels with an outline and no scene. Apple's own
  equivalents are Reduce Transparency, Increase Contrast and, in iOS 26.1, "Tinted" glass.

**Left out, and why:**

- **Glass behind running text.** The captions stay solid. NN/g found that text over glass was the
  weakest point of iOS 26.
- **Springs that overshoot.** Nothing bounces past where it rests; a test checks every easing curve.
- **Glass that switches between light and dark** with what is behind it. The screen's colours change
  only with the time of day.
- **SVG refraction** (true lensing at the edges). Safari and Firefox can't draw it behind an element,
  and it is untested on a 2022 TV's browser (Chromium 85).
- **CSS that a 2022 TV doesn't have.** For example, the `inset` shorthand arrived in Chromium 87.
  The angle of the light animates through `@property`, which Chromium 85 has.
- **Apple's typeface.** SF Pro's licence is for Apple platforms. The screen uses Atkinson
  Hyperlegible (SIL Open Font License), designed by the Braille Institute for low vision.

## Consequences

- `tests/test_screen_design.py` holds the rules:
  - the 7:1 worst case for every colour pair, glow and photo, in each part of the day;
  - concentric corners;
  - no overshooting easing;
  - no `inset` shorthand;
  - the solid fallbacks;
  - the light's path through the day.
- On a TV that can't blur (no `backdrop-filter`), the panels are solid and nothing else changes.
- The look costs little to draw: the blur sits on four still panels, and the lights behind them move
  slowly enough that a TV can keep up. It still has to be measured on a real 2022 TV before we claim
  it runs well there.

## Amended 2026-10-14 (from the founder's report on the real TV)

- **One steady clock size.** The clock used to shrink and grow, with an animation, whenever a card, a photo
  or a caption came or went, and read as "the time keeps shifting". It keeps one size; nothing moves when
  something appears.
- **Captions like a TV's subtitles.** Everything Andy says, paged three lines at a time at about its
  speaking pace, laid over the foot of the screen (no empty band kept for them), and kept to the left
  column while the settings QR code is up, never over it.
- **A card gives way to the family photos after five minutes** (it was 15).
- **A gear for Settings** (the settings code, Under the hood), for a mouse or the TV's remote: arrow keys,
  OK, Back.
- **How a web answer was found,** in small type under its sources.
`tests/test_screen_design.py` keeps the clock's single size, the captions' overlay and the gear.
