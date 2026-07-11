"""Streamlit 여러 페이지에서 함께 사용하는 함수."""

from __future__ import annotations

from typing import Any

import pandas as pd
import streamlit as st

from youtube_api import (
    YouTubeAPIError,
    create_youtube_client,
    extract_video_id,
    fetch_top_level_comments,
    get_video_details,
)

COMMENT_COLUMNS = [
    "comment_id",
    "author",
    "author_channel_url",
    "author_profile_image_url",
    "comment",
    "like_count",
    "reply_count",
    "published_at",
    "updated_at",
    "comment_url",
]


def init_session_state() -> None:
    defaults: dict[str, Any] = {
        "comments_df": pd.DataFrame(columns=COMMENT_COLUMNS),
        "video_details": {},
        "video_url_input": "",
        "fetch_order": "relevance",
        "max_comments": 500,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def get_api_key() -> str | None:
    """Streamlit Secrets에서만 API 키를 읽는다."""
    try:
        key = st.secrets["google"]["youtube_api_key"]
    except (FileNotFoundError, KeyError, TypeError, AttributeError):
        return None
    key = str(key).strip()
    return key or None


def render_api_status() -> bool:
    api_key_exists = get_api_key() is not None
    if api_key_exists:
        st.success("YouTube API 키가 Secrets에 연결되어 있습니다.", icon="✅")
    else:
        st.warning(
            "API 키가 아직 없습니다. Streamlit 앱의 Settings → Secrets에 키를 등록해 주세요.",
            icon="🔑",
        )
    return api_key_exists


def _normalize_comment_dataframe(comments: list[dict[str, Any]]) -> pd.DataFrame:
    df = pd.DataFrame(comments, columns=COMMENT_COLUMNS)
    if df.empty:
        return df

    df["like_count"] = pd.to_numeric(df["like_count"], errors="coerce").fillna(0).astype(int)
    df["reply_count"] = pd.to_numeric(df["reply_count"], errors="coerce").fillna(0).astype(int)
    df["published_at"] = pd.to_datetime(df["published_at"], errors="coerce", utc=True)
    df["updated_at"] = pd.to_datetime(df["updated_at"], errors="coerce", utc=True)
    return df


def render_comment_loader(key_prefix: str = "loader") -> bool:
    """댓글 불러오기 폼을 표시하고 성공 여부를 반환한다."""
    with st.form(f"{key_prefix}_form"):
        video_value = st.text_input(
            "YouTube 영상 주소",
            value=st.session_state.get("video_url_input", ""),
            placeholder="https://www.youtube.com/watch?v=...",
            key=f"{key_prefix}_url",
        )
        left, right = st.columns(2)
        with left:
            max_comments = st.select_slider(
                "가져올 최대 댓글 수",
                options=[50, 100, 200, 300, 500, 700, 1000, 1500, 2000],
                value=st.session_state.get("max_comments", 500),
                key=f"{key_prefix}_max",
                help="댓글 100개마다 API 요청이 한 번씩 추가됩니다.",
            )
        with right:
            order_label = st.selectbox(
                "YouTube API 수집 순서",
                options=["관련도순", "최신순"],
                index=0 if st.session_state.get("fetch_order") == "relevance" else 1,
                key=f"{key_prefix}_order",
            )
        submitted = st.form_submit_button(
            "댓글 불러오기",
            type="primary",
            use_container_width=True,
        )

    if not submitted:
        return False

    api_key = get_api_key()
    if not api_key:
        st.error("먼저 Streamlit Settings → Secrets에 YouTube API 키를 등록해 주세요.")
        return False

    try:
        video_id = extract_video_id(video_value)
        order = "relevance" if order_label == "관련도순" else "time"

        with st.spinner("영상 정보와 댓글을 불러오는 중입니다..."):
            youtube = create_youtube_client(api_key)
            video_details = get_video_details(youtube, video_id)
            comments = fetch_top_level_comments(
                youtube,
                video_id,
                max_comments=max_comments,
                order=order,
            )
            comments_df = _normalize_comment_dataframe(comments)

        st.session_state["comments_df"] = comments_df
        st.session_state["video_details"] = video_details
        st.session_state["video_url_input"] = video_value
        st.session_state["fetch_order"] = order
        st.session_state["max_comments"] = max_comments

        if comments_df.empty:
            st.warning("가져올 수 있는 공개 댓글이 없습니다.")
        else:
            st.success(f"댓글 {len(comments_df):,}개를 불러왔습니다.")
        return True
    except (ValueError, YouTubeAPIError) as error:
        st.error(str(error))
        return False
    except Exception as error:  # 예상하지 못한 배포 환경 오류 표시
        st.error(f"예상하지 못한 오류가 발생했습니다: {error}")
        return False


def has_comments() -> bool:
    df = st.session_state.get("comments_df")
    return isinstance(df, pd.DataFrame) and not df.empty


def require_comments() -> bool:
    if has_comments():
        return True

    st.info("먼저 ‘전체 댓글 분석’ 페이지에서 영상 댓글을 불러와 주세요.")
    try:
        st.page_link(
            "pages/1_전체_댓글_분석.py",
            label="전체 댓글 분석 페이지로 이동",
            icon="📊",
        )
    except Exception:
        pass
    return False


def render_video_summary() -> None:
    details = st.session_state.get("video_details", {})
    if not details:
        return

    image_col, info_col = st.columns([1, 2])
    with image_col:
        thumbnail_url = details.get("thumbnail_url")
        if thumbnail_url:
            st.image(thumbnail_url, use_container_width=True)
    with info_col:
        st.subheader(details.get("title", "영상"))
        st.caption(f"채널: {details.get('channel_title', '정보 없음')}")
        metric_cols = st.columns(3)
        metric_cols[0].metric("조회수", f"{details.get('view_count', 0):,}")
        metric_cols[1].metric("영상 좋아요", f"{details.get('like_count', 0):,}")
        metric_cols[2].metric("전체 댓글 수", f"{details.get('comment_count', 0):,}")
        st.link_button("YouTube에서 영상 열기", details.get("video_url", "https://youtube.com"))


def classify_comments(
    df: pd.DataFrame,
    popular_threshold: int = 10,
    top_threshold: int = 100,
) -> pd.DataFrame:
    """좋아요 수 기준으로 일반/인기/최상위 댓글을 구분한다."""
    result = df.copy()
    popular_threshold = max(1, int(popular_threshold))
    top_threshold = max(popular_threshold + 1, int(top_threshold))

    def category(likes: int) -> str:
        if likes >= top_threshold:
            return "🔥 최상위 댓글"
        if likes >= popular_threshold:
            return "⭐ 인기 댓글"
        return "일반 댓글"

    result["category"] = result["like_count"].apply(category)
    return result


def display_comment_table(df: pd.DataFrame, key: str) -> None:
    if df.empty:
        st.info("조건에 맞는 댓글이 없습니다.")
        return

    display_columns = [
        column
        for column in [
            "category",
            "author",
            "comment",
            "like_count",
            "reply_count",
            "published_at",
            "comment_url",
        ]
        if column in df.columns
    ]
    display_df = df[display_columns].copy()
    if "published_at" in display_df.columns:
        display_df["published_at"] = display_df["published_at"].dt.strftime(
            "%Y-%m-%d %H:%M"
        )

    column_config: dict[str, Any] = {
        "category": st.column_config.TextColumn("분류", width="small"),
        "author": st.column_config.TextColumn("작성자", width="medium"),
        "comment": st.column_config.TextColumn("댓글", width="large"),
        "like_count": st.column_config.NumberColumn("좋아요", format="%d"),
        "reply_count": st.column_config.NumberColumn("답글", format="%d"),
        "published_at": st.column_config.TextColumn("작성일"),
        "comment_url": st.column_config.LinkColumn("댓글 링크", display_text="열기"),
    }

    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True,
        column_config=column_config,
        key=key,
    )


def dataframe_to_csv_bytes(df: pd.DataFrame) -> bytes:
    export_df = df.copy()
    for column in ["published_at", "updated_at"]:
        if column in export_df.columns:
            export_df[column] = export_df[column].astype(str)
    return export_df.to_csv(index=False).encode("utf-8-sig")
