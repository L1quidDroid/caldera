# Branding Plugin for Caldera

Custom branding and theme for Caldera with **Triskele Labs** style guide - a clean, security-focused corporate aesthetic.

## Overview

This plugin customizes Caldera's appearance with:
- **Modern color palette**: Deep navy, bright cyan/teal accents
- **Clean typography**: Sans-serif with strong hierarchy
- **Professional components**: Rounded cards, subtle shadows, bold CTAs
- **Custom templates**: Login page and dashboard overrides
- **Live configuration**: Admin UI for real-time customization

## Features

### 🎨 Triskele Labs Theme

**Color Palette:**
- **Primary Dark**: `#020816` - Deep navy/blue-black for headers and backgrounds
- **Primary Accent**: `#00D1FF` - Bright cyan/teal for CTAs, links, highlights
- **Secondary Gradient**: `#0A3D91` → `#0BC4D9` - Teal gradient for banners
- **Neutral Light**: `#F5F7FA` - Off-white backgrounds
- **Text Colors**: `#1F2937` (dark), `#6B7280` (mid-grey)

**Typography:**
- **Font**: Modern sans-serif system stack (-apple-system, Segoe UI, Roboto)
- **Hierarchy**: H1 (48px bold), H2 (32px semibold), H3 (22px semibold), Body (16px)
- **Style**: Strong weight, large hero text, scannable paragraphs

**Components:**
- Rounded corners (8-16px radius)
- Subtle shadows on cards
- Gradient backgrounds for hero sections
- Professional badges and status indicators
- Animated hover effects
- Responsive design

### 🔧 Configuration

**Customizable via YAML** (`branding_config.yml`):
- All colors (hex values)
- Typography sizes and weights
- Logo paths (header, login, favicon)
- Company name and messaging
- Feature toggles
- Spacing and styling parameters

**Admin Interface** (`/plugin/branding/gui`):
- Live color picker with real-time preview
- Typography configuration
- Text customization
- Save/reset/reload functionality
- Visual preview of changes

### 📄 Template Overrides

**Custom Login Page** (`templates/login.html`):
- Gradient animated background
- Modern card design
- Security badge
- Professional branding
- Responsive layout

**Dashboard Enhancements**:
- Hero headers with gradients
- Improved navigation bar
- Better card layouts
- Status badges
- Alert styling

## Installation

### 1. Enable the Plugin

The plugin is installed in `plugins/branding/`. Caldera will automatically detect it on startup.

```bash
cd /path/to/caldera
# Plugin is already in plugins/branding/
# Restart Caldera to load it
python3 server.py
```

### 2. Verify Plugin Loaded

Check the Caldera logs for:
```
INFO: Branding plugin enabled with theme: triskele_labs
INFO: Primary colors: #020816 / #00D1FF
```

### 3. Access Admin Interface

Navigate to: `http://localhost:8888/plugin/branding/gui`

## Usage

### Access Branding Admin UI

1. Start Caldera: `python3 server.py`
2. Login to Caldera
3. Navigate to: `http://localhost:8888/plugin/branding/gui`
4. Customize colors, typography, and text
5. Click "Save Configuration"

### API Endpoints

**Get Current Configuration:**
```bash
curl http://localhost:8888/plugin/branding/api/config \
  -H "KEY: ADMIN123"
```

**Update Configuration:**
```bash
curl -X POST http://localhost:8888/plugin/branding/api/config \
  -H "KEY: ADMIN123" \
  -H "Content-Type: application/json" \
  -d '{
    "colors": {
      "primary_dark": "#020816",
      "primary_accent": "#00D1FF"
    },
    "customization": {
      "company_name": "Your Company"
    }
  }'
```

### Manual Configuration

Edit `plugins/branding/branding_config.yml`:

