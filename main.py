import streamlit as st

st.set_page_config(page_title="시험 계획표", page_icon="📚", layout="wide")

SUBJECTS = ["국어", "수학", "영어", "과학", "사회"]


def init_state():
    defaults = {
        "mock_scores": [],
        "wrong_questions": [],
        "study_plan": [],
    }
    for key, value in defaults.items():
        if key not in st.session_state or not isinstance(st.session_state[key], list):
            st.session_state[key] = value.copy()


def unresolved_counts():
    counts = {subject: 0 for subject in SUBJECTS}
    for item in st.session_state.wrong_questions:
        subject = item.get("과목")
        if subject in counts and not bool(item.get("해결", False)):
            counts[subject] += 1
    return counts


def expected_score(subject):
    records = sorted(
        st.session_state.mock_scores,
        key=lambda item: str(item.get("날짜", "")),
    )
    values = []
    for item in records:
        value = item.get(subject)
        if isinstance(value, (int, float)):
            values.append(float(value))

    recent = values[-3:]
    average = sum(recent) / len(recent) if recent else 70.0
    trend = recent[-1] - recent[-2] if len(recent) >= 2 else 0.0
    penalty = min(12.0, unresolved_counts()[subject] * 0.8)
    return max(0.0, min(100.0, average + trend * 0.35 - penalty))


init_state()

st.title("📚 나만의 시험 계획표")
st.caption("모의고사 성적과 오답을 바탕으로 과목을 연속 배정하는 시험 대비 사이트입니다.")

unsolved_total = sum(1 for item in st.session_state.wrong_questions if not bool(item.get("해결", False)))
predictions = [expected_score(subject) for subject in SUBJECTS]

col1, col2, col3, col4 = st.columns(4)
col1.metric("모의고사 기록", f"{len(st.session_state.mock_scores)}회")
col2.metric("전체 오답", f"{len(st.session_state.wrong_questions)}문제")
col3.metric("미해결 오답", f"{unsolved_total}문제")
col4.metric("평균 예상점수", f"{sum(predictions) / len(predictions):.1f}점")

st.divider()
st.subheader("페이지 안내")

cards = [
    ("🗓️ 날짜별 계획표", "시험 기간과 연속 학습 일수를 설정해 달력형 계획표를 만듭니다."),
    ("📊 모의고사 성적", "시험별 과목 점수를 입력하고 최근 점수 변화를 확인합니다."),
    ("📝 오답 기록", "틀린 문제와 원인을 기록하고 해결 여부를 관리합니다."),
    ("🎯 현재 예상점수", "최근 성적과 미해결 오답을 반영한 참고 점수를 확인합니다."),
]

for title, description in cards:
    with st.container(border=True):
        st.markdown(f"### {title}")
        st.write(description)

st.info("입력한 자료는 같은 브라우저 세션의 여러 페이지에서 공유됩니다. 브라우저 세션이 완전히 종료되면 초기화될 수 있습니다.")
