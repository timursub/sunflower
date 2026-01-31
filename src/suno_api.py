#!/usr/bin/env python3
"""Suno API Integration Module"""

import asyncio
import logging
import os

import aiohttp
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
SUNO_API_KEY = os.getenv("SUNO_API_KEY")
SUNO_API_URL = os.getenv("SUNO_API_URL", "https://api.sunoapi.org/api/v1")

if not SUNO_API_KEY:
    logger.warning("No SUNO_API_KEY found!")


_headers = {
    "Authorization": f"Bearer {SUNO_API_KEY}",
    "Content-Type": "application/json",
}

REQUEST_TIMEOUT = 30


async def create_generating_tasks(prompt, count):
    data = {
        "customMode": False,
        "instrumental": False,
        "callBackUrl": "playground",
        "model": "V4",
        "prompt": prompt,
        "negativeTags": "",
    }
    tasks_ids = []

    timeout = aiohttp.ClientTimeout(total=REQUEST_TIMEOUT)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        for _ in range(count):
            async with session.post(
                f"{SUNO_API_URL}/generate",
                headers=_headers,
                json=data,
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    task_id = result["data"]["taskId"]
                    logger.info(f"✅ Started: {task_id}")
                    tasks_ids.append(task_id)
                else:
                    logger.error(f"❌ Failed: {response.status}")
                    raise Exception(f"API returned {response.status}")

            await asyncio.sleep(1)  # even 0.5 helps

    return tasks_ids


async def get_generated_tracks(task_id):
    logger.info(f"📊 Checking: {task_id}")

    timeout = aiohttp.ClientTimeout(total=REQUEST_TIMEOUT)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        async with session.get(
            f"{SUNO_API_URL}/generate/record-info?taskId={task_id}",
            headers=_headers,
        ) as response:
            if response.status == 200:
                result = await response.json()
                data = result["data"]
                if data["status"] == "SUCCESS":
                    urls = []
                    for record in data["response"]["sunoData"]:
                        audioUrl = record["audioUrl"]
                        title = record["title"]
                        urls.append((audioUrl, title))
                    return urls
                else:
                    return None
            else:
                raise Exception(f"Status check returned {response.status}")
            
            """File system utilities for downloading and managing audio files"""


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

