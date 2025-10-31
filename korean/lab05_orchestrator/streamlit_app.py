import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

import streamlit as st
from PIL import Image

# Ensure repository root is on the import path
REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.append(str(REPO_ROOT))

# 이미지 경로 설정
IMAGES_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "images"))

# 종합 분석 오케스트레이터 import 시도
try:
    from orchestrator.agent import comprehensive_analyzer

    AGENT_AVAILABLE = True
except ImportError as e:
    print(f"Comprehensive Analyzer Agent import 실패: {e}")
    AGENT_AVAILABLE = False

# 키워드 저장 파일 경로
KEYWORDS_FILE = os.path.join(
    os.path.dirname(__file__),
    "orchestrator",
    "sub_agents",
    "keyword_extractor",
    "registered_keywords.txt",
)


def load_keywords() -> List[str]:
    """등록된 키워드 목록 로드"""
    if os.path.exists(KEYWORDS_FILE):
        with open(KEYWORDS_FILE, "r", encoding="utf-8") as f:
            keywords = [line.strip() for line in f if line.strip()]
            return keywords
    return []


def save_keywords(keywords: List[str]):
    """키워드 목록 저장"""
    os.makedirs(os.path.dirname(KEYWORDS_FILE), exist_ok=True)
    with open(KEYWORDS_FILE, "w", encoding="utf-8") as f:
        for keyword in keywords:
            f.write(f"{keyword}\n")


def register_keyword(keyword: str) -> Dict[str, Any]:
    """새로운 키워드 등록"""
    keywords = load_keywords()

    if keyword in keywords:
        return {
            "status": "already_exists",
            "keyword": keyword,
            "total_keywords": len(keywords),
        }

    keywords.append(keyword)
    save_keywords(keywords)

    return {"status": "registered", "keyword": keyword, "total_keywords": len(keywords)}


def extract_keywords_from_highlights(keyword_highlights: List[Dict]) -> List[str]:
    """keyword_highlighted_list에서 키워드 목록 추출"""
    if not keyword_highlights:
        return []
    return [
        item.get("keyword", "") for item in keyword_highlights if item.get("keyword")
    ]


def save_uploaded_image(uploaded_file) -> str:
    """업로드된 이미지를 저장하고 경로 반환"""
    if uploaded_file is None:
        return None

    os.makedirs(IMAGES_DIR, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"uploaded_{timestamp}_{uploaded_file.name}"
    filepath = os.path.join(IMAGES_DIR, filename)

    image = Image.open(uploaded_file)
    image.save(filepath)

    return filepath


st.set_page_config(
    page_title="Lab 05. 종합 리뷰 분석 Agent", page_icon="🔬", layout="wide"
)

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
    .analysis-card {
        background: white;
        border-radius: 12px;
        padding: 16px;
        margin: 12px 0;
        border: 1px solid #e5e7eb;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    .status-approved {
        border-left: 4px solid #10b981;
        background: #ecfdf5;
    }
    .status-rejected {
        border-left: 4px solid #ef4444;
        background: #fef2f2;
    }
    .highlight-box {
        background: #f8fafc;
        border-radius: 8px;
        padding: 12px;
        margin: 8px 0;
        border-left: 3px solid #6366f1;
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
            "content": "이 제품 정말 좋아요! 음질도 훌륭하고 배터리도 오래 갑니다.",
            "timestamp": "2024-01-15 14:30",
            "image": None,
        },
        {
            "id": 2,
            "author": "이영희",
            "rating": 1,
            "content": "완전 쓰레기네요. 돈 아까워요.",
            "timestamp": "2024-01-14 10:20",
            "image": None,
        },
        {
            "id": 3,
            "author": "박철수",
            "rating": 5,
            "content": "별로예요. 기대했는데 실망이에요.",
            "timestamp": "2024-01-13 16:45",
            "image": None,
        },
        {
            "id": 4,
            "author": "최지훈",
            "rating": 4,
            "content": "이어폰 디자인이 깔끔하고 착용감도 편해요. 음질은 가격대비 괜찮은 것 같아요. 아침에 운동할 때 써봤는데 떨어지지도 않고 좋네요!",
            "timestamp": "2024-01-12 09:15",
            "image_path": os.path.join(IMAGES_DIR, "earphone.png"),
        },
        {
            "id": 5,
            "author": "정수연",
            "rating": 3,
            "content": "이어폰 만만세",
            "timestamp": "2024-01-11 16:22",
            "image_path": os.path.join(IMAGES_DIR, "flower.webp"),
        },
    ]

