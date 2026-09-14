import logging
import os
import time

import httpx

logger = logging.getLogger(__name__)

INIT_URL = "https://open.tiktokapis.com/v2/post/publish/video/init/"
STATUS_URL = "https://open.tiktokapis.com/v2/post/publish/status/fetch/"

MAX_CHUNK_SIZE = 60 * 1024 * 1024  # 60MB, within TikTok's recommended 5-64MB chunk range


def upload_video(
    access_token: str,
    file_path: str,
    caption: str,
    privacy_level: str = "SELF_ONLY",
    disable_duet: bool = False,
    disable_comment: bool = False,
    disable_stitch: bool = False,
) -> str:
    """
    Upload and publish a video via TikTok's Content Posting API (Direct Post, FILE_UPLOAD source).
    Returns the publish_id. Note: until the TikTok app passes audit, privacy_level is
    typically restricted to "SELF_ONLY" by TikTok itself regardless of what's requested here.
    """
    video_size = os.path.getsize(file_path)
    if video_size <= MAX_CHUNK_SIZE:
        chunk_size = video_size
        total_chunk_count = 1
    else:
        chunk_size = MAX_CHUNK_SIZE
        total_chunk_count = -(-video_size // MAX_CHUNK_SIZE)  # ceil division

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json; charset=UTF-8",
    }
    body = {
        "post_info": {
            "title": caption,
            "privacy_level": privacy_level,
            "disable_duet": disable_duet,
            "disable_comment": disable_comment,
            "disable_stitch": disable_stitch,
            "video_cover_timestamp_ms": 1000,
        },
        "source_info": {
            "source": "FILE_UPLOAD",
            "video_size": video_size,
            "chunk_size": chunk_size,
            "total_chunk_count": total_chunk_count,
        },
    }

    with httpx.Client(timeout=60) as client:
        resp = client.post(INIT_URL, headers=headers, json=body)
        resp.raise_for_status()
        payload = resp.json()
        error = payload.get("error", {})
        if error.get("code") not in (None, "ok"):
            raise Exception(f"TikTok init failed: {error}")

        data = payload["data"]
        publish_id = data["publish_id"]
        upload_url = data["upload_url"]

        with open(file_path, "rb") as f:
            start = 0
            while start < video_size:
                end = min(start + chunk_size, video_size) - 1
                f.seek(start)
                chunk = f.read(end - start + 1)
                upload_headers = {
                    "Content-Range": f"bytes {start}-{end}/{video_size}",
                    "Content-Type": "video/mp4",
                }
                put_resp = client.put(upload_url, headers=upload_headers, content=chunk)
                if put_resp.status_code not in (200, 201, 206):
                    raise Exception(f"TikTok chunk upload failed ({put_resp.status_code}): {put_resp.text}")
                start = end + 1

        for _ in range(10):
            time.sleep(3)
            try:
                status_resp = client.post(STATUS_URL, headers=headers, json={"publish_id": publish_id})
                status_data = status_resp.json().get("data", {})
            except Exception as e:
                logger.warning(f"Could not fetch TikTok publish status: {e}")
                break
            status = status_data.get("status")
            if status == "PUBLISH_COMPLETE":
                break
            if status == "FAILED":
                raise Exception(f"TikTok publish failed: {status_data}")

        return publish_id
