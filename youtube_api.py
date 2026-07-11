"""YouTube Data API v3 호출과 URL 처리 함수."""

from __future__ import annotations

import json
import re
from typing import Any
from urllib.parse import parse_qs, urlparse

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

VIDEO_ID_PATTERN = re.compile(r"^[A-Za-z0-9_-]{11}$")


class YouTubeAPIError(RuntimeError):
    """사용자에게 보여줄 수 있는 YouTube API 오류."""


def extract_video_id(value: str) -> str:
    """YouTube 영상 URL 또는 11자리 영상 ID에서 videoId를 추출한다."""
    raw = (value or "").strip()
    if not raw:
        raise ValueError("YouTube 영상 URL 또는 영상 ID를 입력해 주세요.")

    if VIDEO_ID_PATTERN.fullmatch(raw):
        return raw

    candidate_url = raw if "://" in raw else f"https://{raw}"
    parsed = urlparse(candidate_url)
    host = parsed.netloc.lower().split(":")[0]
    path_parts = [part for part in parsed.path.split("/") if part]

    video_id = ""
    if host in {"youtu.be", "www.youtu.be"} and path_parts:
        video_id = path_parts[0]
    elif host.endswith("youtube.com"):
        if parsed.path == "/watch":
            video_id = parse_qs(parsed.query).get("v", [""])[0]
        elif path_parts and path_parts[0] in {"shorts", "embed", "live"}:
            if len(path_parts) >= 2:
                video_id = path_parts[1]

    video_id = video_id.strip()
    if not VIDEO_ID_PATTERN.fullmatch(video_id):
        raise ValueError(
            "올바른 YouTube 주소를 입력해 주세요. watch, youtu.be, shorts, embed, live 주소를 지원합니다."
        )
    return video_id


def create_youtube_client(api_key: str) -> Any:
    """API 키로 YouTube Data API v3 클라이언트를 생성한다."""
    if not api_key or not api_key.strip():
        raise ValueError("YouTube API 키가 설정되어 있지 않습니다.")

    return build(
        "youtube",
        "v3",
        developerKey=api_key.strip(),
        cache_discovery=False,
    )


def _friendly_http_error(error: HttpError) -> YouTubeAPIError:
    status = getattr(error.resp, "status", None)
    reason = ""
    message = ""

    try:
        payload = json.loads(error.content.decode("utf-8"))
        api_error = payload.get("error", {})
        message = api_error.get("message", "")
        errors = api_error.get("errors", [])
        if errors:
            reason = errors[0].get("reason", "")
    except (ValueError, UnicodeDecodeError, AttributeError):
        pass

    known_messages = {
        "commentsDisabled": "이 영상은 댓글 사용이 중지되어 있습니다.",
        "videoNotFound": "영상을 찾을 수 없습니다. 비공개 또는 삭제된 영상일 수 있습니다.",
        "quotaExceeded": "YouTube API의 오늘 할당량을 초과했습니다.",
        "dailyLimitExceeded": "YouTube API의 일일 사용 한도를 초과했습니다.",
        "keyInvalid": "YouTube API 키가 올바르지 않습니다.",
        "accessNotConfigured": "Google Cloud에서 YouTube Data API v3가 활성화되어 있지 않습니다.",
        "forbidden": "이 영상의 댓글에 접근할 권한이 없습니다.",
    }

    if reason in known_messages:
        return YouTubeAPIError(known_messages[reason])
    if status == 400:
        return YouTubeAPIError("요청 형식이 올바르지 않습니다. 영상 주소를 다시 확인해 주세요.")
    if status == 403:
        return YouTubeAPIError(
            "API 접근이 거부되었습니다. API 활성화, 키 제한 설정, 할당량을 확인해 주세요."
        )
    if status == 404:
        return YouTubeAPIError("영상을 찾을 수 없습니다.")

    detail = message or str(error)
    return YouTubeAPIError(f"YouTube API 요청 중 오류가 발생했습니다: {detail}")


