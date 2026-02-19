from __future__ import annotations

import aiohttp


async def fetch_text(url: str, timeout_s: int = 30) -> str:
    timeout = aiohttp.ClientTimeout(total=timeout_s)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        async with session.get(url) as response:
            response.raise_for_status()
            return await response.text()
