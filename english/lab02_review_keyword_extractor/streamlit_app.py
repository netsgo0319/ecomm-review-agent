import json
import os
from datetime import datetime
from typing import Any, Dict, List

import streamlit as st
from keyword_extractor.agent import search_keywords

# Keyword storage file path
KEYWORDS_FILE = os.path.join(
    os.path.dirname(__file__), "keyword_extractor", "registered_keywords.txt"
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
    with open(KEYWORDS_FILE, "w", encoding="utf-8") as f:
        for keyword in keywords:
            f.write(f"{keyword}\n")


def register_keyword(keyword: str) -> Dict[str, Any]:
    """Register new keyword"""
    # Load existing keywords
    keywords = load_keywords()

    # Check for duplicates
    if keyword in keywords:
        return {
            "status": "already_exists",
            "keyword": keyword,
            "total_keywords": len(keywords),
        }

    # Add new keyword
    keywords.append(keyword)

    # Save
    save_keywords(keywords)

    return {"status": "registered", "keyword": keyword, "total_keywords": len(keywords)}


# Keyword extraction helper function
def extract_keywords_from_result(match_result: Dict[str, Any]) -> List[str]:
    """Extract keyword list from matching result"""
    if not match_result.get("success"):
        return []

    analysis_result = match_result.get("analysis_result", {})
    matched_keywords = analysis_result.get("matched_keywords", [])

    if not matched_keywords:
        return []

    # New format: dictionary array
    if isinstance(matched_keywords[0], dict):
        return [
            item.get("keyword", "") for item in matched_keywords if item.get("keyword")
        ]
    # Old format: string array
    else:
        return matched_keywords


st.set_page_config(page_title="Lab 02. Keyword Search Agent", page_icon="🏷️", layout="wide")

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
    .keyword-badge {
        background-color: #e1f5fe;
        color: #01579b;
        padding: 4px 8px;
        margin: 2px;
        border-radius: 12px;
        font-size: 12px;
        display: inline-block;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# Initialize session state
if "keyword_matching_results" not in st.session_state:
    st.session_state.keyword_matching_results = {}

if "show_keyword_modal" not in st.session_state:
    st.session_state.show_keyword_modal = False

if "comments" not in st.session_state:
    st.session_state.comments = [
        {
            "id": 1,
            "author": "Park Jihoon",
            "rating": 5,
            "content": "Overall not bad. Seems usable for the price.",
            "timestamp": "2024-01-16 17:32",
        },
        {
            "id": 2,
            "author": "Kim Minsu",
            "rating": 5,
            "content": "It arrived just one day after ordering! I was in a hurry, so thank you for the fast delivery.",
            "timestamp": "2024-01-15 14:30",
        },
        {
            "id": 3,
            "author": "Lee Younghee",
            "rating": 4,
            "content": "I like the design the most, highly recommend white! But it hurts my ears a bit when I wear it, maybe because I have small ears.",
            "timestamp": "2024-01-14 16:45",
        },
        {
            "id": 4,
            "author": "Park Cheolsu",
            "rating": 3,
            "content": "I need to use it for a few more days, but so far both the sound quality and battery are satisfactory.",
            "timestamp": "2024-01-13 10:20",
        },
        {
            "id": 5,
            "author": "Choi Jiyoung",
            "rating": 5,
            "content": "I like the product. Especially when making calls, the voice comes through clearly, which is satisfying. The battery also lasts long.",
            "timestamp": "2024-01-12 09:15",
        },
    ]

# Main content area
st.header("🏷️ Lab 02. Keyword Search System")
st.subheader("Hands-on Keyword Search and Matching System for Reviews")
st.markdown("---")

# Product information and rating calculation
total_reviews = len(st.session_state.comments)
total_rating = sum([comment["rating"] for comment in st.session_state.comments])
average_rating = total_rating / total_reviews if total_reviews else 0

# Product information section (moved to top)
st.subheader("📦 Product Information")
# <h3 style="color:black">📦 Product Information</h3>
st.markdown(
    f"""
    <div class="product-rating-container">
        <div class="product-rating-grid">
            <div>
                <h3 style="color:black">📦 Product Information</h3>
                <p><strong>Product Name:</strong> Premium Wireless Earphones</p>
                <p><strong>Price:</strong> $89.00</p>
                <p><strong>Product Description:</strong></p>
                <p>Premium wireless earphones featuring high-quality sound and long battery life. Provides noise cancellation functionality and comfortable fit.</p>
            </div>
            <div class="rating-card">
                <div class="metric-label"><strong>Average Rating</strong> ({total_reviews} total reviews)</div>
                <div class="metric-value">{average_rating:.1f} / 5.0</div>
            </div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# Keyword management section
st.subheader("🏷️ Keyword Management")

# Display registered keywords and new keyword registration button
col1, col2 = st.columns([4, 1])

with col1:
    st.write("**Registered Keywords (Click to filter)**")
    registered_keywords = load_keywords()

    # Initialize selected keyword session state
    if "selected_keyword_filter" not in st.session_state:
        st.session_state["selected_keyword_filter"] = None

    if registered_keywords:
        # Display keywords as buttons (multiple per row)
        cols = st.columns(min(8, len(registered_keywords)))
        for idx, keyword in enumerate(registered_keywords):
            with cols[idx % len(cols)]:
                is_selected = st.session_state.get("selected_keyword_filter") == keyword
                button_type = "primary" if is_selected else "secondary"
                if st.button(
                    f"#{keyword}",
                    key=f"keyword_filter_{keyword}",
                    type=button_type,
                    use_container_width=True,
                ):
                    # Toggle action: deselect if same keyword clicked, select if different keyword clicked
                    if st.session_state["selected_keyword_filter"] == keyword:
                        st.session_state["selected_keyword_filter"] = None
                    else:
                        st.session_state["selected_keyword_filter"] = keyword
                    st.rerun()
    else:
        st.info("⚠️ No registered keywords. Please register a new keyword!")

with col2:
    if st.button("➕ Register New Keyword", type="primary", use_container_width=True):
        st.session_state["show_keyword_modal"] = True
        st.rerun()

# Keyword registration modal (popup)
if st.session_state.get("show_keyword_modal", False):
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
                                st.session_state["show_keyword_modal"] = False
                                st.rerun()
                    except Exception as e:
                        st.error(f"❌ Keyword registration failed: {str(e)}")
                else:
                    st.error("Please enter a keyword.")

            if cancel:
                st.session_state["show_keyword_modal"] = False
                st.rerun()

        st.markdown("---")

st.divider()

# Review section
st.subheader("📝 Customer Reviews")

# Get selected keyword filter
selected_keyword = st.session_state.get("selected_keyword_filter", None)

for comment in reversed(st.session_state.comments):
    # Check filtering
    show_comment = True
    if selected_keyword:  # Filter only when a keyword is selected
        # Filter only when a keyword is selected
        if comment["id"] in st.session_state.keyword_matching_results:
            result = st.session_state.keyword_matching_results[comment["id"]]
            match_result = result.get("match_result", {})
            keywords = extract_keywords_from_result(match_result)
            show_comment = selected_keyword in keywords
        else:
            show_comment = False

    if show_comment:
        with st.container():
            # Highlight review content
            highlighted_content = comment["content"]

            if comment["id"] in st.session_state.keyword_matching_results:
                result = st.session_state.keyword_matching_results[comment["id"]]
                match_result = result.get("match_result", {})

                if match_result.get("success"):
                    analysis_result = match_result.get("analysis_result", {})

                    # Highlight only phrases related to selected keyword
                    matched_keywords = analysis_result.get("matched_keywords", [])
                    phrases_to_highlight = []

                    if matched_keywords:
                        # New format: dictionary array
                        if isinstance(matched_keywords[0], dict):
                            for item in matched_keywords:
                                item_keyword = item.get("keyword", "")
                                original_phrase = item.get("original_phrase", "")

                                # Highlight only when matching selected keyword or no selection
                                if (
                                    not selected_keyword
                                    or item_keyword == selected_keyword
                                ) and original_phrase:
                                    phrases_to_highlight.append(original_phrase)
                        # Old format: string array - use matched_phrases
                        else:
                            if not selected_keyword:
                                phrases_to_highlight = analysis_result.get(
                                    "matched_phrases", []
                                )
                            else:
                                # When specific keyword selected, extract only that keyword's phrases
                                all_phrases = analysis_result.get("matched_phrases", [])
                                phrases_to_highlight = (
                                    all_phrases  # Use all phrases in old format
                                )

                    # Highlight phrases
                    for phrase in phrases_to_highlight:
                        if phrase and phrase in highlighted_content:
                            highlighted_content = highlighted_content.replace(
                                phrase,
                                f'<mark style="background: linear-gradient(135deg, #fff3cd 0%, #ffeaa7 100%); color: #856404; padding: 3px 8px; border-radius: 8px; font-weight: 500; box-shadow: 0 2px 6px rgba(255, 235, 59, 0.3); border: 1px solid #ffeaa7;">{phrase}</mark>',
                            )

            col1, col2, col3, col4 = st.columns([3, 1, 1, 1])

            with col1:
                st.write(f"**{comment['author']}**")
                st.markdown(highlighted_content, unsafe_allow_html=True)

                # Display found keywords (only if analyzed)
                if comment["id"] in st.session_state.keyword_matching_results:
                    result = st.session_state.keyword_matching_results[comment["id"]]
                    match_result = result.get("match_result", {})
                    if match_result.get("success"):
                        analysis_result = match_result.get("analysis_result", {})
                        matched_keywords = analysis_result.get("matched_keywords", [])

                        # New format: extract keywords from dictionary array
                        if matched_keywords and isinstance(matched_keywords[0], dict):
                            keywords = [
                                item.get("keyword", "")
                                for item in matched_keywords
                                if item.get("keyword")
                            ]
                        # Old format: string array
                        else:
                            keywords = matched_keywords

                        if keywords:
                            keywords_html = ""
                            for kw in keywords:
                                if kw == selected_keyword and selected_keyword:
                                    keywords_html += f'<span class="keyword-badge" style="background-color: #ff9800; color: white; font-weight: bold;">{kw}</span>'
                                else:
                                    keywords_html += (
                                        f'<span class="keyword-badge">{kw}</span>'
                                    )
                            st.markdown(
                                f"**Found Keywords:** {keywords_html}",
                                unsafe_allow_html=True,
                            )

            with col2:
                st.caption("⭐" * comment["rating"])
                st.caption(f"{comment['rating']}/5")

            with col3:
                st.caption(comment["timestamp"])

            with col4:
                # Individual keyword analysis button
                button_label = (
                    "✅ Re-analyze"
                    if comment["id"] in st.session_state.keyword_matching_results
                    else "🔍 Analyze Keywords"
                )
                if st.button(
                    button_label,
                    key=f"search_{comment['id']}",
                    type="primary",
                    use_container_width=True,
                ):
                    with st.spinner("Searching keywords..."):
                        try:
                            match_result = search_keywords(comment["content"])
                            st.session_state.keyword_matching_results[comment["id"]] = {
                                "timestamp": datetime.now().strftime(
                                    "%Y-%m-%d %H:%M:%S"
                                ),
                                "review_text": comment["content"],
                                "match_result": match_result,
                            }
                            st.success("✅ Analysis complete!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error during keyword search: {str(e)}")

            st.divider()

st.divider()

# New review registration section
st.subheader("✍️ Write New Review")

with st.form("new_comment_form"):
    col1, col2 = st.columns([3, 1])

    with col1:
        author_name = st.text_input("Author", placeholder="Enter your name")
        comment_content = st.text_area(
            "Review Content", placeholder="Write your review about the product", height=100
        )

    with col2:
        rating = st.selectbox("Rating", [1, 2, 3, 4, 5], index=4)

    if st.form_submit_button("Submit Review", type="primary"):
        if author_name and comment_content:
            new_comment = {
                "id": (
                    max([c["id"] for c in st.session_state.comments]) + 1
                    if st.session_state.comments
                    else 1
                ),
                "author": author_name,
                "content": comment_content,
                "rating": rating,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
            }

            st.session_state.comments.append(new_comment)
            st.success("Review has been submitted successfully!")
            st.rerun()
        else:
            st.error("Please enter both author name and review content.")
