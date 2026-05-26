---
name: Pro-Editor Aesthetic
colors:
  surface: '#0b1326'
  surface-dim: '#0b1326'
  surface-bright: '#31394d'
  surface-container-lowest: '#060e20'
  surface-container-low: '#131b2e'
  surface-container: '#171f33'
  surface-container-high: '#222a3d'
  surface-container-highest: '#2d3449'
  on-surface: '#dae2fd'
  on-surface-variant: '#c2c6d6'
  inverse-surface: '#dae2fd'
  inverse-on-surface: '#283044'
  outline: '#8c909f'
  outline-variant: '#424754'
  surface-tint: '#adc6ff'
  primary: '#adc6ff'
  on-primary: '#002e6a'
  primary-container: '#4d8eff'
  on-primary-container: '#00285d'
  inverse-primary: '#005ac2'
  secondary: '#b9c8de'
  on-secondary: '#233143'
  secondary-container: '#39485a'
  on-secondary-container: '#a7b6cc'
  tertiary: '#ffb786'
  on-tertiary: '#502400'
  tertiary-container: '#df7412'
  on-tertiary-container: '#461f00'
  error: '#ffb4ab'
  on-error: '#690005'
  error-container: '#93000a'
  on-error-container: '#ffdad6'
  primary-fixed: '#d8e2ff'
  primary-fixed-dim: '#adc6ff'
  on-primary-fixed: '#001a42'
  on-primary-fixed-variant: '#004395'
  secondary-fixed: '#d4e4fa'
  secondary-fixed-dim: '#b9c8de'
  on-secondary-fixed: '#0d1c2d'
  on-secondary-fixed-variant: '#39485a'
  tertiary-fixed: '#ffdcc6'
  tertiary-fixed-dim: '#ffb786'
  on-tertiary-fixed: '#311400'
  on-tertiary-fixed-variant: '#723600'
  background: '#0b1326'
  on-background: '#dae2fd'
  surface-variant: '#2d3449'
typography:
  headline-lg:
    fontFamily: Sora
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
    letterSpacing: -0.02em
  headline-md:
    fontFamily: Sora
    fontSize: 18px
    fontWeight: '600'
    lineHeight: 24px
    letterSpacing: -0.01em
  body-md:
    fontFamily: Sora
    fontSize: 14px
    fontWeight: '400'
    lineHeight: 20px
  body-sm:
    fontFamily: Sora
    fontSize: 13px
    fontWeight: '400'
    lineHeight: 18px
  label-mono:
    fontFamily: JetBrains Mono
    fontSize: 12px
    fontWeight: '500'
    lineHeight: 16px
    letterSpacing: 0.02em
  label-caps:
    fontFamily: JetBrains Mono
    fontSize: 10px
    fontWeight: '700'
    lineHeight: 12px
    letterSpacing: 0.05em
rounded:
  sm: 0.125rem
  DEFAULT: 0.25rem
  md: 0.375rem
  lg: 0.5rem
  xl: 0.75rem
  full: 9999px
spacing:
  unit: 4px
  gutter: 1px
  sidebar-width: 260px
  toolbar-height: 40px
  panel-padding: 12px
---

## Brand & Style

The design system is engineered for high-performance productivity, targeting professionals in technical and creative fields. The aesthetic is inspired by integrated development environments (IDEs) and professional non-linear editors. It prioritizes information density, functional clarity, and a "mechanical" feel that suggests precision and power.

The style is a hybrid of **Minimalism** and **Technical Brutalism**. It utilizes a dark, monochromatic foundation to reduce eye strain during long sessions, while employing sharp, 1px borders to define a rigid structure. The interface should feel like a tool—unobtrusive, efficient, and highly organized.

## Colors

The palette is anchored in a deep slate and charcoal spectrum to create a sophisticated, low-light environment. 

- **Primary:** A vibrant Blue (#3b82f6) is used sparingly for active states, primary actions, and focus indicators.
- **Surface Scale:** Uses a tiered approach of dark neutrals to distinguish between the background canvas, sidebar panels, and modal overlays.
- **Borders:** A consistent slate border (#1e293b) is the primary tool for layout separation, replacing shadows.
- **Accents:** Success, warning, and error states should use desaturated versions of green, amber, and red to maintain the professional, restrained aesthetic.

## Typography

The typography system balances modern geometry with technical legibility. **Sora** is the primary typeface for headers and UI text, offering a clean, wide-set look that remains readable at small sizes. **JetBrains Mono** is utilized for metadata, technical labels, and status indicators to reinforce the editor aesthetic.

- **Scale:** Sizes are kept intentionally small (13px - 14px for body) to facilitate high information density.
- **Contrast:** High contrast is maintained between primary text (white/slate-50) and secondary text (slate-400).
- **Technicality:** Use monospaced labels for numerical data, coordinates, or timecodes to ensure character alignment in dense tables and sidebars.

## Layout & Spacing

This design system uses a **Fixed-Panel Grid** model. Rather than a fluid container, the layout is composed of persistent functional zones: Navigation Bar, Sidebars (Left/Right), Main Viewport, and a Bottom Panel (Timeline/Console).

- **Density:** Spacing is tight, built on a 4px base unit. 12px is the standard padding for internal containers.
- **Separation:** Divisions are created by 1px solid borders rather than margins or gutters.
- **Breakpoints:** 
  - **Desktop (1280px+):** Full multi-panel view.
  - **Tablet (768px - 1279px):** Sidebars become collapsible icons.
  - **Mobile:** Single panel focus with a bottom navigation bar for context switching.

## Elevation & Depth

Depth is conveyed through **Tonal Layering** and **Borders**, not shadows.

1. **Canvas (Level 0):** The darkest layer, used for the main workspace or background.
2. **Panels (Level 1):** Slightly lighter slate, used for sidebars and toolbars. Separated by 1px borders.
3. **Floating UI (Level 2):** Context menus and tooltips use a slightly higher tonal value with a subtle 1px border.
4. **Active State:** The primary accent color (#3b82f6) is used as a "glow" or high-contrast highlight on the 1px border of the focused element.

## Shapes

The shape language is strictly geometric and professional. 

- **Containers:** Square corners (0px) for all major layout panels and viewport sections to maximize screen real estate.
- **UI Elements:** Buttons, input fields, and tags use a minimal 4px (`0.25rem`) radius. 
- **Active Indicators:** Tabs and selection states should use sharp, rectangular indicators (vertical or horizontal bars) to match the IDE aesthetic.

## Components

### Buttons
- **Primary:** Solid #3b82f6 background, white text, 4px radius.
- **Ghost:** Transparent background, 1px border (#1e293b). On hover, background shifts to a subtle slate-800.
- **Icon Buttons:** Fixed 28x28px or 32x32px squares.

### Inputs & Fields
- **Search/Text:** 1px border on all sides. Background is darker than the panel it sits on. Use monospaced font for technical values.
- **Dropdowns:** Sharp corners, 1px border, utilizing a "chevron-down" icon.

### Layout Components
- **Panels:** Headers should have a subtle bottom border and use `label-caps` for titles.
- **Tabs:** "Folder style" tabs with a top-border highlight in primary blue for the active state.
- **Tree Lists:** High-density lists with 1px indentation guides for nested folders/files.

### Control Elements
- **Sliders/Scrubbers:** 2px height tracks with a small 12px square or circular handle. 
- **Checkboxes:** Small 14px squares with a 2px radius and sharp checkmark.