import streamlit as st
from detector import InventoryDetector
import pandas as pd

# Page Configuration
st.set_page_config(
    page_title="Smart Inventory Counter",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom premium styling
st.markdown("""
    <style>
        .main {
            background-color: #0f1115;
            color: #e2e8f0;
        }
        .stButton>button {
            background-color: #4f46e5;
            color: white;
            border-radius: 8px;
            border: none;
            padding: 8px 16px;
            font-weight: 600;
        }
        .stButton>button:hover {
            background-color: #4338ca;
            color: #ffffff;
        }
        .header-container {
            background: linear-gradient(135deg, #1e1b4b 0%, #311042 100%);
            padding: 2.5rem;
            border-radius: 12px;
            margin-bottom: 2rem;
            border: 1px solid #312e81;
        }
    </style>
""", unsafe_allow_html=True)

# App header
st.markdown("""
    <div class="header-container">
        <h1 style='margin: 0; color: #f8fafc; font-family: "Outfit", sans-serif;'>📦 Smart Inventory Counter</h1>
        <p style='margin: 0.5rem 0 0 0; color: #94a3b8;'>Computer Vision-Powered Retail Stock Tallying System</p>
    </div>
""", unsafe_allow_html=True)

# Initialize detector cached in Streamlit session
@st.cache_resource
def get_detector():
    return InventoryDetector()

try:
    detector = get_detector()
except Exception as e:
    st.error(f"Failed to load YOLOv8 model: {e}")
    detector = None

# Sidebar Navigation
st.sidebar.title("Navigation")
app_mode = st.sidebar.radio("Go to", ["Static Image Upload", "Live Webcam (Coming Soon)", "SKU Management", "Analytics & History"])

if app_mode == "Static Image Upload":
    st.subheader("📷 Shelf Snapshot Scanning")
    st.write("Upload an image of your inventory shelf to automatically count items.")

    uploaded_file = st.file_uploader("Choose an image...", type=["jpg", "jpeg", "png"])

    if uploaded_file is not None and detector is not None:
        col1, col2 = st.columns([2, 1])

        with col1:
            st.write("### Processing Scan...")
            with st.spinner("Running YOLOv8 Object Detection..."):
                try:
                    annotated_image, counts = detector.detect_image(uploaded_file)
                    st.image(annotated_image, caption="Processed Image", use_container_width=True)
                except Exception as e:
                    st.error(f"Error processing image: {e}")
                    counts = {}

        with col2:
            st.write("### Detection Tallies")
            if counts:
                # Convert to dataframe for clean rendering
                df = pd.DataFrame(list(counts.items()), columns=["Category", "Detected Count"])
                st.dataframe(df, hide_index=True, use_container_width=True)
                
                # Show key metrics card
                total_items = sum(counts.values())
                st.metric(label="Total Objects Detected", value=total_items)
            else:
                st.info("No items detected in the image.")

else:
    st.info(f"The '{app_mode}' tab is scheduled for development in the upcoming phases of the implementation plan.")
