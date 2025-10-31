from datetime import datetime

import streamlit as st
from sentiment_analyzer.agent import analyze_sentiment

st.set_page_config(page_title="Lab 01. Sentiment Analysis Agent", page_icon="🛍️", layout="wide")

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
            "author": "Kim Minsu",
            "rating": 5,
            "content": "The earphone design is clean and comfortable to wear. The sound quality is pretty decent for the price. I tried it during my morning workout and it didn't fall off, which is great!",
            "timestamp": "2024-01-15 14:30",
        },
        {
            "id": 2,
            "author": "Lee Younghee",
            "rating": 5,
            "content": "The product is really good! The sound quality is excellent and the battery lasts long.",
            "timestamp": "2024-01-14 10:20",
        },
        {
            "id": 3,
            "author": "Park Cheolsu",
            "rating": 3,
            "content": "So-so. At least the delivery was fast.",
            "timestamp": "2024-01-13 16:45",
        },
        {
            "id": 4,
            "author": "Choi Jihoon",
            "rating": 1,
            "content": "This is a total disaster!^^ If you want to throw your money away, please buy this!",
            "timestamp": "2024-01-12 09:15",
        },
        {
            "id": 5,
            "author": "Jung Sooyeon",
            "rating": 3,
            "content": "Not as good as I expected. I had high hopes because people said it was good value... For this price, buy something else.",
            "timestamp": "2024-01-11 16:22",
        },
    ]

# Session state for storing sentiment analysis results
if "sentiment_analysis_results" not in st.session_state:
    st.session_state.sentiment_analysis_results = {}


# Helper function to save sentiment analysis results
def save_sentiment_result(comment_id, content, sentiment_result):
    """Save sentiment analysis results to session state"""
    sentiment_data = sentiment_result["sentiment_result"]

    result_dict = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "label": sentiment_data.get("sentiment", "neutral"),
        "score": sentiment_data.get("score", 0.5),
        "confidence": sentiment_data.get("confidence", 0.5),
        "rationale": sentiment_data.get("reason", "No analysis rationale available"),
        "review_text": content,
        "raw_response": sentiment_result.get("raw_response", ""),
    }

    if not sentiment_result["success"]:
        result_dict["confidence"] = 0.3
        result_dict["rationale"] = "Analysis error"
        result_dict["error"] = sentiment_result.get("error", "")

    st.session_state.sentiment_analysis_results[comment_id] = result_dict
    return sentiment_result["success"]


# Function to generate star rating HTML
def generate_stars_html(rating):
    """Generate star rating HTML"""
    stars = ""
    for i in range(5):
        if i < rating:
            stars += '<span style="color: #fbbf24; font-size: 18px;">★</span>'
        else:
            stars += '<span style="color: #d1d5db; font-size: 18px;">★</span>'
    return stars


# Function to get sentiment icon and color
def get_sentiment_style(label):
    """Return icon and color based on sentiment"""
    if label in ["positive"]:
        return "😊", "#22c55e"
    elif label in ["negative"]:
        return "😞", "#ef4444"
    else:
        return "😐", "#6b7280"


# Main content area
st.header("🛍️ Lab 01. Review Sentiment Analysis System")
st.subheader("Hands-on Sentiment Analysis System for Reviews")
st.markdown("---")

total_reviews = len(st.session_state.comments)
total_rating = sum([comment["rating"] for comment in st.session_state.comments])
average_rating = total_rating / total_reviews if total_reviews else 0

