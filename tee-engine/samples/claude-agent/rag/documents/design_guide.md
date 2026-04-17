# Grain & Ground — Design System Reference

## Color Palette
- `--clr-bg: #F5F0EB` — page background, card fill, hero background
- `--clr-dark: #3B2314` — primary text, dark section backgrounds
- `--clr-accent: #C07A5A` — accent lines, CTA borders, price text, rule elements
- `--clr-mid: #A0623E` — hover states, secondary accents

Always use CSS custom properties. Never hardcode color hex values outside of :root.

## Typography
Load via Google Fonts:
  @import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,400;0,600;1,400&family=Inter:wght@400;500&display=swap')

- `--ff-serif: 'Cormorant Garamond', Georgia, serif` — headings
- `--ff-sans: 'Inter', system-ui, sans-serif` — body

Scale:
- Hero h1: clamp(3rem, 8vw, 6rem), weight 400, letter-spacing -0.01em, font-family serif
- Section h2: clamp(2rem, 4vw, 3.2rem), weight 400, font-family serif
- Card h3: 1.5rem, weight 600, font-family serif
- Body p: 1rem, line-height 1.75, font-family sans
- Labels: 0.78rem, weight 500, letter-spacing 0.14em, text-transform uppercase, color accent

## Spacing
- Section vertical padding: 7rem (mobile: 4.5rem)
- Content max-width: 1100px, centered (margin: 0 auto; padding: 0 1.5rem)
- Grid gap: 2rem
- Card padding: 2.5rem
- Readable paragraph max-width: 680px

## Section Header Pattern (used in Story, Menu, Shop, Visit)
```
<div class="section-header fade-in">
  <span class="label">Our Story</span>
  <hr class="rule">
  <h2>Where Coffee Begins</h2>
</div>
```
CSS:
- .label: display block, --clr-accent, 0.78rem, letter-spacing 0.14em, uppercase, text-align center
- .rule: display block, width 40px, height 1px, border none, background --clr-accent, margin 1rem auto 1.5rem
- h2: text-align center

## Menu Card Pattern
```html
<article class="menu-card fade-in">
  <div class="card-icon" aria-hidden="true"><!-- exact SVG here --></div>
  <h3>Item Name</h3>
  <p class="card-desc">Single-origin description, region.</p>
  <span class="price">₩7,500</span>
</article>
```
CSS:
- .menu-card: background var(--clr-bg), padding 2.5rem, border 1px solid rgba(192,122,90,0.2), text-align center
- .card-icon: width 120px, height 120px, margin 0 auto 1.5rem, display flex, align-items center, justify-content center
- .card-icon svg: width 100%, height 100%
- h3: font-family serif, 1.5rem, weight 600, margin-bottom 0.6rem
- .card-desc: font-family sans, 0.9rem, line-height 1.6, color rgba(59,35,20,0.75), margin-bottom 1rem
- .price: font-family sans, weight 500, color var(--clr-accent), font-size 1rem

## CTA Button Pattern
```html
<a href="#" class="btn">Shop Beans & Goods</a>
```
CSS:
- .btn: display inline-block, border 1.5px solid var(--clr-accent), color var(--clr-accent)
- padding: 0.85rem 2.5rem, letter-spacing 0.07em, text-decoration none, font-family sans, font-size 0.9rem
- transition: background 0.25s ease, color 0.25s ease
- hover: background var(--clr-accent), color var(--clr-bg)
- border-radius: 2px (keep crisp)

## Navigation
- position: sticky, top 0, z-index 100
- background: rgba(245,240,235,0.93), backdrop-filter: blur(10px)
- border-bottom: 1px solid rgba(192,122,90,0.15)
- content: brand name left in Cormorant Garamond 1.3rem
- padding: 1.25rem 1.5rem
- No right-side nav links needed

## Dark Section (#shop)
- background: var(--clr-dark) — #3B2314
- color: var(--clr-bg) — #F5F0EB
- CTA button on dark: border-color var(--clr-accent), color var(--clr-accent)
- hover: background var(--clr-accent), color var(--clr-dark)

## Scroll Animation
CSS classes:
```
.fade-in { opacity: 0; transform: translateY(24px); transition: opacity 0.65s ease, transform 0.65s ease; }
.fade-in.visible { opacity: 1; transform: translateY(0); }
```
JS (place before </body>):
```
const io = new IntersectionObserver(
  entries => entries.forEach(e => { if (e.isIntersecting) e.target.classList.add('visible'); }),
  { threshold: 0.1 }
);
document.querySelectorAll('.fade-in').forEach(el => io.observe(el));
```

## Footer
- background: var(--clr-dark)
- color: var(--clr-bg), opacity 0.75 for secondary text
- Brand name centered in Cormorant Garamond
- Social links: Instagram icon (SVG inline), email icon (SVG inline)
- Icon links: 40x40px, border 1px solid rgba(245,240,235,0.25), flex centered
- Copyright line: 0.8rem, opacity 0.45

## Seasonal Drink Placeholder (no SVG)
Use a pure CSS circle with a simple coffee-wave pattern:
```html
<div class="card-icon seasonal-icon" aria-hidden="true">
  <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 240 240" fill="none">
    <circle cx="120" cy="120" r="110" fill="#F5F0EB"/>
    <circle cx="120" cy="120" r="60" fill="none" stroke="#C07A5A" stroke-width="2" opacity="0.4"/>
    <path d="M90 120 Q105 110 120 120 Q135 130 150 120" stroke="#C07A5A" stroke-width="2.5" stroke-linecap="round" fill="none" opacity="0.6"/>
    <path d="M95 132 Q110 122 125 132 Q140 142 155 132" stroke="#C07A5A" stroke-width="2" stroke-linecap="round" fill="none" opacity="0.4"/>
    <text x="120" y="170" text-anchor="middle" font-family="serif" font-size="13" fill="#C07A5A" opacity="0.7">Seasonal</text>
  </svg>
</div>
```
