import logging
import re
import asyncio
import yt_dlp
from domain.entities.post import Post
from application.interfaces.instagram_gateway import InstagramGateway

logger = logging.getLogger(__name__)

# Regex to validate Instagram URLs and extract shortcode
INSTAGRAM_URL_PATTERN = re.compile(
    r'(?:https?://)?(?:www\.)?instagram\.com/(?:reel|p|tv)/([\w-]+)',
    re.IGNORECASE,
)

# Custom exceptions for Instagram parsing
class InstagramError(Exception):
    """Base exception for Instagram parsing errors."""
    pass

class PostUnavailableError(InstagramError):
    """Raised when the post is private, deleted, or unavailable."""
    pass

class RateLimitError(InstagramError):
    """Raised when Instagram rate-limits the request."""
    pass

class InvalidURLError(InstagramError):
    """Raised when the URL is not a valid Instagram post/reel link."""
    pass


class YtdlpInstagramGateway(InstagramGateway):
    async def fetch_post(self, url: str, correlation_id: str | None = None) -> Post:
        match = INSTAGRAM_URL_PATTERN.search(url)
        if not match:
            raise InvalidURLError("Bu link Instagram Reels/Post linkiga o'xshamaydi.")
            
        clean_url = match.group(0)
        shortcode = match.group(1)
        
        cid = f"[{correlation_id}] " if correlation_id else ""
        logger.info("%sFetching post from Instagram using yt-dlp. Shortcode: %s", cid, shortcode)

        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': True,
            'skip_download': True,
            'cachedir': False,   # Disable cache folder
            'nocache': True,     # Bypass internal cache
            'http_headers': {
                'Accept-Language': 'en-US,en;q=0.9',
            }
        }

        loop = asyncio.get_event_loop()

        def _extract():
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                return ydl.extract_info(clean_url, download=False)

        try:
            info = await loop.run_in_executor(None, _extract)
        except yt_dlp.utils.DownloadError as e:
            err_msg = str(e)
            logger.warning("yt-dlp download error: %s", err_msg)
            
            if "Private" in err_msg or "login" in err_msg.lower():
                raise PostUnavailableError(
                    "Bu post maxfiy (private). Faqat ochiq (public) postlardan hashtag olish mumkin."
                )
            elif "429" in err_msg or "too many requests" in err_msg.lower():
                raise RateLimitError(
                    "Instagram so'rovlarni cheklamoqda. Iltimos, biroz kuting va qayta urinib ko'ring."
                )
            else:
                raise PostUnavailableError(
                    "Bu post topilmadi. U o'chirilgan yoki maxfiy bo'lishi mumkin."
                )
        except Exception as e:
            logger.exception("Unexpected error fetching post %s", clean_url)
            raise InstagramError(
                f"Post ma'lumotlarini olishda xatolik yuz berdi: {e}"
            )

        caption = info.get('description') or info.get('title') or ""
        
        # Extract comments
        comments_list = []
        raw_comments = info.get('comments') or []
        for c in raw_comments:
            text = c.get('text')
            if text:
                comments_list.append(text)

        return Post(
            shortcode=shortcode,
            url=clean_url,
            caption=caption,
            comments=comments_list
        )
