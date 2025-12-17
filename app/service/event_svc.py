import asyncio
import json
import websockets

from datetime import datetime, timezone

from app.service.interfaces.i_event_svc import EventServiceInterface
from app.utility.base_service import BaseService


class EventService(EventServiceInterface, BaseService):
    """Event-driven messaging service for CALDERA internal communications.
    
    Provides a WebSocket-based publish/subscribe event system for real-time
    notifications and inter-service communication. The event service enables
    decoupled, asynchronous messaging using exchange/queue routing patterns
    similar to message brokers like RabbitMQ.
    
    Key capabilities:
        - Fire events to specific exchange/queue combinations
        - Register callbacks for specific event types
        - Global event listeners for monitoring all events
        - WebSocket-based delivery for real-time updates
        - Automatic timestamping and metadata injection
    
    Common event exchanges:
        - 'agent': Agent lifecycle events (added, removed, heartbeat)
        - 'link': Link execution events (started, completed, failed)
        - 'operation': Operation state changes (created, finished, paused)
        - 'planner': Planner events (bucket transitions, stopping conditions)
        - 'caldera': General system events
    
    Attributes:
        log: Logger instance for this service
        contact_svc: Reference to contact service for WebSocket access
        ws_uri: WebSocket URI for event delivery
        global_listeners: List of callbacks invoked for all events
        default_exchange: Default exchange name ('caldera')
        default_queue: Default queue name ('general')
    
    Examples:
        >>> event_svc = EventService()
        >>> await event_svc.fire_event(exchange='agent', queue='added', paw='abc123')
        >>> await event_svc.observe_event(my_callback, exchange='link', queue='completed')
    """

    def __init__(self):
        """Initialize event service with WebSocket configuration."""
        self.log = self.add_service('event_svc', self)
        self.contact_svc = self.get_service('contact_svc')
        self.ws_uri = 'ws://{}'.format(self.get_config('app.contact.websocket'))
        self.global_listeners = []
        self.default_exchange = 'caldera'
        self.default_queue = 'general'

    async def observe_event(self, callback, exchange=None, queue=None):
        """
        Register a callback for a certain event. Callback is fired when
        an event of that type is observed.

        :param callback: Callback function
        :type callback: function
        :param exchange: event exchange
        :type exchange: str
        :param queue: event queue
        :type queue: str
        """
        exchange = exchange or self.default_exchange
        queue = queue or self.default_queue
        path = '/'.join([exchange, queue])
        handle = _Handle(path, callback)
        ws_contact = await self.contact_svc.get_contact('websocket')
        ws_contact.handler.handles.append(handle)

    async def register_global_event_listener(self, callback):
        """
        Register a global event listener that is fired when any event
        is fired.

        :param callback: Callback function
        :type callback: function
        """
        self.global_listeners.append(callback)

    async def notify_global_event_listeners(self, event, **callback_kwargs):
        """
        Notify all registered global event listeners when an event is fired.

        :param event: Event string (i.e. '<exchange>/<queue>')
        :type event: str
        """
        for c in self.global_listeners:
            try:
                c(event, **callback_kwargs)
            except Exception as e:
                self.log.error("Global callback error: {}".format(e), exc_info=True)

    async def handle_exceptions(self, awaitable):
        """Gracefully handle WebSocket exceptions during event delivery.
        
        Wraps async WebSocket operations to catch and log errors without
        propagating them, ensuring event delivery failures don't crash
        the event loop or interrupt other operations.
        
        Args:
            awaitable: Async operation to execute with exception handling
        
        Returns:
            Result of awaitable if successful, None if exception occurred
        
        Note:
            ConnectionClosedOK exceptions are silently ignored as they indicate
            no handler was registered for the event (expected condition).
        """
        try:
            return await awaitable
        except websockets.exceptions.ConnectionClosedOK:
            pass  # No handler was registered for this event
        except Exception as e:
            self.log.error("WebSocket error: {}".format(e), exc_info=True)

    async def fire_event(self, exchange=None, queue=None, timestamp=True, **callback_kwargs):
        """Fire an event to registered listeners via WebSocket.
        
        Publishes an event to the specified exchange/queue, notifying all
        registered callbacks and global listeners. Events are delivered
        asynchronously via WebSocket with optional automatic timestamping.
        
        Args:
            exchange: Event exchange name (e.g., 'agent', 'link', 'operation').
                Defaults to 'caldera' if not specified.
            queue: Event queue name (e.g., 'added', 'completed', 'failed').
                Defaults to 'general' if not specified.
            timestamp: If True, automatically add UTC timestamp to event metadata.
                Defaults to True.
            **callback_kwargs: Arbitrary event data passed to all listeners as kwargs.
        
        Examples:
            >>> await event_svc.fire_event(
            ...     exchange='agent',
            ...     queue='added',
            ...     paw='abc123',
            ...     platform='linux'
            ... )
        """
        exchange = exchange or self.default_exchange
        queue = queue or self.default_queue
        metadata = {}
        if timestamp:
            metadata.update(dict(timestamp=datetime.now(timezone.utc).timestamp()))
        callback_kwargs.update(dict(metadata=metadata))
        uri = '/'.join([self.ws_uri, exchange, queue])
        if self.global_listeners:
            asyncio.get_event_loop().create_task(self.notify_global_event_listeners('/'.join([exchange, queue]),
                                                                                    **callback_kwargs))
        d = json.dumps(callback_kwargs)
        async with websockets.connect(uri) as websocket:
            asyncio.get_event_loop().create_task(self.handle_exceptions(websocket.send(d)))
            await asyncio.sleep(0)  # yield control to event loop


class _Handle:

    def __init__(self, tag, callback):
        self.tag = tag
        self.callback = callback

    async def run(self, socket, path, services):
        return await self.callback(socket, path, services)