# 종합 분석 결과 저장용 session state
if "comprehensive_analysis_results" not in st.session_state:
    st.session_state.comprehensive_analysis_results = {}

# 키워드 필터 선택 상태
if "selected_keyword_filter" not in st.session_state:
    st.session_state.selected_keyword_filter = None

# 키워드 등록 모달 상태
if "show_keyword_modal" not in st.session_state:
    st.session_state.show_keyword_modal = False

# 분석 진행 중 플래그
if "is_analyzing" not in st.session_state:
    st.session_state.is_analyzing = False

# 메인 콘텐츠 영역
st.header("🔬 Lab 05. 종합 리뷰 분석 시스템")
st.subheader("리뷰에 대한 종합적 분석 시스템 실습")
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
            <div class="rating-card">
                <div class="metric-label"><strong>평균 평점</strong> (총 {total_reviews}개 리뷰)</div>
                <div class="metric-value">{average_rating:.1f} / 5.0</div>
            </div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown("---")

# 키워드 관리 섹션
st.subheader("🏷️ 키워드 관리")

col1, col2 = st.columns([4, 1])

with col1:
    st.write("**등록된 키워드 (클릭하여 필터링)**")
    registered_keywords = load_keywords()

    if registered_keywords:
        cols = st.columns(min(8, len(registered_keywords)))
        for idx, keyword in enumerate(registered_keywords):
            with cols[idx % len(cols)]:
                is_selected = st.session_state.selected_keyword_filter == keyword
                button_type = "primary" if is_selected else "secondary"
                if st.button(
                    f"#{keyword}",
                    key=f"keyword_filter_{keyword}",
                    type=button_type,
                    use_container_width=True,
                ):
                    if st.session_state.selected_keyword_filter == keyword:
                        st.session_state.selected_keyword_filter = None
                    else:
                        st.session_state.selected_keyword_filter = keyword
                    st.rerun()
    else:
        st.info("⚠️ 등록된 키워드가 없습니다. 새 키워드를 등록해주세요!")

with col2:
    if st.button("➕ 새 키워드 등록", type="primary", use_container_width=True):
        st.session_state.show_keyword_modal = True
        st.rerun()

# 키워드 등록 모달
if st.session_state.show_keyword_modal:
    with st.container():
        st.markdown("---")
        st.subheader("➕ 새 키워드 등록")

        with st.form("keyword_form"):
            new_keyword = st.text_input("키워드", placeholder="예: 음질")

            col1, col2 = st.columns([1, 1])
            with col1:
                submit = st.form_submit_button(
                    "🏷️ 등록", type="primary", use_container_width=True
                )
            with col2:
                cancel = st.form_submit_button("❌ 취소", use_container_width=True)

            if submit:
                if new_keyword:
                    try:
                        with st.spinner("키워드 등록 중..."):
                            result = register_keyword(new_keyword)
                            if result.get("status") == "already_exists":
                                st.warning(
                                    f"⚠️ 키워드 '{new_keyword}'는 이미 등록되어 있습니다."
                                )
                            else:
                                st.success(f"✅ 키워드 '{new_keyword}' 등록 완료!")
                                st.session_state.show_keyword_modal = False
                                st.rerun()
                    except Exception as e:
                        st.error(f"❌ 키워드 등록 실패: {str(e)}")
                else:
                    st.error("키워드를 입력해주세요.")

            if cancel:
                st.session_state.show_keyword_modal = False
                st.rerun()

        st.markdown("---")

st.markdown("---")

st.subheader("💬 리뷰 목록 및 종합 분석")

selected_keyword = st.session_state.selected_keyword_filter

