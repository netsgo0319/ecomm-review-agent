import os
import sys
from datetime import datetime

import streamlit as st
from PIL import Image

sys.path.append(".")

# Image path configuration
IMAGES_DIR = os.path.join(os.path.dirname(__file__), "images")

# Attempt to import moderation agent
try:
    from review_moderator.agent import moderate_review

    AGENT_AVAILABLE = True
except ImportError as e:
    print(f"Agent import failed: {e}")
    AGENT_AVAILABLE = False

st.set_page_config(page_title="Lab 03. Review Moderation Agent", page_icon="🛍️", layout="wide")

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
            "author": "Park Cheolsu",
            "rating": 5,
            "content": "Not great. I had high expectations but disappointed.",
            "timestamp": "2024-01-13 16:45",
            "image": None,
        },
        {
            "id": 4,
            "author": "Choi Jihoon",
            "rating": 4,
            "content": "The earphone design is clean and comfortable to wear. The sound quality is pretty decent for the price. I tried it during my morning workout and it didn't fall off, which is great!",
            "timestamp": "2024-01-12 09:15",
            "image_path": os.path.join(IMAGES_DIR, "earphone.png"),
        },
        {
            "id": 5,
            "author": "Jung Sooyeon",
            "rating": 3,
            "content": "Earphone hurray",
            "timestamp": "2024-01-11 16:22",
            "image_path": os.path.join(IMAGES_DIR, "flower.webp"),
        },
    ]

# Session state for storing moderation results
if "comment_moderation_results" not in st.session_state:
    st.session_state.comment_moderation_results = {}

