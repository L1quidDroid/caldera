"""
Webhook Event Publisher

Publishes Caldera events to external webhooks (SIEM, Slack, N8N, custom endpoints).
Listens to Caldera event service and sends HTTP notifications.
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from collections import deque

import aiohttp

from app.utility.base_service import BaseService


class WebhookPublisher(BaseService):
    """
    Publishes Caldera events to external webhooks.
    
    Integrates with EventService to listen for operation lifecycle events
    and forwards them to configured webhook endpoints with retry logic.
    """

    def __init__(self):
        self.log = logging.getLogger('webhook_publisher')
        self.webhooks: List[Dict[str, Any]] = []
        self.event_queue = deque(maxlen=1000)
        self.session: Optional[aiohttp.ClientSession] = None
        self.running = False
        self.retry_config = {
            'max_retries': 3,
            'retry_delay': 5,
            'timeout': 30
        }

    async def start(self):
        """Start the webhook publisher."""
        self.running = True
        self.session = aiohttp.ClientSession()
        self.log.info("Webhook publisher started")

    async def stop(self):
        """Stop the webhook publisher and close connections."""
        self.running = False
        if self.session and not self.session.closed:
            await self.session.close()
        self.log.info("Webhook publisher stopped")

    def register_webhook(
        self,
        url: str,
        name: str = None,
        headers: Dict[str, str] = None,
        filters: Dict[str, List[str]] = None,
        enabled: bool = True
    ):
        """
        Register a webhook endpoint.
        
        Args:
            url: Webhook URL
            name: Friendly name for the webhook
            headers: Custom HTTP headers (e.g., Authorization)
            filters: Event filters {'exchange': ['operation'], 'queue': ['completed', 'started']}
            enabled: Whether webhook is active
        """
        webhook = {
            'url': url,
            'name': name or url,
            'headers': headers or {},
            'filters': filters or {},
            'enabled': enabled,
            'stats': {
                'sent': 0,
                'failed': 0,
                'last_sent': None,
                'last_error': None
            }
        }
        self.webhooks.append(webhook)
        self.log.info(f"Registered webhook: {webhook['name']} -> {url}")

    def unregister_webhook(self, url: str):
        """Remove a webhook by URL."""
        self.webhooks = [w for w in self.webhooks if w['url'] != url]
        self.log.info(f"Unregistered webhook: {url}")

    def _should_send(self, webhook: Dict, exchange: str, queue: str) -> bool:
        """Check if event matches webhook filters."""
        if not webhook['enabled']:
            return False
        
        filters = webhook['filters']
        if not filters:
            return True
        
        # Check exchange filter
        if 'exchange' in filters:
            if exchange not in filters['exchange']:
                return False
        
        # Check queue filter
        if 'queue' in filters:
            if queue not in filters['queue']:
                return False
        
        return True

    async def _send_webhook(
        self,
        webhook: Dict,
        payload: Dict,
        retry_count: int = 0
    ) -> bool:
        """
        Send event to webhook with retry logic.
        
        Returns:
            True if successful, False otherwise
        """
        if not self.session or self.session.closed:
            self.log.error("Session not available")
            return False
        
        headers = {
            'Content-Type': 'application/json',
            'User-Agent': 'Caldera-Webhook-Publisher/1.0',
            **webhook['headers']
        }
        
        try:
            async with self.session.post(
                webhook['url'],
                json=payload,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=self.retry_config['timeout'])
            ) as resp:
                if resp.status >= 200 and resp.status < 300:
                    webhook['stats']['sent'] += 1
                    webhook['stats']['last_sent'] = datetime.utcnow().isoformat()
                    self.log.debug(f"Webhook sent successfully: {webhook['name']} (status={resp.status})")
                    return True
                else:
                    error_text = await resp.text()
                    raise Exception(f"HTTP {resp.status}: {error_text[:200]}")
        
        except asyncio.TimeoutError:
            error_msg = f"Timeout after {self.retry_config['timeout']}s"
            self.log.warning(f"Webhook timeout: {webhook['name']} - {error_msg}")
            
            # Retry logic
            if retry_count < self.retry_config['max_retries']:
                await asyncio.sleep(self.retry_config['retry_delay'])
                return await self._send_webhook(webhook, payload, retry_count + 1)
            else:
                webhook['stats']['failed'] += 1
                webhook['stats']['last_error'] = error_msg
                return False
        
        except Exception as e:
            error_msg = str(e)
            self.log.error(f"Webhook error: {webhook['name']} - {error_msg}")
            
            # Retry for network errors
            if retry_count < self.retry_config['max_retries'] and isinstance(e, (aiohttp.ClientError, OSError)):
                await asyncio.sleep(self.retry_config['retry_delay'])
                return await self._send_webhook(webhook, payload, retry_count + 1)
            else:
                webhook['stats']['failed'] += 1
                webhook['stats']['last_error'] = error_msg
                return False

    async def publish_event(
        self,
        exchange: str,
        queue: str,
        data: Dict,
        campaign_id: Optional[str] = None,
        test_run_id: Optional[str] = None
    ):
        """
        Publish event to all matching webhooks.
        
        Args:
            exchange: Event exchange (e.g., 'operation', 'agent', 'system')
            queue: Event queue (e.g., 'completed', 'started', 'state_changed')
            data: Event data payload
            campaign_id: Associated campaign ID (for tagging)
            test_run_id: Test run identifier (for SIEM correlation)
        """
        timestamp = datetime.utcnow().isoformat() + 'Z'
        
        payload = {
            'source': 'caldera',
            'version': '1.0',
            'timestamp': timestamp,
            'event': {
                'exchange': exchange,
                'queue': queue,
                'data': data
            },
            'metadata': {
                'campaign_id': campaign_id,
                'test_run_id': test_run_id,
                'caldera_test': True
            }
        }
        
        # Send to matching webhooks
        tasks = []
        for webhook in self.webhooks:
            if self._should_send(webhook, exchange, queue):
                tasks.append(self._send_webhook(webhook, payload))
        
        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            success_count = sum(1 for r in results if r is True)
            self.log.debug(f"Published {exchange}/{queue} to {success_count}/{len(tasks)} webhooks")

    async def event_listener(self, services):
        """
        Event listener for Caldera EventService.
        
        Register this with EventService to listen for all events:
        await event_svc.observe_event(webhook_publisher.event_listener)
        """
        event_svc = services.get('event_svc')
        
        async def handle_event(websocket, path):
            async for message in websocket:
                try:
                    event_data = json.loads(message)
                    exchange = event_data.get('exchange', 'unknown')
                    queue = event_data.get('queue', 'unknown')
                    data = event_data.get('data', {})
                    
                    # Extract campaign metadata if available
                    campaign_id = data.get('campaign_id')
                    test_run_id = data.get('test_run_id')
                    
                    await self.publish_event(exchange, queue, data, campaign_id, test_run_id)
                
                except json.JSONDecodeError:
                    self.log.error(f"Invalid JSON in event: {message}")
                except Exception as e:
                    self.log.error(f"Error handling event: {e}")
        
        return handle_event

    def get_stats(self) -> Dict[str, Any]:
        """Get webhook statistics."""
        return {
            'webhooks': [
                {
                    'name': w['name'],
                    'url': w['url'],
                    'enabled': w['enabled'],
                    'stats': w['stats']
                }
                for w in self.webhooks
            ],
            'queue_size': len(self.event_queue)
        }


class SIEMIntegration:
    """
    SIEM-specific integration for Elastic, Splunk, etc.
    
    Provides specialized formatting and tagging for SIEM platforms.
    """

    def __init__(self, siem_type: str, endpoint: str, api_key: str, index_name: str = None):
        self.siem_type = siem_type.lower()
        self.endpoint = endpoint.rstrip('/')
        self.api_key = api_key
        self.index_name = index_name or 'caldera-events'
        self.log = logging.getLogger(f'siem_{self.siem_type}')
        self.session: Optional[aiohttp.ClientSession] = None

    async def start(self):
        """Initialize SIEM connection."""
        self.session = aiohttp.ClientSession()
        self.log.info(f"SIEM integration started: {self.siem_type}")

    async def stop(self):
        """Close SIEM connection."""
        if self.session and not self.session.closed:
            await self.session.close()

    def _format_elastic_event(self, event_data: Dict) -> Dict:
        """Format event for Elasticsearch."""
        return {
            '@timestamp': event_data['timestamp'],
            'source': 'caldera',
            'event': {
                'kind': 'event',
                'category': ['security'],
                'type': [event_data['event']['queue']],
                'action': f"{event_data['event']['exchange']}.{event_data['event']['queue']}",
                'dataset': 'caldera.operations'
            },
            'caldera': {
                'exchange': event_data['event']['exchange'],
                'queue': event_data['event']['queue'],
                'campaign_id': event_data['metadata'].get('campaign_id'),
                'test_run_id': event_data['metadata'].get('test_run_id'),
                'data': event_data['event']['data']
            },
            'tags': ['caldera', 'purple-team', 'adversary-emulation']
        }

    def _format_splunk_event(self, event_data: Dict) -> Dict:
        """Format event for Splunk HEC."""
        return {
            'time': datetime.fromisoformat(event_data['timestamp'].replace('Z', '+00:00')).timestamp(),
            'sourcetype': 'caldera:events',
            'source': 'caldera',
            'index': self.index_name,
            'event': {
                'caldera_exchange': event_data['event']['exchange'],
                'caldera_queue': event_data['event']['queue'],
                'campaign_id': event_data['metadata'].get('campaign_id'),
                'test_run_id': event_data['metadata'].get('test_run_id'),
                'caldera_test': True,
                **event_data['event']['data']
            }
        }

    async def send_event(self, event_data: Dict) -> bool:
        """Send event to SIEM with platform-specific formatting."""
        if not self.session or self.session.closed:
            return False

        try:
            if self.siem_type == 'elastic':
                url = f"{self.endpoint}/{self.index_name}/_doc"
                headers = {
                    'Authorization': f'ApiKey {self.api_key}',
                    'Content-Type': 'application/json'
                }
                payload = self._format_elastic_event(event_data)
            
            elif self.siem_type == 'splunk':
                url = f"{self.endpoint}/services/collector/event"
                headers = {
                    'Authorization': f'Splunk {self.api_key}',
                    'Content-Type': 'application/json'
                }
                payload = self._format_splunk_event(event_data)
            
            else:
                self.log.error(f"Unsupported SIEM type: {self.siem_type}")
                return False

            async with self.session.post(url, json=payload, headers=headers, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                if resp.status >= 200 and resp.status < 300:
                    self.log.debug(f"SIEM event sent: {self.siem_type}")
                    return True
                else:
                    error_text = await resp.text()
                    self.log.error(f"SIEM error: {resp.status} - {error_text[:200]}")
                    return False

        except Exception as e:
            self.log.error(f"SIEM send error: {e}")
            return False


# =============================================================================
# CONSOLIDATED WORKFLOW SERVICE (Replaces n8n for B1s optimization)
# =============================================================================

class ConsolidatedWorkflowService:
    """
    Unified workflow service that replaces n8n for B1s memory optimization.
    
    Handles the complete purple team automation pipeline:
    1. Caldera operation completion → 
    2. Tag ELK alerts with ATT&CK IDs →
    3. Slack/Teams notification →
    4. Generate ATT&CK coverage report →
    5. Export PDF →
    6. Publish to GitHub Pages
    
    Memory savings: ~100MB by eliminating n8n container
    """

    def __init__(
        self,
        caldera_url: str,
        caldera_api_key: str,
        elastic_endpoint: str = None,
        elastic_password: str = None,
        slack_webhook_url: str = None,
        github_token: str = None,
        github_repo: str = None,
        reports_dir: str = './reports'
    ):
        self.log = logging.getLogger('consolidated_workflow')
        self.caldera_url = caldera_url.rstrip('/')
        self.caldera_api_key = caldera_api_key
        self.elastic_endpoint = elastic_endpoint
        self.elastic_password = elastic_password
        self.slack_webhook_url = slack_webhook_url
        self.github_token = github_token
        self.github_repo = github_repo
        self.reports_dir = Path(reports_dir)
        self.reports_dir.mkdir(parents=True, exist_ok=True)
        
        self.session: Optional[aiohttp.ClientSession] = None
        self.webhook_publisher = WebhookPublisher()
        
        # SIEM integration (if configured)
        self.siem: Optional[SIEMIntegration] = None
        if elastic_endpoint and elastic_password:
            # Use basic auth for local Elasticsearch
            self.siem = SIEMIntegration(
                siem_type='elastic',
                endpoint=elastic_endpoint,
                api_key=elastic_password,  # Will be used as password for basic auth
                index_name='caldera-events'
            )

    async def start(self):
        """Initialize the workflow service."""
        self.session = aiohttp.ClientSession()
        await self.webhook_publisher.start()
        if self.siem:
            await self.siem.start()
        self.log.info("Consolidated workflow service started")

    async def stop(self):
        """Clean up resources."""
        if self.session and not self.session.closed:
            await self.session.close()
        await self.webhook_publisher.stop()
        if self.siem:
            await self.siem.stop()
        self.log.info("Consolidated workflow service stopped")

    async def get_operation_results(self, operation_id: str) -> Dict[str, Any]:
        """Fetch operation results from Caldera API."""
        headers = {
            'KEY': self.caldera_api_key,
            'Content-Type': 'application/json'
        }
        
        try:
            async with self.session.get(
                f"{self.caldera_url}/api/v2/operations/{operation_id}",
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as resp:
                if resp.status == 200:
                    return await resp.json()
                else:
                    self.log.error(f"Failed to get operation: {resp.status}")
                    return {}
        except Exception as e:
            self.log.error(f"Error fetching operation: {e}")
            return {}

    async def get_operation_links(self, operation_id: str) -> List[Dict]:
        """Fetch operation links (executed abilities) from Caldera."""
        headers = {
            'KEY': self.caldera_api_key,
            'Content-Type': 'application/json'
        }
        
        try:
            async with self.session.get(
                f"{self.caldera_url}/api/v2/operations/{operation_id}/links",
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as resp:
                if resp.status == 200:
                    return await resp.json()
                return []
        except Exception as e:
            self.log.error(f"Error fetching links: {e}")
            return []

    def extract_attck_techniques(self, links: List[Dict]) -> List[Dict[str, str]]:
        """Extract ATT&CK technique IDs from operation links."""
        techniques = []
        for link in links:
            ability = link.get('ability', {})
            technique_id = ability.get('technique_id', '')
            technique_name = ability.get('technique_name', '')
            tactic = ability.get('tactic', '')
            
            if technique_id:
                techniques.append({
                    'technique_id': technique_id,
                    'technique_name': technique_name,
                    'tactic': tactic,
                    'status': link.get('status', 0),
                    'paw': link.get('paw', ''),
                    'ability_id': ability.get('ability_id', '')
                })
        return techniques

    async def tag_elk_alerts(
        self,
        operation_id: str,
        techniques: List[Dict[str, str]],
        campaign_id: str = None
    ) -> bool:
        """
        Tag related alerts in Elasticsearch with ATT&CK technique IDs.
        
        Creates correlation between Caldera operations and SIEM detections.
        """
        if not self.elastic_endpoint:
            self.log.warning("Elasticsearch not configured, skipping ELK tagging")
            return False
        
        timestamp = datetime.utcnow().isoformat() + 'Z'
        
        # Create enrichment document for correlation
        enrichment_doc = {
            '@timestamp': timestamp,
            'event': {
                'kind': 'enrichment',
                'category': ['threat'],
                'type': ['indicator'],
                'action': 'caldera.operation.complete'
            },
            'caldera': {
                'operation_id': operation_id,
                'campaign_id': campaign_id,
                'techniques': techniques,
                'technique_ids': [t['technique_id'] for t in techniques],
                'tactics': list(set(t['tactic'] for t in techniques if t['tactic']))
            },
            'threat': {
                'framework': 'MITRE ATT&CK',
                'technique': {
                    'id': [t['technique_id'] for t in techniques],
                    'name': [t['technique_name'] for t in techniques]
                }
            },
            'tags': ['caldera', 'purple-team', 'operation-complete', 'caldera_test']
        }
        
        if self.siem:
            # Format as standard event for SIEM integration
            event_data = {
                'timestamp': timestamp,
                'event': {
                    'exchange': 'operation',
                    'queue': 'completed',
                    'data': enrichment_doc
                },
                'metadata': {
                    'campaign_id': campaign_id,
                    'test_run_id': operation_id,
                    'caldera_test': True
                }
            }
            return await self.siem.send_event(event_data)
        
        return False

    async def send_slack_notification(
        self,
        operation_id: str,
        operation_name: str,
        techniques: List[Dict[str, str]],
        summary: Dict[str, Any]
    ) -> bool:
        """
        Send formatted Slack notification with operation results.
        
        Uses Slack Block Kit for rich formatting.
        """
        if not self.slack_webhook_url:
            self.log.warning("Slack webhook not configured, skipping notification")
            return False
        
        # Calculate stats
        total_techniques = len(techniques)
        successful = sum(1 for t in techniques if t.get('status', -1) == 0)
        failed = total_techniques - successful
        
        # Build Slack blocks
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "🎯 Caldera Operation Complete",
                    "emoji": True
                }
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*Operation:*\n{operation_name}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*ID:*\n`{operation_id[:8]}...`"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Techniques:*\n{total_techniques} total"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Status:*\n✅ {successful} | ❌ {failed}"
                    }
                ]
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*ATT&CK Coverage:*\n" + ", ".join(
                        [f"`{t['technique_id']}`" for t in techniques[:10]]
                    ) + (f" (+{total_techniques - 10} more)" if total_techniques > 10 else "")
                }
            },
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": f"🕐 Completed at {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}"
                    }
                ]
            }
        ]
        
        payload = {
            "blocks": blocks,
            "text": f"Caldera operation {operation_name} completed with {total_techniques} techniques"
        }
        
        try:
            async with self.session.post(
                self.slack_webhook_url,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=10)
            ) as resp:
                if resp.status == 200:
                    self.log.info("Slack notification sent successfully")
                    return True
                else:
                    self.log.error(f"Slack notification failed: {resp.status}")
                    return False
        except Exception as e:
            self.log.error(f"Slack notification error: {e}")
            return False

    async def generate_coverage_report(
        self,
        operation_id: str,
        techniques: List[Dict[str, str]],
        output_format: str = 'json'
    ) -> Dict[str, Any]:
        """
        Generate ATT&CK coverage report from operation results.
        
        Returns:
            Dictionary with coverage metrics and technique details
        """
        # Group by tactic
        tactics = {}
        for t in techniques:
            tactic = t.get('tactic', 'unknown')
            if tactic not in tactics:
                tactics[tactic] = []
            tactics[tactic].append(t)
        
        # Calculate coverage metrics
        total = len(techniques)
        successful = sum(1 for t in techniques if t.get('status', -1) == 0)
        
        report = {
            'operation_id': operation_id,
            'generated_at': datetime.utcnow().isoformat() + 'Z',
            'summary': {
                'total_techniques': total,
                'successful': successful,
                'failed': total - successful,
                'success_rate': (successful / total * 100) if total > 0 else 0,
                'unique_tactics': len(tactics)
            },
            'tactics': {
                tactic: {
                    'count': len(techs),
                    'techniques': [
                        {
                            'id': t['technique_id'],
                            'name': t['technique_name'],
                            'status': 'success' if t.get('status', -1) == 0 else 'failed'
                        }
                        for t in techs
                    ]
                }
                for tactic, techs in tactics.items()
            },
            'technique_ids': [t['technique_id'] for t in techniques],
            'framework': 'MITRE ATT&CK'
        }
        
        # Save JSON report
        json_path = self.reports_dir / f"coverage_{operation_id[:8]}.json"
        with open(json_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        self.log.info(f"Coverage report saved: {json_path}")
        return report

    async def export_pdf_report(self, campaign_id: str) -> Optional[str]:
        """
        Generate PDF report using existing PDFReportGenerator.
        
        Returns:
            Path to generated PDF, or None if failed
        """
        try:
            # Import here to avoid circular imports
            from orchestrator.pdf_generator import PDFReportGenerator
            
            generator = PDFReportGenerator(
                caldera_url=self.caldera_url,
                api_key=self.caldera_api_key
            )
            
            timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
            output_path = self.reports_dir / f"report_{campaign_id[:8]}_{timestamp}.pdf"
            
            result = await generator.generate_report(
                campaign_id=campaign_id,
                output_path=str(output_path),
                include_output=False,
                include_facts=True,
                attack_layer=True
            )
            
            self.log.info(f"PDF report generated: {output_path}")
            return str(output_path)
            
        except ImportError as e:
            self.log.warning(f"PDF generation not available: {e}")
            return None
        except Exception as e:
            self.log.error(f"PDF generation failed: {e}")
            return None

    async def publish_to_github_pages(
        self,
        report_path: str,
        commit_message: str = None
    ) -> bool:
        """
        Publish report to GitHub Pages via GitHub API.
        
        Commits report to gh-pages branch for static hosting.
        """
        if not self.github_token or not self.github_repo:
            self.log.warning("GitHub not configured, skipping publish")
            return False
        
        import base64
        
        report_file = Path(report_path)
        if not report_file.exists():
            self.log.error(f"Report file not found: {report_path}")
            return False
        
        # Read file content
        with open(report_file, 'rb') as f:
            content = base64.b64encode(f.read()).decode('utf-8')
        
        filename = report_file.name
        commit_message = commit_message or f"Add report: {filename}"
        
        # GitHub API endpoint
        api_url = f"https://api.github.com/repos/{self.github_repo}/contents/reports/{filename}"
        
        headers = {
            'Authorization': f'token {self.github_token}',
            'Accept': 'application/vnd.github.v3+json',
            'Content-Type': 'application/json'
        }
        
        payload = {
            'message': commit_message,
            'content': content,
            'branch': 'gh-pages'
        }
        
        try:
            async with self.session.put(
                api_url,
                json=payload,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as resp:
                if resp.status in (200, 201):
                    self.log.info(f"Report published to GitHub Pages: {filename}")
                    return True
                else:
                    error = await resp.text()
                    self.log.error(f"GitHub publish failed: {resp.status} - {error[:200]}")
                    return False
        except Exception as e:
            self.log.error(f"GitHub publish error: {e}")
            return False

    async def on_operation_complete(
        self,
        operation_id: str,
        campaign_id: str = None
    ) -> Dict[str, Any]:
        """
        Main workflow handler: triggered when Caldera operation completes.
        
        Orchestrates the full purple team automation pipeline:
        1. Fetch operation results from Caldera
        2. Extract ATT&CK techniques
        3. Tag related ELK alerts
        4. Send Slack notification
        5. Generate coverage report (JSON)
        6. Export PDF report
        7. Publish to GitHub Pages
        
        Returns:
            Workflow execution summary
        """
        self.log.info(f"Processing operation complete: {operation_id}")
        results = {
            'operation_id': operation_id,
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'steps': {}
        }
        
        # Step 1: Fetch operation results
        operation = await self.get_operation_results(operation_id)
        if not operation:
            results['error'] = 'Failed to fetch operation'
            return results
        
        operation_name = operation.get('name', 'Unknown')
        results['operation_name'] = operation_name
        
        # Step 2: Get links and extract techniques
        links = await self.get_operation_links(operation_id)
        techniques = self.extract_attck_techniques(links)
        results['techniques_count'] = len(techniques)
        
        # Step 3: Tag ELK alerts
        elk_result = await self.tag_elk_alerts(operation_id, techniques, campaign_id)
        results['steps']['elk_tagging'] = 'success' if elk_result else 'skipped'
        
        # Step 4: Slack notification
        slack_result = await self.send_slack_notification(
            operation_id, operation_name, techniques, results
        )
        results['steps']['slack_notification'] = 'success' if slack_result else 'skipped'
        
        # Step 5: Generate coverage report
        coverage = await self.generate_coverage_report(operation_id, techniques)
        results['steps']['coverage_report'] = 'success'
        results['coverage_summary'] = coverage.get('summary', {})
        
        # Step 6: Export PDF (if campaign_id provided)
        if campaign_id:
            pdf_path = await self.export_pdf_report(campaign_id)
            results['steps']['pdf_export'] = 'success' if pdf_path else 'skipped'
            results['pdf_path'] = pdf_path
            
            # Step 7: Publish to GitHub Pages
            if pdf_path:
                gh_result = await self.publish_to_github_pages(pdf_path)
                results['steps']['github_pages'] = 'success' if gh_result else 'skipped'
        
        self.log.info(f"Workflow complete for operation {operation_id}")
        return results


# =============================================================================
# FLASK APP FOR WEBHOOK ENDPOINT
# =============================================================================

from pathlib import Path

def create_webhook_app():
    """
    Create Flask app for receiving Caldera webhooks.
    
    Endpoints:
        POST /webhook/caldera-complete - Handle operation completion
        GET /health - Health check
        GET /stats - Webhook statistics
    """
    try:
        from flask import Flask, request, jsonify
    except ImportError:
        print("Flask not available. Install with: pip install flask")
        return None
    
    import os
    
    app = Flask(__name__)
    
    # Initialize workflow service from environment
    workflow_service = ConsolidatedWorkflowService(
        caldera_url=os.getenv('CALDERA_URL', 'http://localhost:8888'),
        caldera_api_key=os.getenv('CALDERA_API_KEY', ''),
        elastic_endpoint=os.getenv('ELASTIC_ENDPOINT'),
        elastic_password=os.getenv('ELASTIC_PASSWORD'),
        slack_webhook_url=os.getenv('SLACK_WEBHOOK_URL'),
        github_token=os.getenv('GITHUB_TOKEN'),
        github_repo=os.getenv('GITHUB_REPO'),
        reports_dir=os.getenv('REPORTS_DIR', './reports')
    )
    
    @app.before_request
    def ensure_started():
        if not hasattr(app, '_workflow_started'):
            asyncio.get_event_loop().run_until_complete(workflow_service.start())
            app._workflow_started = True
    
    @app.route('/health', methods=['GET'])
    def health():
        return jsonify({'status': 'ok', 'service': 'webhook-service'})
    
    @app.route('/stats', methods=['GET'])
    def stats():
        return jsonify(workflow_service.webhook_publisher.get_stats())
    
    @app.route('/webhook/caldera-complete', methods=['POST'])
    def handle_caldera_complete():
        """
        Handle Caldera operation completion webhook.
        
        Expected payload:
        {
            "operation_id": "abc123",
            "campaign_id": "campaign123",  # optional
            "event": "operation.complete"
        }
        """
        data = request.get_json() or {}
        operation_id = data.get('operation_id')
        campaign_id = data.get('campaign_id')
        
        if not operation_id:
            return jsonify({'error': 'operation_id required'}), 400
        
        # Run async workflow
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(
                workflow_service.on_operation_complete(operation_id, campaign_id)
            )
            return jsonify(result)
        except Exception as e:
            return jsonify({'error': str(e)}), 500
        finally:
            loop.close()
    
    @app.route('/webhook/test', methods=['POST'])
    def test_webhook():
        """Test endpoint to verify webhook connectivity."""
        return jsonify({
            'status': 'received',
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'payload': request.get_json()
        })
    
    return app


# Run standalone webhook server
if __name__ == '__main__':
    app = create_webhook_app()
    if app:
        print("Starting webhook service on http://0.0.0.0:5000")
        app.run(host='0.0.0.0', port=5000, debug=False)
