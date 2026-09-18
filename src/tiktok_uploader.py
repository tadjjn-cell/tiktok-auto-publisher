import logging
import os
import time

import httpx

logger = logging.getLogger(__name__)

DIRECT_INIT_URL = "https://open.tiktokapis.com/v2/post/publish/video/init/"
INBOX_INIT_URL = "https://open.tiktokapis.com/v2/post/publish/inbox/video/init/"
STATUS_URL = "https://open.tiktokapis.com/v2/post/publish/status/fetch/"

MAX_CHUNK_SIZE = 60 * 1024 * 1024  # 60MB, within TikTok's recommended 5-64MB chunk range

DONE_STATUSES = {"PUBLISH_COMPLETE", "SEND_TO_USER_INBOX"}


def _chunk_plan(video_size: int) -> tuple[int, int]:
    if video_size <= MAX_CHUNK_SIZE:
        return video_size, 1
    return MAX_CHUNK_SIZE, -(-video_size // MAX_CHUNK_SIZE)  # ceil division


def _init_and_upload(client: httpx.Client, headers: dict, init_url: str, body: dict, file_path: str) -> str:
    resp = client.post(init_url, headers=headers, json=body)
    resp.raise_for_status()
    payload = resp.json()
    error = payload.get("error", {})
    if error.get("code") not in (None, "ok"):
        raise Exception(f"TikTok init failed: {error}")

    data = payload["data"]
    publish_id = data["publish_id"]
    upload_url = data["upload_url"]

    video_size = body["source_info"]["video_size"]
    chunk_size = body["source_info"]["chunk_size"]

    with open(file_path, "rb") as f:
        start = 0
        while start < video_size:
            end = min(start + chunk_size, video_size) - 1
            f.seek(start)
            chunk = f.read(end - start + 1)
            put_resp = client.put(
                upload_url,
                headers={"Content-Range": f"bytes {start}-{end}/{video_size}", "Content-Type": "video/mp4"},
                content=chunk,
            )
            if put_resp.status_code not in (200, 201, 206):
                raise Exception(f"TikTok chunk upload failed ({put_resp.status_code}): {put_resp.text}")
            start = end + 1

    for _ in range(10):
        time.sleep(3)
        try:
            status_resp = client.post(STATUS_URL, headers=headers, json={"publish_id": publish_id})
            status_data = status_resp.json().get("data", {})
        except Exception as e:
            logger.warning(f"Could not fetch TikTok status: {e}")
            break
        status = status_data.get("status")
        if status in DONE_STATUSES:
            break
        if status == "FAILED":
            raise Exception(f"TikTok processing failed: {status_data}")

    return publish_id


def _headers(access_token: str) -> dict:
    return {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json; charset=UTF-8",
    }


def upload_to_drafts(access_token: str, file_path: str) -> str:
    """
    Upload a video to the user's TikTok inbox/drafts (Upload API, scope video.upload).
    The API accepts no caption here: the creator opens the draft in the TikTok app,
    pastes a caption, and taps Post. Returns the publish_id.
    """
    video_size = os.path.getsize(file_path)
    chunk_size, total_chunk_count = _chunk_plan(video_size)
    body = {
        "source_info": {
            "source": "FILE_UPLOAD",
            "video_size": video_size,
            "chunk_size": chunk_size,
            "total_chunk_count": total_chunk_count,
        }
    }
    with httpx.Client(timeout=120) as client:
        return _init_and_upload(client, _headers(access_token), INBOX_INIT_URL, body, file_path)


def upload_direct_post(
    access_token: str,
    file_path: str,
    caption: str,
    privacy_level: str = "SELF_ONLY",
    disable_duet: bool = False,
    disable_comment: bool = False,
    disable_stitch: bool = False,
) -> str:
    """
    Publish straight to the profile (Direct Post, scope video.publish). Until the TikTok
    app passes audit, TikTok forces SELF_ONLY visibility regardless of privacy_level.
    """
    video_size = os.path.getsize(file_path)
    chunk_size, total_chunk_count = _chunk_plan(video_size)
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
    with httpx.Client(timeout=120) as client:
        return _init_and_upload(client, _headers(access_token), DIRECT_INIT_URL, body, file_path)