for comment in reversed(st.session_state.comments):
    # 키워드 필터링 체크
    show_comment = True
    if selected_keyword:
        if comment["id"] in st.session_state.comprehensive_analysis_results:
            result_data = st.session_state.comprehensive_analysis_results[comment["id"]]
            analysis = result_data.get("analysis_result", {})

            # 검수 통과 여부 확인
            moderation_result = analysis.get("moderation_result", {})
            overall_status = moderation_result.get("overall_status", "FAIL")

            # 검수 통과한 경우에만 키워드 필터링 적용
            if overall_status == "PASS":
                keyword_highlights = analysis.get("keyword_highlighted_list", [])
                keywords = extract_keywords_from_highlights(keyword_highlights)
                show_comment = selected_keyword in keywords
            else:
                show_comment = False
        else:
            show_comment = False

    if not show_comment:
        continue
    with st.container():
        col1, col2, col3, col4 = st.columns([3, 1, 1, 1])

        with col1:
            st.write(f"**{comment['author']}**")

            # 리뷰 내용 하이라이트 처리
            highlighted_content = comment["content"]

            if comment["id"] in st.session_state.comprehensive_analysis_results:
                result_data = st.session_state.comprehensive_analysis_results[
                    comment["id"]
                ]
                analysis = result_data.get("analysis_result", {})

                # 검수 통과 여부 확인
                moderation_result = analysis.get("moderation_result", {})
                overall_status = moderation_result.get("overall_status", "FAIL")

                # 검수 통과한 경우에만 키워드 하이라이트
                if overall_status == "PASS":
                    keyword_highlights = analysis.get("keyword_highlighted_list", [])

                    # 선택된 키워드와 관련된 구문만 하이라이트
                    phrases_to_highlight = []
                    for item in keyword_highlights:
                        item_keyword = item.get("keyword", "")
                        original_phrase = item.get("original_phrase", "")

                        # 선택된 키워드와 일치하거나 선택 없을 때만 하이라이트
                        if (
                            not selected_keyword or item_keyword == selected_keyword
                        ) and original_phrase:
                            phrases_to_highlight.append(original_phrase)

                    # 구문 하이라이트
                    for phrase in phrases_to_highlight:
                        if phrase and phrase in highlighted_content:
                            highlighted_content = highlighted_content.replace(
                                phrase,
                                f'<mark style="background: linear-gradient(135deg, #fff3cd 0%, #ffeaa7 100%); color: #856404; padding: 3px 8px; border-radius: 8px; font-weight: 500; box-shadow: 0 2px 6px rgba(255, 235, 59, 0.3); border: 1px solid #ffeaa7;">{phrase}</mark>',
                            )

            st.markdown(highlighted_content, unsafe_allow_html=True)

            # 발견된 키워드 표시 (검수 통과한 경우에만)
            if comment["id"] in st.session_state.comprehensive_analysis_results:
                result_data = st.session_state.comprehensive_analysis_results[
                    comment["id"]
                ]
                analysis = result_data.get("analysis_result", {})

                # 검수 통과 여부 확인
                moderation_result = analysis.get("moderation_result", {})
                overall_status = moderation_result.get("overall_status", "FAIL")

                # 검수 통과한 경우에만 키워드 표시
                if overall_status == "PASS":
                    keyword_highlights = analysis.get("keyword_highlighted_list", [])
                    keywords = extract_keywords_from_highlights(keyword_highlights)

                    if keywords:
                        keywords_html = ""
                        for kw in keywords:
                            if kw == selected_keyword and selected_keyword:
                                keywords_html += f'<span style="background-color: #ff9800; color: white; padding: 4px 8px; margin: 2px; border-radius: 12px; font-size: 12px; display: inline-block; font-weight: bold;">{kw}</span>'
                            else:
                                keywords_html += f'<span style="background-color: #e1f5fe; color: #01579b; padding: 4px 8px; margin: 2px; border-radius: 12px; font-size: 12px; display: inline-block;">{kw}</span>'
                        st.markdown(
                            f"**발견된 키워드:** {keywords_html}",
                            unsafe_allow_html=True,
                        )

            # 이미지 표시 (image 또는 image_path)
            image_to_display = comment.get("image") or comment.get("image_path")
            if image_to_display:
                st.write("📷 **첨부된 이미지:**")
                try:
                    st.image(image_to_display, width=150)
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
                "🔬 종합분석",
                key=f"comprehensive_analysis_{comment['id']}",
                type="primary",
                use_container_width=True,
                disabled=st.session_state.is_analyzing,
            ):
                if AGENT_AVAILABLE:
                    st.session_state.is_analyzing = True
                    with st.spinner("종합 리뷰 분석 중..."):
                        try:
                            # 리뷰 데이터 준비
                            review_data = {
                                "review_id": comment["id"],
                                "content": comment["content"],
                                "rating": comment["rating"],
                                "author": comment["author"],
                                "timestamp": comment["timestamp"],
                            }

                            # 제품 데이터 준비
                            product_data = {
                                "name": "프리미엄 무선 이어폰",
                                "category": "전자기기",
                            }

                            # 이미지 가져오기
                            pil_image = None
                            if comment.get("image"):
                                pil_image = comment["image"]
                            elif comment.get("image_path"):
                                try:
                                    pil_image = Image.open(comment["image_path"])
                                except Exception as e:
                                    print(f"이미지 로드 실패: {e}")

                            # 종합 분석 실행
                            analysis_result = comprehensive_analyzer(
                                product_data, review_data, pil_image
                            )

                            # 결과를 session state에 저장
                            st.session_state.comprehensive_analysis_results[
                                comment["id"]
                            ] = {
                                "timestamp": datetime.now().strftime(
                                    "%Y-%m-%d %H:%M:%S"
                                ),
                                "analysis_result": analysis_result,
                                "review_data": review_data,
                            }
                            st.session_state.is_analyzing = False
                            st.rerun()

                        except Exception as e:
                            st.session_state.is_analyzing = False
                            import traceback

                            error_details = traceback.format_exc()
                            print(f"=== 종합 분석 에러 디버깅 ===")
                            print(f"에러 메시지: {str(e)}")
                            print(f"상세 스택 트레이스:")
                            print(error_details)
                            print(f"===================")

                            st.error(f"종합 분석 중 오류가 발생했습니다: {str(e)}")
                            with st.expander("상세 에러 정보"):
                                st.code(error_details)
                else:
                    st.warning("종합 분석 에이전트를 사용할 수 없습니다.")

        # 종합 분석 결과가 있으면 표시
        if comment["id"] in st.session_state.comprehensive_analysis_results:
            result_data = st.session_state.comprehensive_analysis_results[comment["id"]]
            analysis = result_data.get("analysis_result", {})

            # ReviewAnalysis 구조에 따른 결과 표시
            moderation_result = analysis.get("moderation_result", {})
            overall_status = moderation_result.get("overall_status", "FAIL")
            is_approved = overall_status == "PASS"

            # 검수 결과에 따른 상태 표시
            if is_approved:
                status_class = "status-approved"
                status_icon = "✅"
                status_text = "검수 통과"
            else:
                status_class = "status-rejected"
                status_icon = "❌"
                status_text = "검수 실패"

            with st.expander(
                f"{status_icon} 종합 분석 결과 - {status_text}", expanded=True
            ):
                # 분석 시간
                st.write(f"**분석 시간:** {result_data['timestamp']}")

                # 1. 검수 결과
                st.markdown("### 1️⃣ 리뷰 검수 결과")

                # 1-1. 욕설/비속어 검사
                profanity_check = moderation_result.get("profanity_check", {})
                if profanity_check:
                    prof_status = profanity_check.get("status", "SKIP")
                    st.markdown(f"**🔍 욕설/비속어 검사:** {prof_status}")
                    st.markdown(f"**사유:** {profanity_check.get('reason', '-')}")
                    st.markdown(
                        f"**신뢰도:** {profanity_check.get('confidence', 0):.2f}"
                    )
                    st.markdown("---")

                # 1-2. 별점-내용 일치성 검사
                rating_check = moderation_result.get("rating_consistency", {})
                if rating_check:
                    rating_status = rating_check.get("status", "SKIP")
                    st.markdown(f"**⭐ 별점-내용 일치성:** {rating_status}")
                    st.markdown(f"**사유:** {rating_check.get('reason', '-')}")
                    st.markdown(f"**신뢰도:** {rating_check.get('confidence', 0):.2f}")
                    st.markdown("---")

                # 1-3. 이미지 매칭 검사
                image_check = moderation_result.get("image_match", {})
                if image_check:
                    image_status = image_check.get("status", "SKIP")
                    st.markdown(f"**📷 이미지 매칭:** {image_status}")
                    st.markdown(f"**사유:** {image_check.get('reason', '-')}")
                    st.markdown(f"**신뢰도:** {image_check.get('confidence', 0):.2f}")
                    st.markdown("---")

                # 전체 검수 결과
                st.markdown(f"**📋 전체 검수 결과:** {status_text} ({overall_status})")
                failed_checks = moderation_result.get("failed_checks", [])
                if failed_checks:
                    st.markdown(f"**실패 항목:** {', '.join(failed_checks)}")

                # 검수 실패 시 이후 단계 생략
                if not is_approved:
                    st.warning(
                        "⚠️ 리뷰가 검수를 통과하지 못하여 이후 분석 단계가 생략되었습니다."
                    )
                else:
                    # 2. 키워드 분석 결과
                    st.markdown("### 2️⃣ 키워드 분석 결과")
                    keyword_highlights = analysis.get("keyword_highlighted_list", [])

                    if keyword_highlights:
                        for highlight in keyword_highlights:
                            keyword = highlight.get("keyword", "")
                            match_type = highlight.get("match_type", "")
                            original_phrase = highlight.get("original_phrase", "")

                            st.markdown(f"**키워드:** `{keyword}` ({match_type} 매칭)")
                            st.markdown("**관련 문장:**")
                            st.markdown(f"• {original_phrase}")
                    else:
                        st.info("추출된 키워드가 없습니다.")

                    # 3. 감정 분석 결과
                    st.markdown("### 3️⃣ 감정 분석 결과")
                    sentiment = analysis.get("sentiment", "정보 없음")

                    # 감정에 따른 색상 및 아이콘
                    if "positive" in sentiment.lower() or "긍정" in sentiment:
                        sentiment_color = "#22c55e"
                        sentiment_icon = "😊"
                        sentiment_text = "긍정"
                    elif "negative" in sentiment.lower() or "부정" in sentiment:
                        sentiment_color = "#ef4444"
                        sentiment_icon = "😞"
                        sentiment_text = "부정"
                    else:
                        sentiment_color = "#6b7280"
                        sentiment_icon = "😐"
                        sentiment_text = "중립"

                    st.markdown(
                        f"{sentiment_icon} **감정:** {sentiment_text} ({sentiment})"
                    )

                    # 4. 자동 응답 결과
                    st.markdown("### 4️⃣ 자동 응답")
                    auto_response = analysis.get("auto_response", "응답 생성 정보 없음")

                    st.markdown("**💬 생성된 셀러 응답:**")
                    # 자동 응답을 박스로 표시
                    response_html = auto_response.replace("\n", "<br>")
                    st.markdown(
                        f'<div style="background: linear-gradient(135deg, #f8fafc 0%, #ffffff 100%); padding: 20px; border-radius: 12px; border: 2px solid #3b82f6; margin-top: 10px; line-height: 1.6;">{response_html}</div>',
                        unsafe_allow_html=True,
                    )

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

        uploaded_image = st.file_uploader(
            "이미지 첨부 (선택사항)",
            type=["png", "jpg", "jpeg"],
            accept_multiple_files=False,
        )

    with col2:
        rating = st.selectbox(
            "평점", [5, 4, 3, 2, 1], format_func=lambda x: f"⭐ {x}점"
        )

    submitted = st.form_submit_button("리뷰 등록", type="primary")

    if submitted:
        if author_name and comment_content:
            # 이미지 처리
            pil_image = None
            if uploaded_image:
                try:
                    pil_image = Image.open(uploaded_image)
                except Exception as e:
                    st.error(f"이미지 처리 중 오류가 발생했습니다: {e}")
                    st.stop()

            new_comment = {
                "id": len(st.session_state.comments) + 1,
                "author": author_name,
                "rating": rating,
                "content": comment_content,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "image": pil_image,
            }
            st.session_state.comments.append(new_comment)
            st.success("리뷰가 등록되었습니다!")

            # 자동 종합 분석 수행 (AGENT_AVAILABLE인 경우)
            if AGENT_AVAILABLE:
                with st.spinner("새 리뷰 자동 종합 분석 중..."):
                    try:
                        # 리뷰 데이터 준비
                        review_data = {
                            "review_id": new_comment["id"],
                            "content": comment_content,
                            "rating": rating,
                            "author": author_name,
                            "timestamp": new_comment["timestamp"],
                        }
                        product_data = {
                            "name": "프리미엄 무선 이어폰",
                            "category": "전자기기",
                        }

                        # 종합 분석 실행
                        analysis_result = comprehensive_analyzer(
                            product_data, review_data, pil_image
                        )

                        # 결과를 session state에 저장
                        st.session_state.comprehensive_analysis_results[
                            new_comment["id"]
                        ] = {
                            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            "analysis_result": analysis_result,
                            "review_data": review_data,
                        }

                        st.success("자동 종합 분석이 완료되었습니다!")

                    except Exception as e:
                        st.error(f"자동 종합 분석 중 오류가 발생했습니다: {str(e)}")

            st.rerun()
        else:
            st.error("작성자명과 리뷰 내용을 모두 입력해주세요.")

st.markdown("---")
