# Rounded Logo Rollout Design

## Goal

Adopt the selected `Argus Logo — 02 Rounded` identity across the public website using the existing blue-gold visual language and size-specific artwork.

## Source Asset

Use only the verified archive:

```text
/home/argustest/argustest2/argus-logo-final-02-rounded.zip
```

Its SHA256 sidecar must pass before extraction. The archive supplies:

- Horizontal SVG and PNG
- Stacked SVG and PNG
- Standard mark for 48 px and larger
- Small mark for 16–32 px
- PNG marks at common sizes
- Multi-size favicon

The artwork is pure black on transparent background, with knockout eye details.

## Reusable Component

Create `src/components/ArgusLogo.astro`.

Props:

```ts
type Props = {
  variant?: "horizontal" | "mark" | "small";
  class?: string;
  label?: string;
  decorative?: boolean;
};
```

Rules:

- Inline the selected SVG geometry rather than referencing an external SVG file.
- Replace source `#000000` fills with `currentColor`.
- Preserve the source view boxes and even-odd fill rules.
- Add no runtime JavaScript.
- Use `aria-hidden="true"` when decorative.
- Use `role="img"` and `aria-label` when meaningful.

## Color Treatment

The component receives a blue-gold gradient through CSS:

```text
light: blue-dark → blue → gold-dark
dark: blue → cyan highlight → gold
```

Use an SVG gradient definition, not CSS filters, so the transparent eye knockouts remain clean. Generate unique gradient IDs per component instance to avoid collisions.

Single-color fallback:

- Default to `var(--blue-dark)`.
- Under forced colors, use `CanvasText`.

## Placement and Sizes

Header:

- Use horizontal logo.
- Desktop: 92×32 px visual box.
- Mobile: 76×27 px.
- Remove the separately rendered mark and `Argus` text.
- Keep the existing home link and accessible label.

Footer:

- Use horizontal logo at approximately 82×28 px.
- Keep the tagline and navigation unchanged.

Research Field:

- Use the standard mark at 58×58 px.
- Keep `ARGUS` and the core subtitle below it.

Favicon:

- Use the small mark geometry.
- Produce 16, 32, and 48 px favicon layers.
- Use a single deep-blue fill for clarity; do not use a multi-stop gradient at favicon size.

Open Graph:

- Preserve the existing 1200×630 blue-gold composition.
- Replace its central mark with the Rounded 02 standard mark.
- Preserve the existing asset path so page metadata does not change.

Do not replace:

- The kinetic ARGUS type universe.
- Body typography.
- Terminal/Web workbench identity in this task.

## Static Assets

Create:

- `public/assets/argus-logo-rounded-horizontal.svg`
- `public/assets/argus-mark-rounded.svg`
- `public/assets/argus-mark-rounded-small.svg`
- `public/assets/argus-mark-rounded-favicon.ico`

Overwrite after visual verification:

- `public/assets/argus-mark-gold.png`
- `public/assets/argus-og-blue-gold.png`

Keep the old filenames only where stable metadata URLs require them.

## Validation

- Verify the archive checksum before every generation.
- Confirm header and footer logos retain aspect ratio.
- Confirm no SVG ID collision when multiple logos appear on one page.
- Check 390, 768, and 1440 px.
- Check light, dark, forced-colors, and reduced-motion modes.
- Verify favicon at 16, 32, and 48 px.
- Verify OG output is exactly 1200×630.
- Confirm transparent eye knockouts remain transparent.
- Confirm all 12 bilingual pages build and internal links remain valid.
- Compare public and origin asset hashes after deployment.
