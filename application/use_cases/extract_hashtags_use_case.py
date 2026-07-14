import logging
from dataclasses import dataclass
from domain.entities.post import Post
from domain.value_objects.hashtag import Hashtag
from domain.services.hashtag_extractor import extract_hashtags
from application.interfaces.instagram_gateway import InstagramGateway
from application.interfaces.user_repository import UserRepository
from infrastructure.instagram.yt_dlp_gateway import INSTAGRAM_URL_PATTERN

logger = logging.getLogger(__name__)

@dataclass
class ExtractionResult:
    hashtags: list[Hashtag]
    preview_text: str
    source: str  # 'caption', 'comments', or 'none'

class ExtractHashtagsUseCase:
    def __init__(self, instagram_gateway: InstagramGateway, user_repository: UserRepository):
        self.instagram_gateway = instagram_gateway
        self.user_repository = user_repository

    async def execute(self, user_telegram_id: int, url: str, correlation_id: str | None = None) -> ExtractionResult:
        cid = f"[{correlation_id}] " if correlation_id else ""
        logger.info("%sStarting hashtag extraction for URL: %s", cid, url)

        # Safety Check: Extract expected shortcode from requested URL
        match = INSTAGRAM_URL_PATTERN.search(url)
        expected_shortcode = match.group(1) if match else None
        
        # Fetch the post details from gateway passing correlation ID
        post = await self.instagram_gateway.fetch_post(url, correlation_id)
        
        logger.info(
            "%sFetched post metadata. Expected shortcode: %s, Fetched shortcode: %s", 
            cid, expected_shortcode, post.shortcode
        )

        # Safety Assertion: Verify shortcodes match
        if expected_shortcode and post.shortcode != expected_shortcode:
            logger.error(
                "%sSafety violation: shortcode mismatch! Expected '%s' but fetched '%s'",
                cid, expected_shortcode, post.shortcode
            )
            raise ValueError("Qaytgan ma'lumotlar yuborilgan havola shortcode'iga mos kelmadi.")

        # 1. Check caption
        hashtags = extract_hashtags(post.caption)
        if hashtags:
            logger.info("%sFound %d hashtags in post caption.", cid, len(hashtags))
            preview = post.caption[:200]
            if len(post.caption) > 200:
                preview += "..."
            
            # Log the request
            user = await self.user_repository.get_or_create_user(user_telegram_id)
            await self.user_repository.log_request(user, url, [h.value for h in hashtags])
            
            return ExtractionResult(
                hashtags=hashtags,
                preview_text=preview,
                source='caption'
            )
            
        # 2. If no hashtags in caption, check comments
        logger.info("%sNo hashtags in caption. Checking %d top comments...", cid, len(post.comments))
        for comment in post.comments:
            comment_hashtags = extract_hashtags(comment)
            if comment_hashtags:
                logger.info("%sFound %d hashtags in comment: %s", cid, len(comment_hashtags), comment[:50])
                preview = comment[:200]
                if len(comment) > 200:
                    preview += "..."
                
                # Log the request
                user = await self.user_repository.get_or_create_user(user_telegram_id)
                await self.user_repository.log_request(user, url, [h.value for h in comment_hashtags])
                
                return ExtractionResult(
                    hashtags=comment_hashtags,
                    preview_text=preview,
                    source='comments'
                )
                
        # 3. No hashtags found in caption or comments
        logger.info("%sNo hashtags found anywhere in post caption or comments.", cid)
        preview = post.caption[:200] if post.caption else "Bosh matn (caption) yo'q"
        if len(post.caption) > 200:
            preview += "..."
            
        user = await self.user_repository.get_or_create_user(user_telegram_id)
        await self.user_repository.log_request(user, url, [])
        
        return ExtractionResult(
            hashtags=[],
            preview_text=preview,
            source='none'
        )
