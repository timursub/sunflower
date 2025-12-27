#!/usr/bin/env python3
"""Suno API Integration Module"""

import os
import requests
import time
import logging
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
SUNO_API_KEY = os.getenv('SUNO_API_KEY')
SUNO_API_URL = os.getenv('SUNO_API_URL', 'https://api.sunoapi.org/api/v1')

if not SUNO_API_KEY:
    logger.warning("No SUNO_API_KEY found!")


def get_headers():
    """Get API request headers"""
    return {
        'Authorization': f'Bearer {SUNO_API_KEY}',
        'Content-Type': 'application/json',
    }


def generate_music(prompt, duration=30, genre=None):
    """
    Generate music using Suno API
    
    Args:
        prompt (str): Music description
        duration (int): Length in seconds
        genre (str): Optional genre
    
    Returns:
        dict: Response with task_id or error
    """
    try:
        data = {
            'customMode': False,
            "instrumental": False,
            'callBackUrl': 'playground',
            'model': 'V4',
            'prompt': prompt, 
            'negativeTags': "",
            # 'duration': duration
        }
        # if genre:
        #     data['genre'] = genre
        
        logger.info(f"🎵 Generating: '{prompt}'")
        response = requests.post(
            f'{SUNO_API_URL}/generate',
            headers=get_headers(),
            json=data,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            print(result)
            task_id = result["data"]["taskId"]
            logger.info(f"✅ Started: {task_id}")
            return {
                'success': True,
                'task_id': task_id
            }
        else:
            logger.error(f"❌ Failed: {response.status_code}")
            return {
                'success': False,
                'error': f'API returned {response.status_code}'
            }
            
    except requests.exceptions.Timeout:
        return {'success': False, 'error': 'Request timed out'}
    except requests.exceptions.RequestException as e:
        return {'success': False, 'error': str(e)}


def check_generation_status(task_id):
    """
    Check generation task status
    
    Args:
        task_id (str): Task ID from generate_music
    
    Returns:
        dict: Status information
    """
    try:
        logger.info(f"📊 Checking: {task_id}")
        
        response = requests.get(
            f'{SUNO_API_URL}/generate/record-info?taskId={task_id}',
            headers=get_headers(),
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            data = result["data"]
            if data["status"] == "SUCCESS":
                return {
                    'success': True,
                    'status': 'completed',
                    'audio_url': data["response"]["sunoData"][0]["audioUrl"]
                }
            else:
                return {
                    'success': True,
                    'status': 'not ready',
                }

        else:
            return {
                'success': False,
                'error': f'Status check returned {response.status_code}'
            }
            
    except requests.exceptions.RequestException as e:
        return {'success': False, 'error': str(e)}


def wait_for_completion(task_id, max_wait_time=300, poll_interval=5):
    """
    Wait for generation to complete
    
    Args:
        task_id (str): Task ID to wait for
        max_wait_time (int): Maximum wait in seconds
        poll_interval (int): Check frequency in seconds
    
    Returns:
        dict: Final status with audio URL or error
    """
    start_time = time.time()
    
    while True:
        elapsed = time.time() - start_time
        if elapsed > max_wait_time:
            return {'success': False, 'error': 'Generation timed out'}
        
        status_result = check_generation_status(task_id)
        
        if not status_result['success']:
            return status_result
        
        if status_result['status'] == 'completed':
            logger.info("✅ Completed!")
            return status_result
        
        if status_result['status'] == 'failed':
            return {'success': False, 'error': 'Generation failed'}
        
        logger.info(f"⏳ Processing... ({elapsed:.0f}s)")
        time.sleep(poll_interval)


def download_audio(audio_url, output_path):
    """
    Download generated audio file
    
    Args:
        audio_url (str): URL of audio file
        output_path (str): Where to save
    
    Returns:
        bool: Success status
    """
    try:
        logger.info(f"⬇️ Downloading to {output_path}")
        
        response = requests.get(audio_url, stream=True, timeout=30)
        
        if response.status_code == 200:
            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            logger.info("✅ Downloaded")
            return True
        else:
            logger.error(f"❌ Download failed: {response.status_code}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        return False


def generate_and_wait(prompt, duration=30, genre=None):
    """
    Generate music and wait for completion
    
    Convenience function that combines generate + wait
    
    Args:
        prompt (str): Music description
        duration (int): Length in seconds
        genre (str): Optional genre
    
    Returns:
        dict: Complete result with audio URL or error
    """
    result = generate_music(prompt, duration, genre)
    if not result['success']:
        return result
    return wait_for_completion(result['task_id'])


if __name__ == '__main__':
    # Test the API
    print("Testing Suno API...\n")
    result = generate_and_wait('ambient synthwave with distorted guitars and text we are the champions ', duration=15)
    if result['success']:
        print(f"✅ Success: {result['audio_url']}")
    else:
        print(f"❌ Failed: {result['error']}")

