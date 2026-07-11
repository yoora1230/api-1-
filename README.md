# YouTube 인기 댓글 분류기

YouTube Data API v3로 공개된 최상위 댓글을 가져와 좋아요 수 기준으로 분류하는 Streamlit 멀티페이지 앱입니다.

## 폴더 구조

```text
youtube_comment_analyzer/
├─ main.py
├─ app_utils.py
├─ youtube_api.py
├─ requirements.txt
├─ pages/
│  ├─ 1_전체_댓글_분석.py
│  ├─ 2_좋아요_많은_댓글.py
│  ├─ 3_댓글_검색.py
│  └─ 4_사용_안내.py
└─ .streamlit/
   └─ secrets.toml.example
```

## Streamlit Community Cloud Secrets

앱의 **Settings → Secrets**에 다음 형식으로 등록하세요.

```toml
[google]
youtube_api_key = "YOUR_YOUTUBE_API_KEY"
```

실제 API 키가 들어 있는 `.streamlit/secrets.toml` 파일은 GitHub에 커밋하지 마세요.

## 로컬 실행

```bash
pip install -r requirements.txt
streamlit run main.py
```

## 기능

- YouTube 영상 URL/ID 인식
- 공개 최상위 댓글 최대 2,000개 수집
- 좋아요 및 답글 통계
- 좋아요 구간별 차트
- 인기/최상위 댓글 분류 기준 설정
- 댓글 키워드 및 작성자 검색
- CSV 다운로드
- API 오류와 댓글 비활성화 오류 안내
