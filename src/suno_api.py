#!/usr/bin/env python3
"""Suno API Integration Module"""

import logging
import os
import time

import requests
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


def create_generating_tasks(prompt, count):
    data = {
        "customMode": False,
        "instrumental": False,
        "callBackUrl": "playground",
        "model": "V4",
        "prompt": prompt,
        "negativeTags": "",
    }
    tasks_ids = []
    for _ in range(count):
        response = requests.post(
            f"{SUNO_API_URL}/generate",
            headers=_headers,
            json=data,
            timeout=REQUEST_TIMEOUT,
        )

        if response.status_code == 200:
            result = response.json()
            task_id = result["data"]["taskId"]
            logger.info(f"✅ Started: {task_id}")
            tasks_ids.append(task_id)
        else:
            logger.error(f"❌ Failed: {response.status_code}")
            raise Exception(f"API returned {response.status_code}")

        time.sleep(1)  # even 0.5 helps

    return tasks_ids


def get_generated_tracks(task_id):
    logger.info(f"📊 Checking: {task_id}")

    response = requests.get(
        f"{SUNO_API_URL}/generate/record-info?taskId={task_id}",
        headers=_headers,
        timeout=REQUEST_TIMEOUT,
    )

    if response.status_code == 200:
        result = response.json()
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
        raise Exception(f"Status check returned {response.status_code}")
