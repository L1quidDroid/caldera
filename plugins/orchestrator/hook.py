"""
Orchestrator Plugin for Caldera

Integrates campaign orchestration capabilities directly into Caldera.
Provides webhook publishing, SIEM integration, and campaign management APIs.
"""

import logging

from aiohttp import web

name = 'Orchestrator'
description = 'Multi-phase campaign orchestration with webhooks and SIEM integration'
address = '/plugin/orchestrator'
access = None  # Available to all access levels

async def enable(services):
    """
    Enable the orchestrator plugin.
    
    Registers:
    - Webhook publisher service
    - Campaign management API endpoints
    - Event listeners for operation lifecycle
    """
    log = logging.getLogger('orchestrator_plugin')
    app = services.get('app_svc').application
    
    # Import orchestrator components
    import sys
    from pathlib import Path
    orchestrator_path = Path(__file__).parent.parent.parent / 'orchestrator'
    if str(orchestrator_path) not in sys.path:
        sys.path.insert(0, str(orchestrator_path))
    
    from webhook_publisher import WebhookPublisher, SIEMIntegration
    
    # Initialize webhook publisher
    webhook_publisher = WebhookPublisher()
    await webhook_publisher.start()
    services['webhook_publisher'] = webhook_publisher
    
    # Register with event service for automatic event forwarding
    event_svc = services.get('event_svc')
    if event_svc:
        log.info("Registering webhook publisher with event service")
        # Note: Event service integration would need additional implementation
        # to automatically forward events. For now, campaigns can manually publish.
    
    # Create orchestrator service
    orchestrator_svc = OrchestratorService(services, webhook_publisher)
    
    # Register API routes
    app.router.add_route('GET', '/plugin/orchestrator', orchestrator_svc.splash)
    app.router.add_route('GET', '/plugin/orchestrator/webhooks', orchestrator_svc.list_webhooks)
    app.router.add_route('POST', '/plugin/orchestrator/webhooks', orchestrator_svc.register_webhook)
    app.router.add_route('DELETE', '/plugin/orchestrator/webhooks/{url}', orchestrator_svc.unregister_webhook)
    app.router.add_route('GET', '/plugin/orchestrator/campaigns', orchestrator_svc.list_campaigns)
    app.router.add_route('GET', '/plugin/orchestrator/campaigns/{campaign_id}', orchestrator_svc.get_campaign)
    app.router.add_route('POST', '/plugin/orchestrator/campaigns/{campaign_id}/notify', orchestrator_svc.notify_campaign_event)
    
    # Static files
    app.router.add_static('/orchestrator', 'plugins/orchestrator/static', append_version=True)
    
    log.info(f"Orchestrator plugin enabled at {address}")


class OrchestratorService:
    """Service for orchestrator plugin endpoints."""

    def __init__(self, services, webhook_publisher):
        self.services = services
        self.webhook_publisher = webhook_publisher
        self.data_svc = services.get('data_svc')
        self.auth_svc = services.get('auth_svc')
        self.log = logging.getLogger('orchestrator_service')

    async def splash(self, request):
        """Main plugin page."""
        html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Caldera Orchestrator</title>
            <style>
                body {
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    max-width: 1200px;
                    margin: 40px auto;
                    padding: 20px;
                    background: #f5f5f5;
                }
                .container {
                    background: white;
                    padding: 30px;
                    border-radius: 8px;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                }
                h1 {
                    color: #2c3e50;
                    border-bottom: 3px solid #3498db;
                    padding-bottom: 10px;
                }
                .section {
                    margin: 20px 0;
                }
                .webhook-list {
                    list-style: none;
                    padding: 0;
                }
                .webhook-item {
                    background: #ecf0f1;
                    padding: 15px;
                    margin: 10px 0;
                    border-radius: 5px;
                }
                .stats {
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                    gap: 15px;
                    margin: 20px 0;
                }
                .stat-card {
                    background: #3498db;
                    color: white;
                    padding: 20px;
                    border-radius: 5px;
                    text-align: center;
                }
                .stat-card h3 {
                    margin: 0;
                    font-size: 2em;
                }
                .stat-card p {
                    margin: 5px 0 0 0;
                }
                code {
                    background: #2c3e50;
                    color: #ecf0f1;
                    padding: 2px 6px;
                    border-radius: 3px;
                }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🎯 Caldera Campaign Orchestrator</h1>
                
                <div class="section">
                    <h2>Overview</h2>
                    <p>Multi-phase campaign orchestration with webhook publishing and SIEM integration.</p>
                </div>
                
                <div class="section">
                    <h2>Features</h2>
                    <ul>
                        <li>📋 Campaign specification management</li>
                        <li>🔗 Webhook event publishing</li>
                        <li>📊 SIEM integration (Elastic, Splunk)</li>
                        <li>🔔 Slack/N8N notifications</li>
                        <li>📈 Campaign state tracking</li>
                        <li>🛡️ Governance and approval workflows</li>
                    </ul>
                </div>
                
                <div class="section">
                    <h2>CLI Usage</h2>
                    <p>Use the orchestrator CLI from the command line:</p>
                    <pre><code>python3 orchestrator/cli.py campaign create campaign_spec.yml
