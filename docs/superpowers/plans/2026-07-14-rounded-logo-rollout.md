# Rounded Logo Rollout Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the public website’s existing mark with the selected Rounded 02 logo across header, footer, research field, favicon, and Open Graph artwork.

**Architecture:** One Astro component owns the inline horizontal/mark/small SVG geometry and accessible semantics. A deterministic Python asset generator verifies the source ZIP and creates stable favicon, PNG, and OG outputs. Existing page structure and metadata URLs remain unchanged.

**Tech Stack:** Astro 5, inline SVG, CSS, Python 3.13, Pillow, ImageMagick/RSVG when available, Playwright

## Global Constraints

- Verify `/home/argustest/argustest2/argus-logo-final-02-rounded.zip.sha256` before extraction.
- Preserve knockout eye transparency.
- Header desktop logo: 92×32 px; mobile: 76×27 px.
- Footer logo: approximately 82×28 px.
- Research Field mark: 58×58 px.
- Favicon must use the small 16–32 px geometry and a deep-blue single color.
- OG output must remain exactly 1200×630 at `/assets/argus-og-blue-gold.png`.
- Do not replace the kinetic ARGUS type universe or body typography.
- Add no runtime JavaScript.

---

### Task 1: Verified Logo Source and Generator

**Files:**
- Create: `scripts/generate_rounded_logo_assets.py`
- Create: `scripts/test_generate_rounded_logo_assets.py`

**Interfaces:**
- Produces: `verify_archive()`, `extract_svg_sources()`, `recolor_svg()`, and `generate_assets()`.
- Consumes: the selected ZIP and SHA256 sidecar outside the website repository.

- [ ] **Step 1: Write the failing generator tests**

Create `scripts/test_generate_rounded_logo_assets.py`:

```python
import tempfile
import unittest
from pathlib import Path

from generate_rounded_logo_assets import recolor_svg, verify_archive


class RoundedLogoGeneratorTest(unittest.TestCase):
    def test_verified_archive_and_current_color_svg(self):
        archive = Path("/home/argustest/argustest2/argus-logo-final-02-rounded.zip")
        sidecar = Path(f"{archive}.sha256")
        verify_archive(archive, sidecar)
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "mark.svg"
            recolor_svg(
                "<svg><path fill=\"#000000\" d=\"M0 0h1v1z\"/></svg>",
                output,
            )
            text = output.read_text()
            self.assertIn('fill="currentColor"', text)
            self.assertNotIn("#000000", text)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the test and verify the import fails**

```bash
PYTHONPATH=scripts python -m unittest scripts/test_generate_rounded_logo_assets.py -v
```

Expected: FAIL because the generator module does not exist.

- [ ] **Step 3: Implement archive verification and SVG extraction**

Create `scripts/generate_rounded_logo_assets.py`:

```python
from __future__ import annotations

import hashlib
import json
import re
import shutil
import tempfile
import zipfile
from pathlib import Path

from PIL import Image, ImageDraw


ARCHIVE_ROOT = "argus-logo-final-02-rounded"


def verify_archive(archive: Path, sidecar: Path) -> None:
    expected = sidecar.read_text(encoding="utf-8").split()[0]
    actual = hashlib.sha256(archive.read_bytes()).hexdigest()
    if actual != expected:
        raise ValueError(f"logo archive checksum mismatch: {actual} != {expected}")


