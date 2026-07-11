import streamlit as st

from app_utils import has_comments, init_session_state, render_api_status, render_video_summary

st.set_page_config(
    page_title="YouTube 인기 댓글 분류기",
    page_icon="💬",
    layout="wide",
    initial_sidebar_state="expanded",
)

init_session_state()

st.title("💬 YouTube 인기 댓글 분류기")
st.write(
    "YouTube Data API v3로 영상 댓글을 불러오고, 좋아요 수가 많은 댓글을 별도로 분류하는 사이트입니다."
)

render_api_status()

st.divider()

if has_comments():
    st.subheader("현재 불러온 영상")
    render_video_summary()
    st.success("왼쪽 메뉴에서 인기 댓글 분류 또는 댓글 검색 페이지로 이동할 수 있습니다.")
else:
    st.subheader("사용 순서")
    st.markdown(
        """
1. Streamlit 앱의 **Settings → Secrets**에 YouTube API 키를 등록합니다.
2. 왼쪽 메뉴에서 **전체 댓글 분석** 페이지를 엽니다.
3. YouTube 영상 주소와 댓글 수를 입력한 뒤 댓글을 불러옵니다.
4. **좋아요 많은 댓글** 페이지에서 기준값을 정해 인기 댓글을 분류합니다.
5. 필요한 결과는 CSV 파일로 내려받습니다.
        """
    )

st.divider()

feature_cols = st.columns(3)
with feature_cols[0]:
    st.subheader("📊 전체 분석")
    st.write("댓글 수, 평균 좋아요, 답글 수와 좋아요 분포를 확인합니다.")
with feature_cols[1]:
    st.subheader("🔥 인기 댓글")
    st.write("좋아요 기준을 직접 정하고 인기 댓글과 최상위 댓글을 분리합니다.")
with feature_cols[2]:
    st.subheader("🔎 댓글 검색")
    st.write("키워드, 작성자, 최소 좋아요 수로 댓글을 빠르게 찾습니다.")

st.caption(
    "이 앱은 공개된 최상위 댓글을 분석합니다. 비공개 영상, 삭제된 댓글, 댓글이 중지된 영상은 가져올 수 없습니다."
)
