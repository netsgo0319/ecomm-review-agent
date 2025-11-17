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

# Image path configuration
IMAGES_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "images"))

# Attempt to import comprehensive analyzer orchestrator
try:
    from orchestrator.agent import comprehensive_analyzer

    AGENT_AVAILABLE = True
except ImportError as e:
    print(f"Comprehensive Analyzer Agent import failed: {e}")
    AGENT_AVAILABLE = False

# Keyword storage file path
KEYWORDS_FILE = os.path.join(
    os.path.dirname(__file__),
    "orchestrator",
    "sub_agents",
    "keyword_extractor",
    "registered_keywords.txt",
)


def load_keywords() -> List[str]:
    """Load registered keyword list"""
    if os.path.exists(KEYWORDS_FILE):
        with open(KEYWORDS_FILE, "r", encoding="utf-8") as f:
            keywords = [line.strip() for line in f if line.strip()]
            return keywords
    return []


def save_keywords(keywords: List[str]):
    """Save keyword list"""
    os.makedirs(os.path.dirname(KEYWORDS_FILE), exist_ok=True)
    with open(KEYWORDS_FILE, "w", encoding="utf-8") as f:
        for keyword in keywords:
            f.write(f"{keyword}\n")


def register_keyword(keyword: str) -> Dict[str, Any]:
    """Register new keyword"""
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
    """Extract keyword list from keyword_highlighted_list"""
    if not keyword_highlights:
        return []
    return [
        item.get("keyword", "") for item in keyword_highlights if item.get("keyword")
    ]


def save_uploaded_image(uploaded_file) -> str:
    """Save uploaded image and return path"""
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
    page_title="Lab 05. Comprehensive Review Analysis Agent", page_icon="🔬", layout="wide"
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
            "author": "Kim Minsu",
            "rating": 5,
            "content": "This product is really great! The sound quality is excellent and the battery lasts long.",
            "timestamp": "2024-01-15 14:30",
            "image": None,
        },
        {
            "id": 2,
            "author": "Lee Younghee",
            "rating": 1,
            "content": "Total garbage. Waste of money.",
            "timestamp": "2024-01-14 10:20",
            "image": None,
        },
        {
            "id": 3,
            "author": "Park Chulsoo",
            "rating": 5,
            "content": "Not great. I had high expectations but I'm disappointed.",
            "timestamp": "2024-01-13 16:45",
            "image": None,
        },
        {
            "id": 4,
            "author": "Choi Jihoon",
            "rating": 4,
            "content": "The earphone design is clean and they're comfortable to wear. The sound quality seems decent for the price. I tried them during my morning workout and they didn't fall out, which is great!",
            "timestamp": "2024-01-12 09:15",
            "image_path": os.path.join(IMAGES_DIR, "earphone.png"),
        },
        {
            "id": 5,
            "author": "Jung Sooyeon",
            "rating": 3,
            "content": "Earphones hooray",
            "timestamp": "2024-01-11 16:22",
            "image_path": os.path.join(IMAGES_DIR, "flower.webp"),
        },
    ]

# Session state for storing comprehensive analysis results
if "comprehensive_analysis_results" not in st.session_state:
    st.session_state.comprehensive_analysis_results = {}

# Keyword filter selection state
if "selected_keyword_filter" not in st.session_state:
    st.session_state.selected_keyword_filter = None

# Keyword registration modal state
if "show_keyword_modal" not in st.session_state:
    st.session_state.show_keyword_modal = False

# Analysis in progress flag
if "is_analyzing" not in st.session_state:
    st.session_state.is_analyzing = False

# Main content area
st.header("🔬 Lab 05. Comprehensive Review Analysis System")
st.subheader("Comprehensive Analysis System for Reviews")
st.markdown("---")

total_reviews = len(st.session_state.comments)
total_rating = sum([comment["rating"] for comment in st.session_state.comments])
average_rating = total_rating / total_reviews if total_reviews else 0

