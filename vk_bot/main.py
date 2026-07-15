from __future__ import annotations

import argparse
import asyncio
import logging
import signal

from .client import InternalApiClient, VkApiClient
from .handlers import VkBotHandler, backoff_sleep
from .settings import settings

logger = logging.getLogger(__name__)


async def run() -> None:
    settings.validate()
    vk = VkApiClient(settings)
    internal = InternalApiClient(settings)
    handler = VkBotHandler(vk, internal, settings)
    stop = asyncio.Event()
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, stop.set)
    delay = 1.0
    server = await vk.get_longpoll_server()
    logger.info("bot_started", extra={"event": "bot_started"})
    try:
        while not stop.is_set():
            try:
                payload = await vk.poll(server)
                delay = 1.0
                if "failed" in payload:
                    failed = payload.get("failed")
                    if failed == 1 and payload.get("ts"):
                        server["ts"] = payload["ts"]
                    else:
                        server = await vk.get_longpoll_server()
                    continue
                server["ts"] = payload.get("ts", server["ts"])
                for update in payload.get("updates", []):
                    await handler.handle_update(update)
            except Exception as exc:  # noqa: BLE001
                logger.warning("reconnect_scheduled", extra={"event": "reconnect_scheduled", "retry_delay": delay, "error": type(exc).__name__})
                delay = await backoff_sleep(delay)
                server = await vk.get_longpoll_server()
    finally:
        await vk.close()
        await internal.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Run Bloom Club VK bot")
    parser.add_argument("--log-level", default="INFO")
    args = parser.parse_args()
    logging.basicConfig(level=getattr(logging, args.log_level.upper(), logging.INFO), format="%(asctime)s %(levelname)s %(name)s %(message)s")
    asyncio.run(run())


if __name__ == "__main__":
    main()