```yaml
enabled: true
theme: triskele_labs

colors:
  primary_dark: "#020816"
  primary_accent: "#00D1FF"
  secondary_accent_start: "#0A3D91"
  secondary_accent_end: "#0BC4D9"
  neutral_light: "#F5F7FA"

typography:
  h1_size: "48px"
  h2_size: "32px"
  body_size: "16px"

customization:
  company_name: "Your Company Name"
  tagline: "Your Tagline"
  login_message: "Your Login Message"

logo:
  header_logo: "/plugin/branding/static/img/your_logo.svg"
  favicon: "/plugin/branding/static/img/favicon.ico"
```

Restart Caldera to apply changes.

### Add Custom Logos

1. Place logo files in `plugins/branding/static/img/`:
   - `triskele_logo.svg` - Header logo (180x60px recommended)
   - `triskele_logo_large.svg` - Login page logo (240x80px)
   - `favicon.ico` - Browser favicon (32x32px)

2. Update `branding_config.yml`:
```yaml
logo:
  header_logo: "/plugin/branding/static/img/your_logo.svg"
  login_logo: "/plugin/branding/static/img/your_logo_large.svg"
  favicon: "/plugin/branding/static/img/your_favicon.ico"
```

3. Restart Caldera

## File Structure

```
plugins/branding/
├── hook.py                          # Plugin initialization
├── branding_config.yml              # Configuration file
├── README.md                        # This file
├── static/
│   ├── css/
│   │   └── triskele_theme.css       # Main theme stylesheet
│   └── img/                         # Logo and image assets
│       ├── triskele_logo.svg
│       ├── triskele_logo_large.svg
│       └── favicon.ico
└── templates/
    ├── login.html                   # Custom login page
    └── branding_admin.html          # Admin configuration UI
```

## Customization Guide

### Change Primary Colors

**Option 1: Admin UI**
1. Go to `/plugin/branding/gui`
2. Use color pickers under "Color Palette"
3. See live preview
4. Click "Save Configuration"

**Option 2: Edit YAML**
```yaml
colors:
  primary_dark: "#YOUR_DARK_COLOR"
  primary_accent: "#YOUR_ACCENT_COLOR"
```

### Change Typography

**Edit YAML:**
```yaml
typography:
  h1_size: "56px"      # Larger headings
  h2_size: "36px"
  body_size: "18px"    # Larger body text
  font_family: "Your-Font, sans-serif"
```

**Add Custom Font:**
1. Add font CSS to `static/css/triskele_theme.css`:
```css
@import url('https://fonts.googleapis.com/css2?family=Your+Font');
```

2. Update config:
```yaml
typography:
  font_family: "'Your Font', sans-serif"
```

### Override Additional Templates

To customize more pages:

1. Copy template from `templates/` to `plugins/branding/templates/`
2. Modify the template
3. Update `hook.py` to serve your custom template

Example for custom dashboard:
```python
# In hook.py enable() function:
app.router.add_route('GET', '/dashboard', custom_dashboard_handler)
```

### Add Custom CSS

**Extend theme CSS:**
1. Create `plugins/branding/static/css/custom.css`
2. Add custom styles
3. Link in templates:
```html
<link rel="stylesheet" href="/plugin/branding/static/css/custom.css">
```

## Triskele Labs Style Guide

### Design Principles

- **Clean & Professional**: Lots of whitespace, clear hierarchy
- **Security-Focused**: Dark navy conveys trust, cyan shows innovation
- **Modern**: Rounded corners, subtle shadows, smooth animations
- **Scannable**: Bold headings, short paragraphs, visual hierarchy

### Component Patterns

**Cards:**
```html
<div class="card">
    <div class="card-header">Service Title</div>
    <div class="card-body">
        <p>Service description...</p>
        <button>Learn More</button>
    </div>
</div>
```

**Buttons:**
```html
<!-- Primary CTA -->
<button>Primary Action</button>

<!-- Secondary/Outline -->
<button class="secondary">Secondary Action</button>

<!-- Danger -->
<button class="danger">Delete</button>
```