st.subheader("📦 Product Information")
st.markdown(
    f"""
    <div class="product-rating-container">
        <div class="product-rating-grid">
            <div>
                <p><strong>Product Name:</strong> Premium Wireless Earphones</p>
                <p><strong>Price:</strong> $89.00</p>
                <p><strong>Product Description:</strong></p>
                <p>Premium wireless earphones featuring high-quality sound and long battery life. Offers noise canceling functionality and comfortable fit.</p>
            </div>
            <div class="rating-card">
                <div class="metric-label"><strong>Average Rating</strong> (Total {total_reviews} reviews)</div>
                <div class="metric-value">{average_rating:.1f} / 5.0</div>
            </div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown("---")

# Keyword management section
st.subheader("🏷️ Keyword Management")

col1, col2 = st.columns([4, 1])

with col1:
    st.write("**Registered Keywords (Click to filter)**")
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
        st.info("⚠️ No registered keywords. Please register new keywords!")

with col2:
    if st.button("➕ Register New Keyword", type="primary", use_container_width=True):
        st.session_state.show_keyword_modal = True
        st.rerun()

# Keyword registration modal
if st.session_state.show_keyword_modal:
    with st.container():
        st.markdown("---")
        st.subheader("➕ Register New Keyword")

        with st.form("keyword_form"):
            new_keyword = st.text_input("Keyword", placeholder="e.g., sound quality")

            col1, col2 = st.columns([1, 1])
            with col1:
                submit = st.form_submit_button(
                    "🏷️ Register", type="primary", use_container_width=True
                )
            with col2:
                cancel = st.form_submit_button("❌ Cancel", use_container_width=True)

            if submit:
                if new_keyword:
                    try:
                        with st.spinner("Registering keyword..."):
                            result = register_keyword(new_keyword)
                            if result.get("status") == "already_exists":
                                st.warning(
                                    f"⚠️ Keyword '{new_keyword}' is already registered."
                                )
                            else:
                                st.success(f"✅ Keyword '{new_keyword}' registered successfully!")
                                st.session_state.show_keyword_modal = False
                                st.rerun()
                    except Exception as e:
                        st.error(f"❌ Keyword registration failed: {str(e)}")
                else:
                    st.error("Please enter a keyword.")

            if cancel:
                st.session_state.show_keyword_modal = False
                st.rerun()

        st.markdown("---")

st.markdown("---")

st.subheader("💬 Review List and Comprehensive Analysis")

selected_keyword = st.session_state.selected_keyword_filter

for comment in reversed(st.session_state.comments):
    # Check keyword filtering
    show_comment = True
    if selected_keyword:
        if comment["id"] in st.session_state.comprehensive_analysis_results:
            result_data = st.session_state.comprehensive_analysis_results[comment["id"]]
            analysis = result_data.get("analysis_result", {})

            # Check if moderation passed
            moderation_result = analysis.get("moderation_result", {})
            overall_status = moderation_result.get("overall_status", "FAIL")

            # Apply keyword filtering only if moderation passed
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

            # Highlight review content
            highlighted_content = comment["content"]

            if comment["id"] in st.session_state.comprehensive_analysis_results:
                result_data = st.session_state.comprehensive_analysis_results[
                    comment["id"]
                ]
                analysis = result_data.get("analysis_result", {})

                # Check if moderation passed
                moderation_result = analysis.get("moderation_result", {})
                overall_status = moderation_result.get("overall_status", "FAIL")

                # Highlight keywords only if moderation passed
                if overall_status == "PASS":
                    keyword_highlights = analysis.get("keyword_highlighted_list", [])

                    # Highlight only phrases related to selected keyword
                    phrases_to_highlight = []
                    for item in keyword_highlights:
                        item_keyword = item.get("keyword", "")
                        original_phrase = item.get("original_phrase", "")

                        # Highlight only if it matches selected keyword or no keyword selected
                        if (
                            not selected_keyword or item_keyword == selected_keyword
                        ) and original_phrase:
                            phrases_to_highlight.append(original_phrase)

                    # Apply phrase highlighting
                    for phrase in phrases_to_highlight:
                        if phrase and phrase in highlighted_content:
                            highlighted_content = highlighted_content.replace(
                                phrase,
                                f'<mark style="background: linear-gradient(135deg, #fff3cd 0%, #ffeaa7 100%); color: #856404; padding: 3px 8px; border-radius: 8px; font-weight: 500; box-shadow: 0 2px 6px rgba(255, 235, 59, 0.3); border: 1px solid #ffeaa7;">{phrase}</mark>',
                            )

            st.markdown(highlighted_content, unsafe_allow_html=True)

            # Display found keywords (only if moderation passed)
            if comment["id"] in st.session_state.comprehensive_analysis_results:
                result_data = st.session_state.comprehensive_analysis_results[
                    comment["id"]
                ]
                analysis = result_data.get("analysis_result", {})

                # Check if moderation passed
                moderation_result = analysis.get("moderation_result", {})
                overall_status = moderation_result.get("overall_status", "FAIL")

                # Display keywords only if moderation passed
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
                            f"**Found Keywords:** {keywords_html}",
                            unsafe_allow_html=True,
                        )

            # Display image (image or image_path)
            image_to_display = comment.get("image") or comment.get("image_path")
            if image_to_display:
                st.write("📷 **Attached Image:**")
                try:
                    st.image(image_to_display, width=150)
                except Exception as e:
                    st.error(f"Unable to load image: {e}")

        with col2:
            # Display uniform style rating stars
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
                "🔬 Analyze",
                key=f"comprehensive_analysis_{comment['id']}",
                type="primary",
                use_container_width=True,
                disabled=st.session_state.is_analyzing,
            ):
                if AGENT_AVAILABLE:
                    st.session_state.is_analyzing = True
                    with st.spinner("Analyzing review comprehensively..."):
                        try:
                            # Prepare review data
                            review_data = {
                                "review_id": comment["id"],
                                "content": comment["content"],
                                "rating": comment["rating"],
                                "author": comment["author"],
                                "timestamp": comment["timestamp"],
                            }

                            # Prepare product data
                            product_data = {
                                "name": "Premium Wireless Earphones",
                                "category": "Electronics",
                            }

                            # Get image
                            pil_image = None
                            if comment.get("image"):
                                pil_image = comment["image"]
                            elif comment.get("image_path"):
                                try:
                                    pil_image = Image.open(comment["image_path"])
                                except Exception as e:
                                    print(f"Image load failed: {e}")

                            # Execute comprehensive analysis
                            analysis_result = comprehensive_analyzer(
                                product_data, review_data, pil_image
                            )

                            # Save results to session state
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
                            print(f"=== Comprehensive Analysis Error Debug ===")
                            print(f"Error message: {str(e)}")
                            print(f"Detailed stack trace:")
                            print(error_details)
                            print(f"===================")

                            st.error(f"An error occurred during comprehensive analysis: {str(e)}")
                            with st.expander("Detailed Error Information"):
                                st.code(error_details)
                else:
                    st.warning("Comprehensive analysis agent is not available.")

        # Display comprehensive analysis results if available
        if comment["id"] in st.session_state.comprehensive_analysis_results:
            result_data = st.session_state.comprehensive_analysis_results[comment["id"]]
            analysis = result_data.get("analysis_result", {})

            # Display results according to ReviewAnalysis structure
            moderation_result = analysis.get("moderation_result", {})
            overall_status = moderation_result.get("overall_status", "FAIL")
            is_approved = overall_status == "PASS"

            # Display status based on moderation result
            if is_approved:
                status_class = "status-approved"
                status_icon = "✅"
                status_text = "Moderation Passed"
            else:
                status_class = "status-rejected"
                status_icon = "❌"
                status_text = "Moderation Failed"

            with st.expander(
                f"{status_icon} Comprehensive Analysis Results - {status_text}", expanded=True
            ):
                # Analysis timestamp
                st.write(f"**Analysis Time:** {result_data['timestamp']}")

                # 1. Moderation results
                st.markdown("### 1️⃣ Review Moderation Results")

                # 1-1. Profanity check
                profanity_check = moderation_result.get("profanity_check", {})
                print("!"*13)
                print(profanity_check)
                print("!"*13)
                if profanity_check:
                    prof_status = profanity_check.get("status", "SKIP")
                    st.markdown(f"**🔍 Profanity Check:** {prof_status}")
                    st.markdown(f"**Reason:** {profanity_check.get('reason', '-')}")
                    st.markdown(
                        f"**Confidence:** {profanity_check.get('confidence', 0):.2f}"
                    )
                    st.markdown("---")

                # 1-2. Rating-content consistency check
                rating_check = moderation_result.get("rating_consistency", {})
                if rating_check:
                    rating_status = rating_check.get("status", "SKIP")
                    st.markdown(f"**⭐ Rating-Content Consistency:** {rating_status}")
                    st.markdown(f"**Reason:** {rating_check.get('reason', '-')}")
                    st.markdown(f"**Confidence:** {rating_check.get('confidence', 0):.2f}")
                    st.markdown("---")

                # 1-3. Image matching check
                image_check = moderation_result.get("image_match", {})
                if image_check:
                    image_status = image_check.get("status", "SKIP")
                    st.markdown(f"**📷 Image Matching:** {image_status}")
                    st.markdown(f"**Reason:** {image_check.get('reason', '-')}")
                    st.markdown(f"**Confidence:** {image_check.get('confidence', 0):.2f}")
                    st.markdown("---")

                # Overall moderation result
                st.markdown(f"**📋 Overall Moderation Result:** {status_text} ({overall_status})")
                failed_checks = moderation_result.get("failed_checks", [])
                if failed_checks:
                    st.markdown(f"**Failed Items:** {', '.join(failed_checks)}")

                # Skip subsequent steps if moderation failed
                if not is_approved:
                    st.warning(
                        "⚠️ The review did not pass moderation, so subsequent analysis steps were skipped."
                    )
                else:
                    # 2. Keyword analysis results
                    st.markdown("### 2️⃣ Keyword Analysis Results")
                    keyword_highlights = analysis.get("keyword_highlighted_list", [])

                    if keyword_highlights:
                        for highlight in keyword_highlights:
                            keyword = highlight.get("keyword", "")
                            match_type = highlight.get("match_type", "")
                            original_phrase = highlight.get("original_phrase", "")

                            st.markdown(f"**Keyword:** `{keyword}` ({match_type} match)")
                            st.markdown("**Related Sentence:**")
                            st.markdown(f"• {original_phrase}")
                    else:
                        st.info("No keywords extracted.")

                    # 3. Sentiment analysis results
                    st.markdown("### 3️⃣ Sentiment Analysis Results")
                    sentiment = analysis.get("sentiment", "No information")

                    # Color and icon based on sentiment
                    if "positive" in sentiment.lower():
                        sentiment_color = "#22c55e"
                        sentiment_icon = "😊"
                        sentiment_text = "Positive"
                    elif "negative" in sentiment.lower():
                        sentiment_color = "#ef4444"
                        sentiment_icon = "😞"
                        sentiment_text = "Negative"
                    else:
                        sentiment_color = "#6b7280"
                        sentiment_icon = "😐"
                        sentiment_text = "Neutral"

                    st.markdown(
                        f"{sentiment_icon} **Sentiment:** {sentiment_text} ({sentiment})"
                    )

                    # 4. Auto-response results
                    st.markdown("### 4️⃣ Auto Response")
                    auto_response = analysis.get("auto_response", "No response generated")

                    st.markdown("**💬 Generated Seller Response:**")
                    # Display auto-response in a box
                    response_html = auto_response.replace("\n", "<br>")
                    st.markdown(
                        f'<div style="background: linear-gradient(135deg, #f8fafc 0%, #ffffff 100%); padding: 20px; border-radius: 12px; border: 2px solid #3b82f6; margin-top: 10px; line-height: 1.6;">{response_html}</div>',
                        unsafe_allow_html=True,
                    )

        st.markdown("---")

st.markdown("---")

st.subheader("✍️ Write New Review")

with st.form("comment_form"):
    col1, col2 = st.columns([3, 1])

    with col1:
        author_name = st.text_input("Author Name", placeholder="Enter your name")
        comment_content = st.text_area(
            "Review Content", placeholder="Share your opinion about the product", height=100
        )

        uploaded_image = st.file_uploader(
            "Attach Image (Optional)",
            type=["png", "jpg", "jpeg"],
            accept_multiple_files=False,
        )

    with col2:
        rating = st.selectbox(
            "Rating", [5, 4, 3, 2, 1], format_func=lambda x: f"⭐ {x} stars"
        )

    submitted = st.form_submit_button("Submit Review", type="primary")

    if submitted:
        if author_name and comment_content:
            # Process image
            pil_image = None
            if uploaded_image:
                try:
                    pil_image = Image.open(uploaded_image)
                except Exception as e:
                    st.error(f"An error occurred while processing the image: {e}")
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
            st.success("Review submitted successfully!")

            # Perform automatic comprehensive analysis (if AGENT_AVAILABLE)
            if AGENT_AVAILABLE:
                with st.spinner("Automatically analyzing new review..."):
                    try:
                        # Prepare review data
                        review_data = {
                            "review_id": new_comment["id"],
                            "content": comment_content,
                            "rating": rating,
                            "author": author_name,
                            "timestamp": new_comment["timestamp"],
                        }
                        product_data = {
                            "name": "Premium Wireless Earphones",
                            "category": "Electronics",
                        }

                        # Execute comprehensive analysis
                        analysis_result = comprehensive_analyzer(
                            product_data, review_data, pil_image
                        )

                        # Save results to session state
                        st.session_state.comprehensive_analysis_results[
                            new_comment["id"]
                        ] = {
                            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            "analysis_result": analysis_result,
                            "review_data": review_data,
                        }

                        st.success("Automatic comprehensive analysis completed!")

                    except Exception as e:
                        st.error(f"An error occurred during automatic comprehensive analysis: {str(e)}")

            st.rerun()
        else:
            st.error("Please enter both author name and review content.")

st.markdown("---")
