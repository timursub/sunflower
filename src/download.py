"""File system utilities for downloading and managing audio files"""

import logging

import aiohttp

logger = logging.getLogger(__name__)


async def download_audio(url):
    """
    Download audio file from URL into memory

    Args:
        url: The URL to download from

    Returns:
        Audio file content as bytes
    """
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                response.raise_for_status()
                content = await response.read()

        logger.info(f"Downloaded audio from {url} ({len(content)} bytes)")
        return content

    except Exception as e:
        logger.error(f"Failed to download {url}: {e}")
        raise
