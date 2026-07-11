import streamlit as st

st.set_page_config(page_title="시험 계획표", page_icon="📚", layout="wide")

SUBJECTS = ["국어", "수학", "영어", "과학", "사회"]


def init_state() -> None:
    defaults = {
        "mock_scores": [],
        "wrong_questions": [],
        "study_plan": [],
        "study_materials": {},
    }
    for key, default in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = default.copy() if hasattr(default, "copy") else default

    if not isinstance(st.session_state.mock_scores, list):
        st.session_state.mock_scores = []
    if not isinstance(st.session_state.wrong_questions, list):
        st.session_state.wrong_questions = []
    if not isinstance(st.session_state.study_plan, list):
        st.session_state.study_plan = []
    if not isinstance(st.session_state.study_materials, dict):
        st.session_state.study_materials = {}


def unresolved_count(subject: str) -> int:
    return sum(
        1
        for item in st.session_state.wrong_questions
        if item.get("과목") == subject and not bool(item.get("해결", False))
    )


def expected_score(subject: str) -> float:
    records = sorted(st.session_state.mock_scores, key=lambda item: str(item.get("날짜", "")))
    scores = [
        float(item[subject])
        for item in records
        if isinstance(item.get(subject), (int, float))
    ]
    recent = scores[-3:]
    average = sum(recent) / len(recent) if recent else 70.0
    trend = recent[-1] - recent[-2] if len(recent) >= 2 else 0.0
    penalty = min(12.0, unresolved_count(subject) * 0.8)
    return max(0.0, min(100.0, average + trend * 0.35 - penalty))


init_state()

st.title("📚 나만의 시험 계획표")
st.caption("교과서·자습서·문제집·프린트를 날짜별로 나누어 정확한 공부 내용을 만드는 사이트입니다.")

unsolved_total = sum(
    1 for item in st.session_state.wrong_questions if not bool(item.get("해결", False))
)
predictions = [expected_score(subject) for subject in SUBJECTS]

col1, col2, col3, col4 = st.columns(4)
col1.metric("모의고사 기록", f"{len(st.session_state.mock_scores)}회")
col2.metric("전체 오답", f"{len(st.session_state.wrong_questions)}문제")
col3.metric("미해결 오답", f"{unsolved_total}문제")
col4.metric("평균 예상점수", f"{sum(predictions) / len(predictions):.1f}점")

st.divider()
st.subheader("페이지 안내")

cards = [
    ("🗓️ 날짜별 계획표", "시험 범위와 자료별 페이지를 입력해 달력형 계획표를 만듭니다."),
    ("📊 모의고사 성적", "시험별 과목 점수를 기록하고 최근 점수 변화를 확인합니다."),
    ("📝 오답 기록", "틀린 문제, 원인, 해결 여부를 기록합니다."),
    ("🎯 현재 예상점수", "최근 성적과 미해결 오답을 반영한 참고 점수를 확인합니다."),
]

for title, description in cards:
    with st.container(border=True):
        st.markdown(f"### {title}")
        st.write(description)

st.info(
    "이 버전은 외부 보조 파일을 불러오지 않으며, requirements.txt에는 Streamlit만 적혀 있어 "
    "Python 버전에 맞는 pandas·PyArrow가 자동으로 설치됩니다."
)