**Badges:**
```html
<span class="badge-success">Success</span>
<span class="badge-warning">Warning</span>
<span class="badge-danger">Error</span>
<span class="badge-info">Info</span>
```

**Alerts:**
```html
<div class="alert alert-info">Information message</div>
<div class="alert alert-success">Success message</div>
<div class="alert alert-warning">Warning message</div>
<div class="alert alert-danger">Error message</div>
```

### Color Usage

- **Primary Dark** (`#020816`): Navigation, headers, footers, dark sections
- **Primary Accent** (`#00D1FF`): CTAs, links, active states, highlights
- **Secondary Gradient**: Hero backgrounds, feature banners
- **Neutral Light** (`#F5F7FA`): Page background, contrast to white cards
- **Text Dark/Mid**: Body text and secondary text

### Typography Scale

- **H1 (48px, Bold)**: Hero titles, page titles
- **H2 (32px, SemiBold)**: Section headings
- **H3 (22px, SemiBold)**: Subsection headings, card titles
- **Body (16px, Regular)**: Paragraph text, descriptions
- **Small (14px)**: Labels, captions, meta information

## Integration with Caldera

### Automatic Application

The theme CSS is automatically loaded for:
- Login page (custom template)
- All standard Caldera pages (via CSS overrides)
- Plugin admin interface

### Selectors Targeted

- Navigation: `#navbar`, `.navbar`, `header`
- Cards: `.card`, `.panel`, `.section`
- Buttons: `button`, `.btn`
- Forms: `input`, `textarea`, `select`
- Tables: `table`, `th`, `td`

### Preserving Caldera Functionality

All styling is additive - Caldera's core functionality is preserved. The theme:
- Doesn't modify JavaScript behavior
- Doesn't change API endpoints
- Only enhances visual appearance
- Falls back gracefully if disabled

## Troubleshooting

### Theme Not Applying

1. **Check plugin loaded:**
```bash
# Look for branding plugin in logs
grep -i "branding plugin" caldera.log
```

2. **Clear browser cache:** Ctrl+Shift+R (hard refresh)

3. **Verify CSS file:**
```bash
curl http://localhost:8888/plugin/branding/static/css/triskele_theme.css
# Should return CSS content
```

### Configuration Not Saving

1. **Check file permissions:**
```bash
ls -la plugins/branding/branding_config.yml
# Should be writable by Caldera process
```

2. **Check logs for errors:**
```bash
tail -f logs/caldera.log | grep branding
```

### Custom Login Page Not Showing

The custom login template requires manual integration. To use:

1. Backup original: `cp templates/login.html templates/login.html.backup`
2. Replace with custom: `cp plugins/branding/templates/login.html templates/login.html`
3. Restart Caldera

**Or** modify Caldera's auth handler to serve the custom template.

## Development

### Adding New Features

1. **Extend CSS:** Add styles to `static/css/triskele_theme.css`
2. **Update Config:** Add parameters to `branding_config.yml`
3. **Update Admin UI:** Add controls to `templates/branding_admin.html`
4. **Update API:** Extend `hook.py` handlers

### Testing

Test theme across all Caldera pages:
- Login page
- Dashboard/Operations
- Agents page
- Adversaries page
- Abilities page
- Sources page
- Admin settings

Check responsive design at:
- Desktop (1920px+)
- Laptop (1366px)
- Tablet (768px)
- Mobile (375px)

## Support

For issues or customization help:
- Review this README
- Check Caldera logs: `logs/caldera.log`
- Verify configuration: `/plugin/branding/api/config`
- Reset to defaults: Click "Reset to Default" in admin UI

## Version History

- **v1.0.0** (2025-12-14): Initial release with Triskele Labs theme
  - Complete color palette
  - Typography system
  - Component library
  - Admin UI
  - Configuration API
  - Custom login template

## License

Part of MITRE Caldera. See main Caldera LICENSE file.

---

**Triskele Labs** | Advanced Cybersecurity Services
