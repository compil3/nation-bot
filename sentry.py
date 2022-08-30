import logging
import sentry_sdk
from typing import Any, Callable, Optional
from naff import Client, Extension, listen
from naff.api.events import Error

__all__ = ("setup", "default_sentry_filter")

def default_sentry_filter(event: dict[str, Any], hint: dict[str,Any]) -> Optional[dict[str, Any]]:
    if 'log_record' in hint:
        record: logging.LogRecord = hint['log_record']
        if 'naff' in record.name:
            if ': 403' in record.message:
                return None
            if record.message.startswith('Ignoring exception in '):
                return None
    
    if 'exc_info' in hint:
        exc_type, exc_value, tb = hint['exc_info']
        if isinstance(exc_value, OSError):
            return None
    return event

class Sentry(Extension):
    @listen()
    async def on_startup(self) -> None:
        sentry_sdk.set_context(
            'bot', 
            {
                'name': str(self.bot.user),
                'intents':repr(self.bot.intents),
            },
        )
        sentry_sdk.set_tag("bot_name", str(self.bot.user))

    @listen()
    async def on_error(self, event: Error) -> None:
        with sentry_sdk.configure_scope() as scope:
            scope.set_tag("source", event.source)
            if event.ctx:
                scope.set_context(
                    type(event.ctx).__name__,
                    {
                        "args": event.ctx.args,
                        "kwargs" : event.ctx.kwargs,
                        "message": event.ctx.message,
                    }
                )
            sentry_sdk.capture_exception(event.error)


def setup(
    bot: Client,
    token: str = None,
    filter: Optional[Callable[[dict[str, Any], dict[str, Any]], Optional[dict[str, Any]]]] = None
) -> None:
    if not token:
        logging.error('Sentry token not found, disabling Sentry integration')
        return
    if filter is None:
        filter = default_sentry_filter        
    sentry_sdk.init(token, before_send=filter)
    Sentry(bot)