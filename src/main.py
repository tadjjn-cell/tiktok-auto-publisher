import asyncio
import logging
import os

from src.config import load_config
from src.state import load_state, save_state
from src.telegram_client import get_telegram_client
from src.telegram_source import fetch_new_videos
from src.trends import get_trending_queries
from src.caption_generator import generate_tiktok_caption
from src.tiktok_auth import refresh_access_token
from src.tiktok_uploader import upload_to_drafts, upload_direct_post

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def build_caption(caption: str, hashtags: list[str]) -> str:
    if not hashtags:
        return caption
    tag_line = " ".join(f"#{h.replace(' ', '')}" for h in hashtags)
    return f"{caption}\n\n{tag_line}"


async def notify(client, chat, text: str) -> None:
    try:
        await client.send_message(chat, text)
    except Exception as e:
        logger.warning(f"Could not send Telegram notification: {e}")


async def main() -> None:
    config = load_config()
    state_path = config.get("paths", {}).get("state_file", "data/state.json")
    state = load_state(state_path)

    client = get_telegram_client(config)
    await client.start()

    try:
        max_per_run = config.get("limits", {}).get("max_uploads_per_run", 3)
        videos = await fetch_new_videos(client, config, state, limit=max_per_run)

        if not videos:
            logger.info("No new videos found.")
            return

        refresh_token = state.get("tiktok_refresh_token") or config["tiktok_refresh_token"]
        token_data = await asyncio.to_thread(
            refresh_access_token, config["tiktok_client_key"], config["tiktok_client_secret"], refresh_token
        )
        access_token = token_data["access_token"]
        state["tiktok_refresh_token"] = token_data.get("refresh_token", refresh_token)

        source_chat = config["telegram_source_chat"]
        max_trending = config.get("keywords", {}).get("max_trending", 10)
        privacy_level = config.get("tiktok", {}).get("privacy_level", "SELF_ONLY")
        mode = config.get("tiktok", {}).get("mode", "draft")

        for video in videos:
            topic = video["caption"] or "video"
            logger.info(f"Processing message {video['message_id']}: topic='{topic}'")
            try:
                trending = await asyncio.to_thread(get_trending_queries, topic, max_trending)
                result = await generate_tiktok_caption(topic, trending, config)
                caption = build_caption(result["caption"], result["hashtags"])

                if mode == "draft":
                    publish_id = await asyncio.to_thread(upload_to_drafts, access_token, video["file_path"])
                    logger.info(f"Uploaded to TikTok drafts: {publish_id}")
                    safe_caption = caption.replace("`", "'")
                    await notify(
                        client,
                        source_chat,
                        "📥 Video is in your TikTok drafts. Tap the caption below to copy it, "
                        "then open the draft in TikTok, paste, and tap Post:\n\n"
                        f"```\n{safe_caption}\n```",
                    )
                else:
                    publish_id = await asyncio.to_thread(
                        upload_direct_post, access_token, video["file_path"], caption, privacy_level
                    )
                    logger.info(f"Published to TikTok: {publish_id}")
                    await notify(client, source_chat, f"✅ Posted to TikTok:\n{caption[:200]}")

            except Exception as e:
                logger.error(f"Failed to process message {video['message_id']}: {e}")
                await notify(
                    client,
                    source_chat,
                    f"⚠️ Failed to publish TikTok video (message {video['message_id']}): {e}",
                )
            finally:
                if os.path.exists(video["file_path"]):
                    os.remove(video["file_path"])

    finally:
        save_state(state, state_path)
        await client.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
