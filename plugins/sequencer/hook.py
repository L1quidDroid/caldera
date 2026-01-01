"""
Sequencer Plugin for Caldera

Provides automated multi-step operation sequencing with:
- Fact chaining between operations
- Exponential backoff retry logic
- Tactic fallback on failure
- Real-time progress tracking
- Integration with orchestrator workflow services
"""

import logging
from pathlib import Path

from aiohttp import web

from app.utility.base_world import BaseWorld

name = 'Sequencer'
description = 'Automated operation sequencing with failure recovery and fact chaining'
address = '/plugin/sequencer/gui'
access = BaseWorld.Access.RED  # Red team access only


async def enable(services):
    """
    Enable the sequencer plugin.
    
    Registers:
    - Sequencer service for job tracking
    - REST API endpoints
    - Vue.js GUI components
    - Static file serving
    """
    log = logging.getLogger('sequencer_plugin')
    app = services.get('app_svc').application
    data_svc = services.get('data_svc')
    
    # Import sequencer service
    from plugins.sequencer.app.sequencer_service import SequencerService
    
    # Create sequencer service instance
    sequencer_svc = SequencerService(services)
    
    # Register service globally
    services['sequencer_svc'] = sequencer_svc
    
    # Register REST API routes
    app.router.add_route('GET', '/plugin/sequencer/api/jobs', sequencer_svc.list_jobs)
    app.router.add_route('POST', '/plugin/sequencer/api/start', sequencer_svc.start_sequence)
    app.router.add_route('GET', '/plugin/sequencer/api/status/{job_id}', sequencer_svc.get_status)
    app.router.add_route('POST', '/plugin/sequencer/api/retry/{job_id}', sequencer_svc.retry_job)
    app.router.add_route('POST', '/plugin/sequencer/api/cancel/{job_id}', sequencer_svc.cancel_job)
    app.router.add_route('GET', '/plugin/sequencer/api/sequences', sequencer_svc.list_sequences)
    
    # Serve Vue component (for Magma integration)
    plugin_root = Path(__file__).parent
    gui_path = plugin_root / 'gui'
    
    if gui_path.exists():
        # Static files for GUI
        app.router.add_static('/sequencer/gui', str(gui_path), append_version=True)
    
    # Serve static assets (if any)
    static_path = plugin_root / 'static'
    if static_path.exists():
        app.router.add_static('/sequencer', str(static_path), append_version=True)
    
    # GUI endpoint (legacy iframe support)
    app.router.add_route('GET', '/plugin/sequencer/gui', sequencer_svc.gui_view)
    
    log.info(f'Sequencer plugin enabled - API: {address}')
    log.info(f'  • Start sequence: POST /plugin/sequencer/api/start')
    log.info(f'  • Job status: GET /plugin/sequencer/api/status/<job_id>')
    log.info(f'  • List jobs: GET /plugin/sequencer/api/jobs')