st.subheader("📦 Product Information")
# <h3 style="color:black">📦 Product Information</h3>
st.markdown(
    f"""
    <div class="product-rating-container">
        <div class="product-rating-grid">
            <div>
                <p><strong>Product Name:</strong> Premium Wireless Earphones</p>
                <p><strong>Price:</strong> $89.00</p>
                <p><strong>Product Description:</strong></p>
                <p>Premium wireless earphones featuring high-quality sound and long battery life. Provides noise cancellation functionality and comfortable fit.</p>
            </div>
            <div>
                <div class="rating-card">
                    <div class="metric-label"><strong>Average Rating</strong> ({total_reviews} total reviews)</div>
                    <div class="metric-value">{average_rating:.1f} / 5.0</div>
                </div>
            </div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.subheader("💬 Comments List")

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
            # Check if review has already been analyzed
            is_analyzed = comment["id"] in st.session_state.sentiment_analysis_results
            button_text = "✅ Analyzed" if is_analyzed else "😍 Analyze"
            button_disabled = is_analyzed

            if st.button(
                button_text,
                key=f"review_{comment['id']}",
                type="secondary" if is_analyzed else "primary",
                use_container_width=True,
                disabled=button_disabled,
            ):
                with st.spinner("Analyzing sentiment..."):
                    try:
                        sentiment_result = analyze_sentiment(comment["content"])
                        success = save_sentiment_result(
                            comment["id"], comment["content"], sentiment_result
                        )

                        if success:
                            st.success("✅ Analysis complete!")
                        else:
                            st.warning(
                                "⚠️ An error occurred during analysis, but fallback result was saved."
                            )
                        st.rerun()

                    except Exception as e:
                        st.error(f"Error occurred during sentiment analysis: {str(e)}")

        # Display expandable menu if sentiment analysis results exist
        if comment["id"] in st.session_state.sentiment_analysis_results:
            sentiment_result = st.session_state.sentiment_analysis_results[
                comment["id"]
            ]
            label = sentiment_result.get("label", "neutral")
            score = sentiment_result.get("score", 0.5)
            confidence = sentiment_result.get("confidence", 0.5)

            # Icon and color based on sentiment
            status_icon, status_color = get_sentiment_style(label)

            with st.expander(
                f"{status_icon} Sentiment Analysis Result - {label} ({score:.3f})", expanded=False
            ):
                # Analysis timestamp
                st.write(f"**Analysis Time:** {sentiment_result['timestamp']}")

                # Sentiment analysis results
                col1, col2 = st.columns([1, 2])
                with col1:
                    st.markdown(
                        f"<div style='text-align: center; padding: 20px; background-color: {status_color}15; border-radius: 10px; border: 2px solid {status_color}40;'>"
                        f"<div style='font-size: 48px;'>{status_icon}</div>"
                        f"<div style='font-size: 24px; font-weight: bold; color: {status_color}; margin-top: 10px;'>{label}</div>"
                        f"<div style='font-size: 16px; color: {status_color}; margin-top: 5px;'>Score: {score:.3f}</div>"
                        f"</div>",
                        unsafe_allow_html=True,
                    )

                with col2:
                    st.write("**Analysis Rationale:**")
                    st.write(sentiment_result.get("rationale", "No rationale available"))

                    st.write("**Confidence:**")
                    st.write(f"{confidence:.2f} / 1.00")

                # Error information (if exists)
                if "error" in sentiment_result and sentiment_result["error"]:
                    st.error(f"Analysis error: {sentiment_result['error']}")

                # Agent debugging information
                if (
                    "raw_response" in sentiment_result
                    and sentiment_result["raw_response"]
                ):
                    with st.expander("Agent Debugging Info", expanded=False):
                        st.write("**Agent Raw Response:**")
                        st.code(
                            sentiment_result.get("raw_response", "No response available"),
                            language="text",
                        )

        st.markdown("---")

st.markdown("---")

st.subheader("✍️ Write New Comment")

with st.form("comment_form"):
    col1, col2 = st.columns([3, 1])

    with col1:
        author_name = st.text_input("Author Name", placeholder="Enter your name")
        comment_content = st.text_area(
            "Comment Content", placeholder="Share your opinion about the product", height=100
        )

    with col2:
        rating = st.selectbox(
            "Rating", [5, 4, 3, 2, 1], format_func=lambda x: f"⭐ {x} stars"
        )

    submitted = st.form_submit_button("Submit Comment", type="primary")

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
            st.success("Comment has been submitted successfully!")
            st.rerun()
        else:
            st.error("Please enter both author name and comment content.")

st.markdown("---")