def recolor_svg(source: str, output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(source.replace("#000000", "currentColor"), encoding="utf-8")


def extract_svg_sources(archive: Path, output_dir: Path) -> dict[str, Path]:
    mapping = {
        "horizontal": "svg/argus-logo-horizontal.svg",
        "mark": "svg/argus-mark.svg",
        "small": "svg/argus-mark-small.svg",
    }
    result = {}
    with zipfile.ZipFile(archive) as bundle:
        for key, relative in mapping.items():
            source = bundle.read(f"{ARCHIVE_ROOT}/{relative}").decode("utf-8")
            target = output_dir / f"argus-{key}-rounded.svg"
            recolor_svg(source, target)
            result[key] = target
    return result
```

- [ ] **Step 4: Implement deterministic raster output**

Add generator functions that:

- Extract `png/marks/argus-mark-128.png`, `argus-mark-16.png`, `argus-mark-32.png`, and `argus-mark-48.png`.
- Recolor non-transparent source pixels to website deep blue `(7, 95, 228)`.
- Preserve alpha exactly.
- Write `public/assets/argus-mark-gold.png` as a 256×256 transparent PNG made from the 256 px source and recolored with a blue-to-gold diagonal gradient.
- Write `public/assets/argus-mark-rounded-favicon.ico` containing 16, 32, and 48 px deep-blue layers.
- Compose `public/assets/argus-og-blue-gold.png` at 1200×630 with the existing blue/gold background treatment, centered rounded mark, and `ARGUS` title.
- Emit `public/assets/argus-logo-rounded-horizontal.svg`, `argus-mark-rounded.svg`, and `argus-mark-rounded-small.svg`.

Expose a CLI:

```bash
python scripts/generate_rounded_logo_assets.py \
  --archive /home/argustest/argustest2/argus-logo-final-02-rounded.zip \
  --sidecar /home/argustest/argustest2/argus-logo-final-02-rounded.zip.sha256 \
  --output-dir public/assets
```

- [ ] **Step 5: Run tests and generate assets**

```bash
PYTHONPATH=scripts python -m unittest scripts/test_generate_rounded_logo_assets.py -v
python scripts/generate_rounded_logo_assets.py \
  --archive /home/argustest/argustest2/argus-logo-final-02-rounded.zip \
  --sidecar /home/argustest/argustest2/argus-logo-final-02-rounded.zip.sha256 \
  --output-dir public/assets
```

Expected: tests PASS and all assets exist.

- [ ] **Step 6: Verify static dimensions and alpha**

```bash
python - <<'PY'
from PIL import Image
from pathlib import Path
root = Path("public/assets")
assert Image.open(root / "argus-mark-gold.png").size == (256, 256)
assert Image.open(root / "argus-og-blue-gold.png").size == (1200, 630)
ico = Image.open(root / "argus-mark-rounded-favicon.ico")
assert set(ico.info["sizes"]) >= {(16, 16), (32, 32), (48, 48)}
assert Image.open(root / "argus-mark-gold.png").mode == "RGBA"
PY
```

- [ ] **Step 7: Commit the generator and assets**

```bash
git add scripts/generate_rounded_logo_assets.py scripts/test_generate_rounded_logo_assets.py public/assets
git commit -m "feat: generate Rounded 02 brand assets"
```

---

### Task 2: Reusable Inline Logo Component

**Files:**
- Create: `src/components/ArgusLogo.astro`
- Modify: `src/styles/global.css`
- Modify: `scripts/check-bilingual.mjs`

**Interfaces:**
- Consumes: Rounded 02 geometry from Task 1.
- Produces: `ArgusLogo` props `{ variant?: "horizontal" | "mark" | "small"; class?: string; label?: string; decorative?: boolean }`.

- [ ] **Step 1: Add failing built-output checks**

In `scripts/check-bilingual.mjs`, require:

```js
for (const html of pages.values()) {
  assert.doesNotMatch(html, /argus-mark-gold\.png/);
}
for (const path of ["index.html", "zh.html"]) {
  const html = pages.get(path);
  assert.match(html, /data-argus-logo="horizontal"/);
  assert.match(html, /data-argus-logo="mark"/);
}
```

- [ ] **Step 2: Run build and verify the old PNG assertion fails**

```bash
npm run build
```

Expected: FAIL because Header, Footer, and Research Field still reference `argus-mark-gold.png`.

- [ ] **Step 3: Create `ArgusLogo.astro`**

Implement:

- Unique gradient ID using `crypto.randomUUID()` or an Astro-local deterministic suffix.
- Horizontal viewBox `0 0 1400 480`.
- Mark/small viewBox `0 0 512 512`.
- Source path geometry copied exactly from the selected SVGs.
- Gradient stops:
  - `0% var(--blue-dark)`
  - `52% var(--blue)`
  - `100% var(--gold-dark)`
- Forced-colors fallback through a component class.
- Correct `role`, `aria-label`, and `aria-hidden`.

- [ ] **Step 4: Add component size classes**

In `global.css`:

```css
.argus-logo {
  display: block;
  color: var(--blue-dark);
  overflow: visible;
}

.argus-logo--header { width: 92px; height: 32px; }
.argus-logo--footer { width: 82px; height: 28px; }
.argus-logo--research { width: 58px; height: 58px; }

@media (max-width: 680px) {
  .argus-logo--header { width: 76px; height: 27px; }
}

@media (forced-colors: active) {
  .argus-logo { color: CanvasText; }
  .argus-logo stop { stop-color: CanvasText; }
}
```

- [ ] **Step 5: Commit the reusable component**

```bash
git add src/components/ArgusLogo.astro src/styles/global.css scripts/check-bilingual.mjs
git commit -m "feat: add Rounded 02 logo component"
```

---

### Task 3: Header, Footer, Research Field, and Metadata Integration

**Files:**
- Modify: `src/components/Header.astro`
- Modify: `src/components/Footer.astro`
- Modify: `src/components/ResearchField.astro`
- Modify: `src/layouts/SiteLayout.astro`

**Interfaces:**
- Consumes: `ArgusLogo`.
- Produces: all public pages using Rounded 02.

- [ ] **Step 1: Replace Header identity**

Import `ArgusLogo` and replace:

```astro
<img src="/assets/argus-mark-gold.png" width="20" height="20" alt="" />
<span>Argus</span>
```

with:

```astro
<ArgusLogo variant="horizontal" class="argus-logo--header" decorative />
```

Keep the anchor’s accessible home label.

- [ ] **Step 2: Replace Footer identity**

Use:

```astro
<ArgusLogo variant="horizontal" class="argus-logo--footer" decorative />
```

Remove the duplicate literal `Argus` text; preserve tagline and navigation.

- [ ] **Step 3: Replace Research Field mark**

Use:

```astro
<ArgusLogo variant="mark" class="argus-logo--research" decorative />
```

Keep the `ARGUS` label and subtitle.

- [ ] **Step 4: Replace favicon metadata**

In `SiteLayout.astro`, replace the PNG favicon link with:

```astro
<link rel="icon" href="/assets/argus-mark-rounded-favicon.ico" sizes="any" />
<link rel="icon" type="image/svg+xml" href="/assets/argus-mark-rounded-small.svg" />
```

Keep the OG path unchanged.

- [ ] **Step 5: Run bilingual build**

```bash
npm run build
```

Expected: Astro check, build, and bilingual checker PASS.

- [ ] **Step 6: Commit integration**

```bash
git add src/components/Header.astro src/components/Footer.astro src/components/ResearchField.astro src/layouts/SiteLayout.astro
git commit -m "feat: adopt Rounded 02 public identity"
```

---

### Task 4: Visual and Deployment Verification

**Files:**
- Modify only files that fail a requirement in Tasks 1–3.

- [ ] **Step 1: Start production preview**

```bash
npm run preview -- --host 127.0.0.1 --port 4323
```

- [ ] **Step 2: Verify responsive sizes in Playwright**

At 390, 768, and 1440 px:

- Assert header SVG bounding box is 76×27 below 680 px and 92×32 otherwise.
- Assert footer SVG is 82×28.
- Assert Research Field mark is 58×58.
- Assert no horizontal overflow.
- Capture light and dark screenshots.

- [ ] **Step 3: Verify SVG semantics**

- Header and Footer anchors retain accessible names.
- Decorative SVGs have `aria-hidden`.
- No duplicate SVG IDs exist on the page.
- Knockout eye regions show page background rather than a painted fill.
- Forced-colors uses `CanvasText`.

- [ ] **Step 4: Verify favicon and OG assets**

- Render favicon at 16, 32, and 48 px and compare against the archive size board.
- Confirm OG image is 1200×630 and contains the new rounded mark.
- Verify all 12 pages reference the new favicon.

- [ ] **Step 5: Deploy atomically**

Build a versioned static directory, switch `argus-website-http.service`, and restart only the 8792 origin service.

- [ ] **Step 6: Verify public delivery**

Compare origin and public SHA256 for:

- `/`
- `/zh.html`
- `/assets/argus-mark-rounded-favicon.ico`
- `/assets/argus-og-blue-gold.png`

Re-run Playwright checks against `https://argusbot.cn`.

- [ ] **Step 7: Remove temporary extraction**

```bash
rm -rf /tmp/argus-logo-rounded
```

Keep the verified source ZIP in place.