# Main content area
st.header("🏷️ Lab 03. Review Moderation Agent")
st.subheader("Hands-on Inappropriate Review Moderation System")
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

            # Display image (image or image_path)
            image_to_display = comment.get("image") or comment.get("image_path")
            if image_to_display:
                st.write("📷 **Attached Image:**")
                try:
                    st.image(image_to_display, width=150)
                except Exception as e:
                    st.error(f"Cannot load image: {e}")

        with col2:
            # Display star rating with unified style
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
                "🔍 Moderate",
                key=f"review_{comment['id']}",
                type="primary",
                use_container_width=True,
            ):
                if not AGENT_AVAILABLE:
                    st.warning("Moderation agent is not available.")
                    continue

                with st.spinner("Moderating..."):
                    try:
                        product_data = {
                            "name": "Premium Wireless Earphones",
                            "category": "Electronics",
                        }

                        # Load image (convert to PIL Image)
                        image = None
                        if comment.get("image"):
                            image = comment["image"]
                        elif comment.get("image_path"):
                            try:
                                image = Image.open(comment["image_path"])
                            except Exception:
                                pass

                        result = moderate_review(
                            review_content=comment["content"],
                            rating=comment["rating"],
                            product_data=product_data,
                            image=image,
                        )

                        moderation_result = result["moderation_result"]
                        if hasattr(moderation_result, "model_dump"):
                            moderation_result_dict = moderation_result.model_dump()
                        else:
                            moderation_result_dict = moderation_result

                        st.session_state.comment_moderation_results[comment["id"]] = {
                            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            "overall_status": moderation_result_dict["overall_status"],
                            "details": moderation_result_dict,
                            "failed_checks": moderation_result_dict.get(
                                "failed_checks", []
                            ),
                            "raw_response": result.get("raw_response", ""),
                        }
                    except Exception as e:
                        st.error(f"An error occurred during moderation: {str(e)}")

        # Display expandable menu if moderation result exists
        if comment["id"] in st.session_state.comment_moderation_results:
            moderation_result = st.session_state.comment_moderation_results[
                comment["id"]
            ]

            # Icon based on moderation result status
            status_icon = (
                "✅" if moderation_result["overall_status"] == "PASS" else "❌"
            )

            with st.expander(
                f"{status_icon} View Moderation Details - {moderation_result['overall_status']}",
                expanded=False,
            ):
                # Moderation time
                st.write(f"**Moderation Time:** {moderation_result['timestamp']}")

                # Overall status
                if moderation_result["overall_status"] == "PASS":
                    st.success("✅ Overall Moderation Passed")
                else:
                    st.error("❌ Overall Moderation Failed")

                # Detailed moderation results
                st.write("**Detailed Moderation Results:**")
                details = moderation_result["details"]

                # Results for each moderation item
                for check_name in [
                    "profanity_check",
                    "image_match",
                    "rating_consistency",
                ]:
                    if check_name in details:
                        result = details[check_name]
                        status_emoji = (
                            "✅"
                            if result["status"] == "PASS"
                            else "⏭️" if result["status"] == "SKIP" else "❌"
                        )

                        check_display_name = {
                            "profanity_check": "Profanity/Explicit Content Check",
                            "image_match": "Image Match Check",
                            "rating_consistency": "Rating Consistency Check",
                        }.get(check_name, check_name)

                        with st.container():
                            col_status, col_detail = st.columns([1, 4])
                            with col_status:
                                st.write(f"{status_emoji} **{check_display_name}**")
                            with col_detail:
                                st.write(f"{result.get('reason', 'No reason')}")
                                if "confidence" in result:
                                    st.caption(f"Confidence: {result['confidence']:.2f}")

                # Failed moderation items
                if moderation_result["failed_checks"]:
                    st.write("**Failed Moderation Items:**")
                    for failed_check in moderation_result["failed_checks"]:
                        st.write(f"- {failed_check}")

                # Summary message
                if "summary" in details:
                    st.write("**Summary:**")
                    st.info(details["summary"])

                # Original response (for debugging)
                with st.expander("Original Agent Response (for debugging)", expanded=False):
                    st.code(
                        moderation_result.get("raw_response", "No original response"),
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

        uploaded_image = st.file_uploader(
            "Attach Image (optional)",
            type=["png", "jpg", "jpeg"],
            accept_multiple_files=False,
        )

    with col2:
        rating = st.selectbox(
            "Rating", [5, 4, 3, 2, 1], format_func=lambda x: f"⭐ {x} points"
        )

    submitted = st.form_submit_button("Submit Comment", type="primary")

    if submitted:
        if author_name and comment_content:
            image = None

            if uploaded_image:
                try:
                    image = Image.open(uploaded_image)
                    max_size = (800, 600)
                    image.thumbnail(max_size, Image.Resampling.LANCZOS)
                except Exception as e:
                    st.error(f"An error occurred during image processing: {e}")
                    st.stop()

            new_comment = {
                "id": len(st.session_state.comments) + 1,
                "author": author_name,
                "rating": rating,
                "content": comment_content,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "image": image,
            }
            st.session_state.comments.append(new_comment)
            st.success("Comment has been submitted successfully!")

            # Perform automatic moderation (if AGENT_AVAILABLE)
            if AGENT_AVAILABLE:
                with st.spinner("Auto-moderating new comment..."):
                    try:
                        # Prepare product data
                        product_data = {
                            "name": "Premium Wireless Earphones",
                            "category": "Electronics",
                        }

                        # Execute moderation with agent
                        result = moderate_review(
                            review_content=comment_content,
                            rating=rating,
                            product_data=product_data,
                            image=image,
                        )

                        moderation_result = result["moderation_result"]
                        if hasattr(moderation_result, "model_dump"):
                            moderation_result_dict = moderation_result.model_dump()
                        else:
                            moderation_result_dict = moderation_result

                        # Save moderation result per comment
                        st.session_state.comment_moderation_results[
                            new_comment["id"]
                        ] = {
                            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            "overall_status": moderation_result_dict["overall_status"],
                            "details": moderation_result_dict,
                            "failed_checks": moderation_result_dict.get(
                                "failed_checks", []
                            ),
                            "raw_response": result.get("raw_response", ""),
                        }

                    except Exception as e:
                        st.error(f"An error occurred during automatic moderation: {str(e)}")

            st.rerun()
        else:
            st.error("Please enter both author name and comment content.")

st.markdown("---")
