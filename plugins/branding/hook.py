"""
Branding Plugin for Caldera

Customizes Caldera's appearance with Triskele Labs branding:
- Custom color scheme (navy, cyan/teal accents)
- Typography and layout modifications
- Logo and favicon replacement
- Template overrides for login and dashboard
"""

import logging
import yaml
from pathlib import Path
from aiohttp import web

name = 'Branding'
description = 'Custom branding and theme for Caldera with Triskele Labs style'
address = '/plugin/branding'
access = None  # Available to all access levels


async def enable(services):
    """
    Enable the branding plugin.
    
    Registers:
    - Custom CSS and JavaScript files
    - Static file routes for logos and assets
    - Template overrides
    - Branding configuration API
    """
    log = logging.getLogger('branding_plugin')
    app = services.get('app_svc').application
    
    # Load branding configuration
    plugin_dir = Path(__file__).parent
    config_path = plugin_dir / 'branding_config.yml'
    
    branding_config = {
        'enabled': True,
        'theme': 'triskele_labs',
        'colors': {
            'primary_dark': '#020816',
            'primary_accent': '#00D1FF',
            'secondary_accent_start': '#0A3D91',
            'secondary_accent_end': '#0BC4D9',
            'neutral_light': '#F5F7FA',
            'text_dark': '#1F2937',
            'text_mid': '#6B7280'
        },
        'typography': {
            'font_family': '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif',
            'h1_size': '48px',
            'h2_size': '32px',
            'h3_size': '22px',
            'body_size': '16px'
        },
        'logo': {
            'header_logo': '/plugin/branding/static/img/triskele_logo.svg',
            'login_logo': '/plugin/branding/static/img/triskele_logo_large.svg',
            'favicon': '/plugin/branding/static/img/favicon.ico'
        },
        'customization': {
            'company_name': 'Triskele Labs',
            'tagline': 'Advanced Cybersecurity Services',
            'login_message': 'Secure Access to Adversary Emulation Platform'
        }
    }
    
    # Load custom config if exists
    if config_path.exists():
        with open(config_path, 'r') as f:
            custom_config = yaml.safe_load(f)
            if custom_config:
                branding_config.update(custom_config)
    
    # Store config in services
    services['branding_config'] = branding_config
    
    # Register static file routes
    static_dir = plugin_dir / 'static'
    app.router.add_static('/plugin/branding/static/', static_dir, name='branding_static')
    
    # Register API routes
    app.router.add_route('GET', '/plugin/branding/api/config', get_branding_config)
    app.router.add_route('POST', '/plugin/branding/api/config', update_branding_config)
    app.router.add_route('GET', '/plugin/branding/gui', branding_admin_gui)
    
    log.info(f"Branding plugin enabled with theme: {branding_config['theme']}")
    log.info(f"Primary colors: {branding_config['colors']['primary_dark']} / {branding_config['colors']['primary_accent']}")


async def get_branding_config(request):
    """Get current branding configuration"""
    services = request.app['services']
    branding_config = services.get('branding_config', {})
    return web.json_response(branding_config)


async def update_branding_config(request):
    """Update branding configuration"""
    services = request.app['services']
    data = await request.json()
    
    branding_config = services.get('branding_config', {})
    branding_config.update(data)
    services['branding_config'] = branding_config
    
    # Save to file
    plugin_dir = Path(__file__).parent
    config_path = plugin_dir / 'branding_config.yml'
    
    with open(config_path, 'w') as f:
        yaml.dump(branding_config, f, default_flow_style=False)
    
    return web.json_response({'status': 'updated', 'config': branding_config})


async def branding_admin_gui(request):
    """Render branding administration interface"""
    services = request.app['services']
    
    # Get template path
    plugin_dir = Path(__file__).parent
    template_path = plugin_dir / 'templates' / 'branding_admin.html'
    
    if template_path.exists():
        with open(template_path, 'r') as f:
            content = f.read()
        return web.Response(text=content, content_type='text/html')
    
    # Fallback if template doesn't exist
    return web.Response(text="""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Branding Configuration</title>
        <link rel="stylesheet" href="/gui/css/basic.css">
    </head>
    <body>
        <h1>Branding Configuration</h1>
        <p>Theme: Triskele Labs</p>
        <p>Configuration API: <code>/plugin/branding/api/config</code></p>
    </body>
    </html>
    """, content_type='text/html')
