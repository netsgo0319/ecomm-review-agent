from datetime import datetime

import streamlit as st
from sentiment_analyzer.agent import analyze_sentiment

st.set_page_config(page_title="Lab 01. 감정 분석 Agent", page_icon="🛍️", layout="wide")

st.markdown(
    """
    <style>
    .main > div {
        padding-top: 1rem;
    }
    h1 {
        font-size: 1.8rem !important;
        margin-bottom: 0.5rem !important;
        margin-top: 0 !important;
    }
    .product-rating-container {
        background: linear-gradient(135deg, #eef2ff 0%, #f5f7ff 100%);
        border: 1px solid #dbe3ff;
        border-radius: 18px;
        padding: 20px 24px;
        margin-bottom: 20px;
        box-shadow: 0 14px 34px rgba(99, 102, 241, 0.12);
    }
    .product-rating-grid {
        display: grid;
        grid-template-columns: 2fr 1fr;
        gap: 32px;
        align-items: start;
    }
    .product-rating-container h3 {
        margin: 0 0 16px 0;
    }
    .product-rating-container p {
        margin: 4px 0;
        color: #1f2937;
    }
    .rating-card {
        background-color: #fff;
        border-radius: 14px;
        padding: 20px 24px;
        border: 1px solid rgba(99, 102, 241, 0.15);
        box-shadow: inset 0 0 0 1px rgba(99, 102, 241, 0.04);
    }
    .rating-card .metric-label {
        font-size: 14px;
        color: #64748b;
        margin-bottom: 4px;
    }
    .rating-card .metric-value {
        font-size: 36px;
        font-weight: 700;
        color: #4f46e5;
        margin-bottom: 8px;
    }
    .rating-card .metric-description {
        font-size: 14px;
        color: #475569;
    }
    .keyword-badges {
        margin-top: 24px;
    }
    .keyword-badges h3 {
        margin-bottom: 12px;
    }
    .keyword-badge {
        display: inline-flex;
        align-items: center;
        padding: 6px 12px;
        border-radius: 999px;
        background-color: rgba(79, 70, 229, 0.12);
        color: #4338ca;
        font-size: 13px;
        margin-right: 8px;
        margin-bottom: 8px;
        font-weight: 500;
        letter-spacing: -0.01em;
    }
    .keyword-badge::before {
        content: "#";
        margin-right: 2px;
    }
    @media (max-width: 1024px) {
        .product-rating-grid {
            grid-template-columns: 1fr;
        }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

if "comments" not in st.session_state:
    st.session_state.comments = [
        {
            "id": 1,
            "author": "김민수",
            "rating": 5,
            "content": "이어폰 디자인이 깔끔하고 착용감도 편해요. 음질은 가격대비 그냥저냥 괜찮은 것 같아요. 아침에 운동할 때 써봤는데 떨어지지도 않고 좋네요!",
            "timestamp": "2024-01-15 14:30",
        },
        {
            "id": 2,
            "author": "이영희",
            "rating": 5,
            "content": "제품 정말 좋아요! 음질도 훌륭하고 배터리도 오래 갑니다.",
            "timestamp": "2024-01-14 10:20",
        },
        {
            "id": 3,
            "author": "박철수",
            "rating": 3,
            "content": "쏘쏘. 배송은 빨라서 좋았던듯",
            "timestamp": "2024-01-13 16:45",
        },
        {
            "id": 4,
            "author": "최지훈",
            "rating": 1,
            "content": "진짜 대~~~~~박 입니다!^^ 돈을 땅에 버리고 싶은 사람이라면 꼭 사시길",
            "timestamp": "2024-01-12 09:15",
        },
        {
            "id": 5,
            "author": "정수연",
            "rating": 3,
            "content": "생각보다 별로예요. 가성비 좋다고해서 기대했는데... 이 가격이면 다른거 사세요",
            "timestamp": "2024-01-11 16:22",
        },
    ]

# 감정 분석 결과 저장용 session state
if "sentiment_analysis_results" not in st.session_state:
    st.session_state.sentiment_analysis_results = {}


# 감정 분석 결과 저장 헬퍼 함수
def save_sentiment_result(comment_id, content, sentiment_result):
    """감정 분석 결과를 세션 상태에 저장"""
    sentiment_data = sentiment_result["sentiment_result"]

    result_dict = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "label": sentiment_data.get("sentiment", "neutral"),
        "score": sentiment_data.get("score", 0.5),
        "confidence": sentiment_data.get("confidence", 0.5),
        "rationale": sentiment_data.get("reason", "분석 근거 없음"),
        "review_text": content,
        "raw_response": sentiment_result.get("raw_response", ""),
    }

    if not sentiment_result["success"]:
        result_dict["confidence"] = 0.3
        result_dict["rationale"] = "분석 오류"
        result_dict["error"] = sentiment_result.get("error", "")

    st.session_state.sentiment_analysis_results[comment_id] = result_dict
    return sentiment_result["success"]


# 별점 HTML 생성 함수
def generate_stars_html(rating):
    """별점 HTML을 생성"""
    stars = ""
    for i in range(5):
        if i < rating:
            stars += '<span style="color: #fbbf24; font-size: 18px;">★</span>'
        else:
            stars += '<span style="color: #d1d5db; font-size: 18px;">★</span>'
    return stars


# 감정 아이콘 및 색상 가져오기 함수
def get_sentiment_style(label):
    """감정에 따른 아이콘과 색상 반환"""
    if label in ["긍정", "positive"]:
        return "😊", "#22c55e"
    elif label in ["부정", "negative"]:
        return "😞", "#ef4444"
    else:
        return "😐", "#6b7280"


# 메인 콘텐츠 영역
st.header("🛍️ Lab 01. 리뷰 감정 분석 시스템")
st.subheader("한국어 리뷰의 감정 분석 시스템 실습")
st.markdown("---")

total_reviews = len(st.session_state.comments)
total_rating = sum([comment["rating"] for comment in st.session_state.comments])
average_rating = total_rating / total_reviews if total_reviews else 0

st.subheader("📦 상품 정보")
# <h3 style="color:black">📦 상품 정보</h3>
st.markdown(
    f"""
    <div class="product-rating-container">
        <div class="product-rating-grid">
            <div>
                <p><strong>상품명:</strong> 프리미엄 무선 이어폰</p>
                <p><strong>가격:</strong> 89,000원</p>
                <p><strong>상품 설명:</strong></p>
                <p>고품질 사운드와 긴 배터리 수명을 자랑하는 프리미엄 무선 이어폰입니다. 노이즈 캔슬링 기능과 편안한 착용감을 제공합니다.</p>
            </div>
            <div>
                <div class="rating-card">
                    <div class="metric-label"><strong>평균 평점</strong> (총 {total_reviews}개 리뷰)</div>
                    <div class="metric-value">{average_rating:.1f} / 5.0</div>
                </div>
            </div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.subheader("💬 댓글 목록")

for comment in reversed(st.session_state.comments):
    with st.container():
        col1, col2, col3, col4 = st.columns([3, 1, 1, 1])

        with col1:
            st.write(f"**{comment['author']}**")
            st.write(comment["content"])

        with col2:
            # 별점 표시
            st.markdown(generate_stars_html(comment["rating"]), unsafe_allow_html=True)
            st.caption(f"{comment['rating']}/5")

        with col3:
            st.caption(comment["timestamp"])

        with col4:
            # 이미 분석된 리뷰인지 확인
            is_analyzed = comment["id"] in st.session_state.sentiment_analysis_results
            button_text = "✅ 분석완료" if is_analyzed else "😍 감정분석"
            button_disabled = is_analyzed

            if st.button(
                button_text,
                key=f"review_{comment['id']}",
                type="secondary" if is_analyzed else "primary",
                use_container_width=True,
                disabled=button_disabled,
            ):
                with st.spinner("감정 분석 중..."):
                    try:
                        sentiment_result = analyze_sentiment(comment["content"])
                        success = save_sentiment_result(
                            comment["id"], comment["content"], sentiment_result
                        )

                        if success:
                            st.success("✅ 분석 완료!")
                        else:
                            st.warning(
                                "⚠️ 분석 중 오류가 발생했지만 폴백 결과를 저장했습니다."
                            )
                        st.rerun()

                    except Exception as e:
                        st.error(f"감정 분석 중 오류가 발생했습니다: {str(e)}")

        # 감정 분석 결과가 있으면 펼치기/접기 메뉴 표시
        if comment["id"] in st.session_state.sentiment_analysis_results:
            sentiment_result = st.session_state.sentiment_analysis_results[
                comment["id"]
            ]
            label = sentiment_result.get("label", "중립")
            score = sentiment_result.get("score", 0.5)
            confidence = sentiment_result.get("confidence", 0.5)

            # 감정에 따른 아이콘과 색상
            status_icon, status_color = get_sentiment_style(label)

            with st.expander(
                f"{status_icon} 감정분석 결과 - {label} ({score:.3f})", expanded=False
            ):
                # 분석 시간
                st.write(f"**분석 시간:** {sentiment_result['timestamp']}")

                # 감정 분석 결과
                col1, col2 = st.columns([1, 2])
                with col1:
                    st.markdown(
                        f"<div style='text-align: center; padding: 20px; background-color: {status_color}15; border-radius: 10px; border: 2px solid {status_color}40;'>"
                        f"<div style='font-size: 48px;'>{status_icon}</div>"
                        f"<div style='font-size: 24px; font-weight: bold; color: {status_color}; margin-top: 10px;'>{label}</div>"
                        f"<div style='font-size: 16px; color: {status_color}; margin-top: 5px;'>점수: {score:.3f}</div>"
                        f"</div>",
                        unsafe_allow_html=True,
                    )

                with col2:
                    st.write("**분석 근거:**")
                    st.write(sentiment_result.get("rationale", "근거 없음"))

                    st.write("**신뢰도:**")
                    st.write(f"{confidence:.2f} / 1.00")

                # 오류 정보 (있는 경우)
                if "error" in sentiment_result and sentiment_result["error"]:
                    st.error(f"분석 중 오류: {sentiment_result['error']}")

                # 에이전트 디버깅 정보
                if (
                    "raw_response" in sentiment_result
                    and sentiment_result["raw_response"]
                ):
                    with st.expander("에이전트 디버깅 정보", expanded=False):
                        st.write("**에이전트 원본 응답:**")
                        st.code(
                            sentiment_result.get("raw_response", "응답 없음"),
                            language="text",
                        )

        st.markdown("---")

st.markdown("---")

st.subheader("✍️ 새 댓글 작성")

with st.form("comment_form"):
    col1, col2 = st.columns([3, 1])

    with col1:
        author_name = st.text_input("작성자명", placeholder="이름을 입력하세요")
        comment_content = st.text_area(
            "댓글 내용", placeholder="상품에 대한 의견을 남겨주세요", height=100
        )

    with col2:
        rating = st.selectbox(
            "평점", [5, 4, 3, 2, 1], format_func=lambda x: f"⭐ {x}점"
        )

    submitted = st.form_submit_button("댓글 등록", type="primary")

    if submitted:
        if author_name and comment_content:
            new_comment = {
                "id": len(st.session_state.comments) + 1,
                "author": author_name,
                "rating": rating,
                "content": comment_content,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
            }
            st.session_state.comments.append(new_comment)
            st.success("댓글이 등록되었습니다!")
            st.rerun()
        else:
            st.error("작성자명과 댓글 내용을 모두 입력해주세요.")

st.markdown("---")