python3 orchestrator/cli.py campaign start &lt;campaign_id&gt;
python3 orchestrator/cli.py campaign status &lt;campaign_id&gt;
python3 orchestrator/health_check.py --url=http://localhost:8888</code></pre>
                </div>
                
                <div class="section">
                    <h2>API Endpoints</h2>
                    <ul>
                        <li><code>GET /plugin/orchestrator/webhooks</code> - List registered webhooks</li>
                        <li><code>POST /plugin/orchestrator/webhooks</code> - Register new webhook</li>
                        <li><code>GET /plugin/orchestrator/campaigns</code> - List campaigns</li>
                        <li><code>GET /plugin/orchestrator/campaigns/{id}</code> - Get campaign details</li>
                        <li><code>POST /plugin/orchestrator/campaigns/{id}/notify</code> - Send campaign event</li>
                    </ul>
                </div>
                
                <div class="section">
                    <h2>Documentation</h2>
                    <p>See <code>orchestrator/README.md</code> for complete documentation.</p>
                </div>
            </div>
        </body>
        </html>
        """
        return web.Response(text=html, content_type='text/html')

    async def list_webhooks(self, request):
        """List registered webhooks with statistics."""
        stats = self.webhook_publisher.get_stats()
        return web.json_response(stats)

    async def register_webhook(self, request):
        """Register a new webhook endpoint."""
        try:
            data = await request.json()
            url = data.get('url')
            name = data.get('name')
            headers = data.get('headers', {})
            filters = data.get('filters', {})
            enabled = data.get('enabled', True)
            
            if not url:
                return web.json_response({'error': 'URL required'}, status=400)
            
            self.webhook_publisher.register_webhook(url, name, headers, filters, enabled)
            
            return web.json_response({
                'status': 'success',
                'message': f'Webhook registered: {name or url}'
            })
        
        except Exception as e:
            self.log.error(f"Error registering webhook: {e}")
            return web.json_response({'error': str(e)}, status=500)

    async def unregister_webhook(self, request):
        """Remove a webhook by URL."""
        url = request.match_info.get('url')
        self.webhook_publisher.unregister_webhook(url)
        return web.json_response({'status': 'success', 'message': 'Webhook removed'})

    async def list_campaigns(self, request):
        """List all campaigns from data service."""
        campaigns = await self.data_svc.locate('campaigns')
        return web.json_response([c.display for c in campaigns])

    async def get_campaign(self, request):
        """Get campaign details by ID."""
        campaign_id = request.match_info.get('campaign_id')
        campaigns = await self.data_svc.locate('campaigns', {'campaign_id': campaign_id})
        
        if not campaigns:
            return web.json_response({'error': 'Campaign not found'}, status=404)
        
        return web.json_response(campaigns[0].display)

    async def notify_campaign_event(self, request):
        """
        Manually publish a campaign event to webhooks.
        
        POST /plugin/orchestrator/campaigns/{campaign_id}/notify
        Body: {
            "exchange": "campaign",
            "queue": "started",
            "data": {...}
        }
        """
        try:
            campaign_id = request.match_info.get('campaign_id')
            data = await request.json()
            
            exchange = data.get('exchange', 'campaign')
            queue = data.get('queue', 'event')
            event_data = data.get('data', {})
            test_run_id = data.get('test_run_id')
            
            await self.webhook_publisher.publish_event(
                exchange=exchange,
                queue=queue,
                data=event_data,
                campaign_id=campaign_id,
                test_run_id=test_run_id
            )
            
            return web.json_response({
                'status': 'success',
                'message': 'Event published to webhooks'
            })
        
        except Exception as e:
            self.log.error(f"Error publishing event: {e}")
            return web.json_response({'error': str(e)}, status=500)
