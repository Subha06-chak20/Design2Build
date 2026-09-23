# Visual Verification Checklist

Always inspect the rendered browser screenshot against the reference using these criteria:

### 1. Structure & Layout Flow
- [ ] Are all sections present in the correct order (Nav, Hero, Features, Testimonials, Footer)?
- [ ] Is the content width bounded appropriately (e.g. `max-w-7xl mx-auto px-4`)?
- [ ] Are flexbox / grid columns matching the reference (e.g. 3 columns vs 2 columns)?

### 2. Spacing & Padding
- [ ] Are section vertical paddings (`py-12`, `py-20`) proportional to the reference?
- [ ] Are card inner paddings (`p-6`, `p-8`) consistent?
- [ ] Are item gaps (`gap-4`, `gap-8`) accurately spaced?

### 3. Typography
- [ ] Do heading font weights match (e.g. `font-bold`, `font-extrabold`)?
- [ ] Are font sizes hierarchy aligned (`text-4xl`, `text-xl`, `text-sm`)?
- [ ] Is line height / leading comfortable and matching?
- [ ] Does text wrap at the same natural breaks as the reference?

### 4. Colors & Contrast
- [ ] Does the page background color match (`bg-slate-900`, `bg-gray-50`, custom hex)?
- [ ] Are card background tints accurate (e.g. subtle white on dark, or border-only)?
- [ ] Are brand primary and secondary accent colors faithful?
- [ ] Is text readability/contrast sharp?

### 5. Assets & Visuals
- [ ] Are extracted logos and icons visible at their natural dimensions?
- [ ] Are images styled with proper `object-cover` or `object-contain` without stretching?
- [ ] Do icons match the intended glyphs?

### 6. Borders, Shadows & Radii
- [ ] Are card border radii matching (`rounded-xl`, `rounded-3xl`)?
- [ ] Are drop shadows subtle or prominent (`shadow-sm`, `shadow-xl`, `shadow-2xl`)?
- [ ] Are dividing borders styled with subtle opacity (`border-gray-200`, `border-white/10`)?
