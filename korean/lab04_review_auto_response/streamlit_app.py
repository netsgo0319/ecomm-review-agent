import base64
import json
import os
import sys
from datetime import datetime
from io import BytesIO

import streamlit as st
from PIL import Image

sys.path.append(".")

# 자동답변 에이전트 import 시도
try:
    import sys

    from auto_response.agent import generate_auto_response

    AGENT_AVAILABLE = True
except ImportError as e:
    print(f"Auto Response Agent import 실패: {e}")
    AGENT_AVAILABLE = False

st.set_page_config(page_title="Lab04. 답글 생성 Agent", page_icon="🛍️", layout="wide")

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
    @media (max-width: 1024px) {
        .product-rating-grid {
            grid-template-columns: 1fr;
        }
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def image_to_base64(image):
    buffered = BytesIO()
    image.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode()
    return img_str


def base64_to_image(img_str):
    img_data = base64.b64decode(img_str)
    img = Image.open(BytesIO(img_data))
    return img


if "comments" not in st.session_state:
    # 이미지 미리 로드
    flower_img_base64 = ""
    earphone_img_base64 = ""

    try:
        flower_img = Image.open("images/flower.webp")
        flower_img.thumbnail((800, 600), Image.Resampling.LANCZOS)
        flower_img_base64 = image_to_base64(flower_img)
    except:
        pass

    try:
        earphone_img = Image.open("images/earphone.png")
        earphone_img.thumbnail((800, 600), Image.Resampling.LANCZOS)
        earphone_img_base64 = image_to_base64(earphone_img)
    except:
        pass

    st.session_state.comments = [
        {
            "id": 1,
            "author": "김민수",
            "rating": 5,
            "content": "이 제품 정말 좋아요! 음질도 훌륭하고 배터리도 오래 갑니다. 가격대비 성능이 훌륭하네요.",
            "timestamp": "2024-01-15 14:30",
            "images": [],
        },
        {
            "id": 2,
            "author": "이영희",
            "rating": 2,
            "content": "배송이 너무 늦어요. 언제 받을 수 있나요? 주문한 지 일주일이 넘었는데 아직도 배송 준비 중이라고 나오네요.",
            "timestamp": "2024-01-14 10:20",
            "images": [],
        },
        {
            "id": 3,
            "author": "박철수",
            "rating": 1,
            "content": "제품에 하자가 있어서 환불하고 싶은데 어떻게 해야 하나요? 고객센터 연락도 안 되고 답답합니다.",
            "timestamp": "2024-01-13 16:45",
            "images": [],
        },
        {
            "id": 4,
            "author": "최지은",
            "rating": 4,
            "content": "전체적으로 만족하는데 색상이 사진과 조금 달라요. 그래도 품질은 좋습니다!",
            "timestamp": "2024-01-12 11:15",
            "images": [],
        },
    ]

# 자동답변 결과 저장용 session state
if "auto_responses" not in st.session_state:
    st.session_state.auto_responses = {}

# 메인 콘텐츠 영역
st.header("🛍️ Lab 04. 리뷰 자동답변 시스템")
st.subheader("고객 리뷰에 대해 셀러의 답변을 자동으로 하는 시스템 실습")
st.markdown("---")

total_reviews = len(st.session_state.comments)
total_rating = sum([comment["rating"] for comment in st.session_state.comments])
average_rating = total_rating / total_reviews if total_reviews else 0

st.subheader("📦 상품 정보")
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

st.subheader("💬 리뷰 목록")

for comment in reversed(st.session_state.comments):
    with st.container():
        col1, col2, col3, col4 = st.columns([3, 1, 1, 1])

        with col1:
            st.write(f"**{comment['author']}**")
            st.write(comment["content"])

            if "images" in comment and comment["images"]:
                st.write("📷 **첨부된 이미지:**")
                img_cols = st.columns(min(len(comment["images"]), 3))
                for idx, img_str in enumerate(comment["images"]):
                    with img_cols[idx % 3]:
                        try:
                            img = base64_to_image(img_str)
                            st.image(img, width=150, caption=f"이미지 {idx+1}")
                        except Exception as e:
                            st.error(f"이미지를 불러올 수 없습니다: {e}")

        with col2:
            # 통일된 스타일의 별점 표시
            stars_html = ""
            for i in range(5):
                if i < comment["rating"]:
                    stars_html += (
                        '<span style="color: #fbbf24; font-size: 18px;">★</span>'
                    )
                else:
                    stars_html += (
                        '<span style="color: #d1d5db; font-size: 18px;">★</span>'
                    )

            st.markdown(stars_html, unsafe_allow_html=True)
            st.caption(f"{comment['rating']}/5")

        with col3:
            st.caption(comment["timestamp"])

        with col4:
            if st.button(
                "💬 자동답변",
                key=f"review_{comment['id']}",
                type="primary",
                use_container_width=True,
            ):
                if AGENT_AVAILABLE:
                    with st.spinner("자동답변 생성 중..."):
                        try:
                            # 자동답변 생성 실행
                            agent_result = generate_auto_response(comment["content"])

                            # 자동답변 결과를 comment별로 저장
                            st.session_state.auto_responses[comment["id"]] = {
                                "timestamp": datetime.now().strftime(
                                    "%Y-%m-%d %H:%M:%S"
                                ),
                                "response": agent_result["response"],
                                "tool_result": agent_result["tool_results"],
                                "review_text": comment["content"],
                                "success": True,
                            }

                        except Exception as e:
                            import traceback

                            error_details = traceback.format_exc()
                            print(f"=== 자동답변 생성 에러 디버깅 ===")
                            print(f"에러 메시지: {str(e)}")
                            print(f"상세 스택 트레이스:")
                            print(error_details)
                            print(f"===================")

                            st.error(f"자동답변 생성 중 오류가 발생했습니다: {str(e)}")
                            with st.expander("상세 에러 정보"):
                                st.code(error_details)

                            # 에러 정보도 저장
                            st.session_state.auto_responses[comment["id"]] = {
                                "timestamp": datetime.now().strftime(
                                    "%Y-%m-%d %H:%M:%S"
                                ),
                                "response": f"답변 생성 중 오류가 발생했습니다: {str(e)}",
                                "tool_result": [],
                                "review_text": comment["content"],
                                "success": False,
                                "error": str(e),
                            }
                else:
                    st.warning("자동답변 에이전트를 사용할 수 없습니다.")

        # 자동답변 결과가 있으면 펼치기/접기 메뉴 표시
        if comment["id"] in st.session_state.auto_responses:
            auto_response = st.session_state.auto_responses[comment["id"]]
            success = auto_response.get("success", True)

            # 성공/실패에 따른 아이콘 선택
            if success:
                status_icon = "✅"
                status_color = "#22c55e"
                status_text = "자동답변 생성 완료"
            else:
                status_icon = "❌"
                status_color = "#ef4444"
                status_text = "자동답변 생성 실패"

            with st.expander(f"{status_icon} {status_text}", expanded=True):
                # 답변 생성 시간
                st.write(f"**생성 시간:** {auto_response['timestamp']}")

                # 자동답변 내용
                st.write("**🏬 셀러 답변:**")
                response_content = auto_response.get(
                    "response", "답변을 생성할 수 없습니다."
                )
                # 답변을 예쁘게 표시
                st.markdown(
                    f"""
                    <div style='background-color: #f8fafc; padding: 20px; border-radius: 10px; border-left: 4px solid #3b82f6; margin: 10px 0;'>
                        <div style='color: #1e40af; font-weight: 500; margin-bottom: 8px;'>셀러 답변:</div>
                        <div style='color: #374151; line-height: 1.6;'>{response_content}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                # Tool 호출 결과 표시
                tool_results = auto_response.get("tool_result", [])
                if tool_results:
                    with st.expander(
                        f"🔧 도구 사용 결과 ({len(tool_results)}개)", expanded=False
                    ):
                        import json

                        for idx, tool_info in enumerate(tool_results):
                            st.write(f"**도구 {idx+1} 결과:**")
                            # JSON 형태로 예쁘게 표시
                            st.json(tool_info)

                            if idx < len(tool_results) - 1:
                                st.divider()
                else:
                    st.info("🔧 이 답변에는 도구 사용 정보가 없습니다.")

                # 오류 정보 (있는 경우)
                if not success and "error" in auto_response:
                    st.error(f"생성 중 오류: {auto_response['error']}")

        st.markdown("---")

st.markdown("---")

st.subheader("✍️ 새 리뷰 작성")

with st.form("comment_form"):
    col1, col2 = st.columns([3, 1])

    with col1:
        author_name = st.text_input("작성자명", placeholder="이름을 입력하세요")
        comment_content = st.text_area(
            "리뷰 내용", placeholder="상품에 대한 의견을 남겨주세요", height=100
        )

    with col2:
        rating = st.selectbox(
            "평점", [5, 4, 3, 2, 1], format_func=lambda x: f"⭐ {x}점"
        )

    submitted = st.form_submit_button("리뷰 등록", type="primary")

    if submitted:
        if author_name and comment_content:
            new_comment = {
                "id": len(st.session_state.comments) + 1,
                "author": author_name,
                "rating": rating,
                "content": comment_content,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "images": [],
            }
            st.session_state.comments.append(new_comment)
            st.success("리뷰가 등록되었습니다!")

            # 자동 답변 생성 수행 (AGENT_AVAILABLE인 경우)
            if AGENT_AVAILABLE:
                with st.spinner("새 리뷰 자동답변 생성 중..."):
                    try:
                        # 자동답변 생성 실행
                        agent_result = generate_auto_response(comment_content)

                        # agent_result는 이미 response와 tool_result가 포함된 문자열이므로
                        # JSON으로 파싱하거나 직접 사용
                        import json

                        try:
                            # JSON 파싱 시도
                            parsed_result = json.loads(str(agent_result))
                            response_text = parsed_result.get(
                                "response", str(agent_result)
                            )
                            tool_results = parsed_result.get("tool_results", [])
                        except:
                            # JSON 파싱 실패시 전체를 response로 사용
                            response_text = str(agent_result)
                            tool_results = []

                        # 자동답변 결과를 comment별로 저장
                        st.session_state.auto_responses[new_comment["id"]] = {
                            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            "response": response_text,
                            "tool_result": tool_results,
                            "review_text": comment_content,
                            "success": True,
                        }

                    except Exception as e:
                        st.error(f"자동답변 생성 중 오류가 발생했습니다: {str(e)}")

            st.rerun()
        else:
            st.error("작성자명과 리뷰 내용을 모두 입력해주세요.")

st.markdown("---")
