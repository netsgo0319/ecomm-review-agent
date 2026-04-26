import base64
import json
import os
import sys
from datetime import datetime
from io import BytesIO

import streamlit as st
from PIL import Image

sys.path.append(".")

# Attempt to import auto-response agent
try:
    import sys

    from auto_response.agent import generate_auto_response

    AGENT_AVAILABLE = True
except ImportError as e:
    print(f"Auto Response Agent import failed: {e}")
    AGENT_AVAILABLE = False

st.set_page_config(page_title="Lab04. Auto Response Agent", page_icon="🛍️", layout="wide")

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
    # Preload images
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
            "author": "Kim Minsu",
            "rating": 5,
            "content": "This product is really great! The sound quality is excellent and the battery lasts long. The performance is excellent for the price.",
            "timestamp": "2024-01-15 14:30",
            "images": [],
        },
        {
            "id": 2,
            "author": "Lee Younghee",
            "rating": 2,
            "content": "The delivery is too slow. When can I receive it? It's been more than a week since I ordered, but it still shows 'preparing for shipment'.",
            "timestamp": "2024-01-14 10:20",
            "images": [],
        },
        {
            "id": 3,
            "author": "Park Cheolsu",
            "rating": 1,
            "content": "The product is defective and I want a refund. How do I do that? I can't even reach customer service and it's frustrating.",
            "timestamp": "2024-01-13 16:45",
            "images": [],
        }
    ]

# Session state for storing auto-response results
if "auto_responses" not in st.session_state:
    st.session_state.auto_responses = {}

# Main content area
st.header("🛍️ Lab 04. Review Auto-Response System")
st.subheader("Hands-on System for Automatically Generating Seller Responses to Customer Reviews")
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

st.subheader("💬 Reviews List")

for comment in reversed(st.session_state.comments):
    with st.container():
        col1, col2, col3, col4 = st.columns([3, 1, 1, 1])

        with col1:
            st.write(f"**{comment['author']}**")
            st.write(comment["content"])

            if "images" in comment and comment["images"]:
                st.write("📷 **Attached Images:**")
                img_cols = st.columns(min(len(comment["images"]), 3))
                for idx, img_str in enumerate(comment["images"]):
                    with img_cols[idx % 3]:
                        try:
                            img = base64_to_image(img_str)
                            st.image(img, width=150, caption=f"Image {idx+1}")
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
                "💬 Auto Response",
                key=f"review_{comment['id']}",
                type="primary",
                use_container_width=True,
            ):
                if AGENT_AVAILABLE:
                    with st.spinner("Generating auto-response..."):
                        try:
                            # Execute auto-response generation
                            agent_result = generate_auto_response(comment["content"])

                            # Save auto-response result per comment
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
                            print(f"=== Auto-response Generation Error Debugging ===")
                            print(f"Error message: {str(e)}")
                            print(f"Detailed stack trace:")
                            print(error_details)
                            print(f"===================")

                            st.error(f"An error occurred during auto-response generation: {str(e)}")
                            with st.expander("Detailed Error Information"):
                                st.code(error_details)

                            # Save error information as well
                            st.session_state.auto_responses[comment["id"]] = {
                                "timestamp": datetime.now().strftime(
                                    "%Y-%m-%d %H:%M:%S"
                                ),
                                "response": f"An error occurred during response generation: {str(e)}",
                                "tool_result": [],
                                "review_text": comment["content"],
                                "success": False,
                                "error": str(e),
                            }
                else:
                    st.warning("Auto-response agent is not available.")

        # Display expandable menu if auto-response result exists
        if comment["id"] in st.session_state.auto_responses:
            auto_response = st.session_state.auto_responses[comment["id"]]
            success = auto_response.get("success", True)

            # Select icon based on success/failure
            if success:
                status_icon = "✅"
                status_color = "#22c55e"
                status_text = "Auto-response Generation Complete"
            else:
                status_icon = "❌"
                status_color = "#ef4444"
                status_text = "Auto-response Generation Failed"

            with st.expander(f"{status_icon} {status_text}", expanded=True):
                # Response generation time
                st.write(f"**Generation Time:** {auto_response['timestamp']}")

                # Auto-response content
                st.write("**🏬 Seller Response:**")
                response_content = auto_response.get(
                    "response", "Could not generate response."
                )
                # Display response nicely
                st.markdown(
                    f"""
                    <div style='background-color: #f8fafc; padding: 20px; border-radius: 10px; border-left: 4px solid #3b82f6; margin: 10px 0;'>
                        <div style='color: #1e40af; font-weight: 500; margin-bottom: 8px;'>Seller Response:</div>
                        <div style='color: #374151; line-height: 1.6;'>{response_content}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                # Display tool call results
                tool_results = auto_response.get("tool_result", [])
                if tool_results:
                    with st.expander(
                        f"🔧 Tool Usage Results ({len(tool_results)} items)", expanded=False
                    ):
                        import json

                        for idx, tool_info in enumerate(tool_results):
                            st.write(f"**Tool {idx+1} Result:**")
                            # Display nicely in JSON format
                            st.json(tool_info)

                            if idx < len(tool_results) - 1:
                                st.divider()
                else:
                    st.info("🔧 No tool usage information for this response.")

                # Error information (if exists)
                if not success and "error" in auto_response:
                    st.error(f"Error during generation: {auto_response['error']}")

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

    with col2:
        rating = st.selectbox(
            "Rating", [5, 4, 3, 2, 1], format_func=lambda x: f"⭐ {x} points"
        )

    submitted = st.form_submit_button("Submit Review", type="primary")

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
            st.success("Review has been submitted successfully!")

            # Perform automatic response generation (if AGENT_AVAILABLE)
            if AGENT_AVAILABLE:
                with st.spinner("Generating auto-response for new review..."):
                    try:
                        # Execute auto-response generation
                        agent_result = generate_auto_response(comment_content)

                        # agent_result already contains response and tool_result
                        # Parse as JSON or use directly
                        import json

                        try:
                            # Attempt JSON parsing
                            parsed_result = json.loads(str(agent_result))
                            response_text = parsed_result.get(
                                "response", str(agent_result)
                            )
                            tool_results = parsed_result.get("tool_results", [])
                        except:
                            # If JSON parsing fails, use entire result as response
                            response_text = str(agent_result)
                            tool_results = []

                        # Save auto-response result per comment
                        st.session_state.auto_responses[new_comment["id"]] = {
                            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            "response": response_text,
                            "tool_result": tool_results,
                            "review_text": comment_content,
                            "success": True,
                        }

                    except Exception as e:
                        st.error(f"An error occurred during auto-response generation: {str(e)}")

            st.rerun()
        else:
            st.error("Please enter both author name and review content.")

st.markdown("---")
