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