def get_video_details(youtube: Any, video_id: str) -> dict[str, Any]:
    """영상 제목, 채널, 통계, 썸네일 정보를 가져온다."""
    try:
        response = (
            youtube.videos()
            .list(part="snippet,statistics", id=video_id, maxResults=1)
            .execute()
        )
    except HttpError as error:
        raise _friendly_http_error(error) from error

    items = response.get("items", [])
    if not items:
        raise YouTubeAPIError("영상을 찾을 수 없습니다. 주소나 공개 상태를 확인해 주세요.")

    item = items[0]
    snippet = item.get("snippet", {})
    statistics = item.get("statistics", {})
    thumbnails = snippet.get("thumbnails", {})
    thumbnail = (
        thumbnails.get("maxres")
        or thumbnails.get("standard")
        or thumbnails.get("high")
        or thumbnails.get("medium")
        or thumbnails.get("default")
        or {}
    )

    return {
        "video_id": video_id,
        "title": snippet.get("title", "제목 없음"),
        "channel_title": snippet.get("channelTitle", "채널 정보 없음"),
        "published_at": snippet.get("publishedAt", ""),
        "thumbnail_url": thumbnail.get("url", ""),
        "view_count": int(statistics.get("viewCount", 0)),
        "like_count": int(statistics.get("likeCount", 0)),
        "comment_count": int(statistics.get("commentCount", 0)),
        "video_url": f"https://www.youtube.com/watch?v={video_id}",
    }


def fetch_top_level_comments(
    youtube: Any,
    video_id: str,
    max_comments: int = 500,
    order: str = "relevance",
) -> list[dict[str, Any]]:
    """영상의 최상위 댓글을 페이지 단위로 가져온다."""
    if order not in {"relevance", "time"}:
        raise ValueError("댓글 정렬 방식은 relevance 또는 time이어야 합니다.")

    requested_count = max(1, min(int(max_comments), 5000))
    comments: list[dict[str, Any]] = []
    page_token: str | None = None

    while len(comments) < requested_count:
        batch_size = min(100, requested_count - len(comments))
        request_kwargs: dict[str, Any] = {
            "part": "snippet",
            "videoId": video_id,
            "maxResults": batch_size,
            "order": order,
            "textFormat": "plainText",
        }
        if page_token:
            request_kwargs["pageToken"] = page_token

        try:
            response = youtube.commentThreads().list(**request_kwargs).execute()
        except HttpError as error:
            raise _friendly_http_error(error) from error

        for item in response.get("items", []):
            thread_snippet = item.get("snippet", {})
            top_comment = thread_snippet.get("topLevelComment", {})
            comment_snippet = top_comment.get("snippet", {})
            comment_id = top_comment.get("id", "")

            comments.append(
                {
                    "comment_id": comment_id,
                    "author": comment_snippet.get("authorDisplayName", "알 수 없음"),
                    "author_channel_url": comment_snippet.get("authorChannelUrl", ""),
                    "author_profile_image_url": comment_snippet.get(
                        "authorProfileImageUrl", ""
                    ),
                    "comment": comment_snippet.get("textOriginal")
                    or comment_snippet.get("textDisplay", ""),
                    "like_count": int(comment_snippet.get("likeCount", 0)),
                    "reply_count": int(thread_snippet.get("totalReplyCount", 0)),
                    "published_at": comment_snippet.get("publishedAt", ""),
                    "updated_at": comment_snippet.get("updatedAt", ""),
                    "comment_url": (
                        f"https://www.youtube.com/watch?v={video_id}&lc={comment_id}"
                        if comment_id
                        else f"https://www.youtube.com/watch?v={video_id}"
                    ),
                }
            )
            if len(comments) >= requested_count:
                break

        page_token = response.get("nextPageToken")
        if not page_token:
            break

    return comments
