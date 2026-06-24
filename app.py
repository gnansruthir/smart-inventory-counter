import streamlit as st
import json
import os
import pandas as pd
from detector import InventoryDetector
from db_manager import DBManager
import plotly.express as px

# Page configuration
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
            transition: all 0.3s ease;
        }
        .stButton>button:hover {
            background-color: #4338ca;
            transform: translateY(-1px);
        }
        .header-container {
            background: linear-gradient(135deg, #1e1b4b 0%, #311042 100%);
            padding: 2.5rem;
            border-radius: 12px;
            margin-bottom: 2rem;
            border: 1px solid #312e81;
        }
        .metric-card {
            background-color: #1e293b;
            padding: 1.5rem;
            border-radius: 10px;
            border: 1px solid #334155;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        }
    </style>
""", unsafe_allow_html=True)

# Initialization of helper classes
SKU_FILE = "sku_mapping.json"

def load_sku_mapping():
    if os.path.exists(SKU_FILE):
        with open(SKU_FILE, "r") as f:
            return json.load(f)
    return {}

def save_sku_mapping(mapping):
    with open(SKU_FILE, "w") as f:
        json.dump(mapping, f, indent=2)

sku_mapping = load_sku_mapping()
db_manager = DBManager()

@st.cache_resource
def get_detector():
    return InventoryDetector()

try:
    detector = get_detector()
except Exception as e:
    st.error(f"Failed to load YOLOv8 model: {e}")
    detector = None

# App Title Header
st.markdown("""
    <div class="header-container">
        <h1 style='margin: 0; color: #f8fafc; font-family: "Outfit", sans-serif;'>📦 Smart Inventory Counter</h1>
        <p style='margin: 0.5rem 0 0 0; color: #94a3b8;'>Computer Vision-Powered Retail Stock Tallying System</p>
    </div>
""", unsafe_allow_html=True)

# Sidebar Navigation
st.sidebar.title("Navigation")
app_mode = st.sidebar.radio("Go to", ["Static Image Upload", "Live Webcam (Coming Soon)", "SKU Management", "Analytics & History"])

if app_mode == "Static Image Upload":
    st.subheader("📷 Shelf Snapshot Scanning")
    st.write("Upload an image of your inventory shelf to run detection and calculate total inventory value.")

    uploaded_file = st.file_uploader("Choose an image...", type=["jpg", "jpeg", "png"])

    if uploaded_file is not None and detector is not None:
        col1, col2 = st.columns([2, 1])

        with col1:
            st.write("### Detection Visualization")
            with st.spinner("Processing image..."):
                try:
                    annotated_image, counts = detector.detect_image(uploaded_file)
                    st.image(annotated_image, caption="Processed Image Output", use_container_width=True)
                except Exception as e:
                    st.error(f"Error processing image: {e}")
                    counts = {}

        with col2:
            st.write("### Scan Breakdown")
            if counts:
                # Compile table mapping counts to SKUs
                tally_data = []
                total_value = 0.0
                total_items = 0
                
                for detected_class, count in counts.items():
                    mapping = sku_mapping.get(detected_class, {
                        "sku_name": f"Unmapped ({detected_class})",
                        "price": 0.0,
                        "low_stock_threshold": 0
                    })
                    
                    sku_name = mapping["sku_name"]
                    price = mapping["price"]
                    threshold = mapping["low_stock_threshold"]
                    subtotal = count * price
                    
                    total_value += subtotal
                    total_items += count
                    
                    # Highlight if stock level is below threshold
                    is_low_stock = "⚠️ Low Stock" if count < threshold else "✅ OK"
                    
                    tally_data.append({
                        "Detected Class": detected_class,
                        "SKU Name": sku_name,
                        "Count": count,
                        "Price ($)": f"${price:.2f}",
                        "Subtotal": f"${subtotal:.2f}",
                        "Status": is_low_stock,
                        "_raw_subtotal": subtotal,
                        "_raw_price": price
                    })
                
                df_tally = pd.DataFrame(tally_data)
                
                # Show key metrics in premium widgets
                st.markdown(f"""
                    <div style="display: flex; gap: 10px; margin-bottom: 20px;">
                        <div class="metric-card" style="flex: 1; text-align: center;">
                            <span style="color: #94a3b8; font-size: 0.85rem;">TOTAL ITEMS</span>
                            <h2 style="margin: 5px 0 0 0; color: #f8fafc;">{total_items}</h2>
                        </div>
                        <div class="metric-card" style="flex: 1; text-align: center;">
                            <span style="color: #94a3b8; font-size: 0.85rem;">TOTAL VALUE</span>
                            <h2 style="margin: 5px 0 0 0; color: #10b981;">${total_value:.2f}</h2>
                        </div>
                    </div>
                """, unsafe_allow_html=True)
                
                st.dataframe(
                    df_tally[["Detected Class", "SKU Name", "Count", "Price ($)", "Subtotal", "Status"]], 
                    hide_index=True, 
                    use_container_width=True
                )
                
                # Log scan button
                if st.button("💾 Commit & Log Scan to Database"):
                    db_items = []
                    for item in tally_data:
                        db_items.append({
                            'sku_name': item['SKU Name'],
                            'detected_class': item['Detected Class'],
                            'count': item['Count'],
                            'unit_price': item['_raw_price']
                        })
                    try:
                        db_manager.log_scan(total_items, total_value, db_items)
                        st.success("Successfully logged scan results to SQLite!")
                    except Exception as e:
                        st.error(f"Failed to log scan: {e}")
            else:
                st.info("No retail products detected in this snapshot.")

elif app_mode == "SKU Management":
    st.subheader("⚙️ SKU Catalog Configuration")
    st.write("Configure details mapping YOLO classification classes to retail SKUs.")
    
    # Form to add/edit mappings
    with st.form("add_sku_form"):
        st.write("### Add / Update SKU Mapping")
        class_name = st.text_input("YOLO Class ID (e.g. 'bottle', 'cup')").lower().strip()
        sku_name = st.text_input("Product Name (e.g. 'Pepsi 500ml')")
        price = st.number_input("Retail Unit Price ($)", min_value=0.0, step=0.01)
        threshold = st.number_input("Low Stock Threshold Alert", min_value=0, step=1)
        
        submit_btn = st.form_submit_button("Save SKU Config")
        
        if submit_btn:
            if not class_name or not sku_name:
                st.warning("Please specify both the target Class ID and the Product Name.")
            else:
                sku_mapping[class_name] = {
                    "sku_name": sku_name,
                    "price": price,
                    "low_stock_threshold": int(threshold)
                }
                save_sku_mapping(sku_mapping)
                st.success(f"Configured SKU mapping for class '{class_name}'.")

    # Present existing mappings in a table
    st.write("### Active SKU Mappings")
    if sku_mapping:
        records = []
        for cls_name, info in sku_mapping.items():
            records.append({
                "YOLO Class": cls_name,
                "Retail Product Name": info["sku_name"],
                "Unit Price": f"${info['price']:.2f}",
                "Alert Threshold": info["low_stock_threshold"]
            })
        st.dataframe(pd.DataFrame(records), hide_index=True, use_container_width=True)
    else:
        st.info("No custom SKU mappings registered yet.")

elif app_mode == "Analytics & History":
    st.subheader("📈 Historical Trends & Scan Logs")
    st.write("Analyze previous scans stored inside the SQLite database.")
    
    scans = db_manager.get_all_scans()
    
    if scans:
        df_scans = pd.DataFrame(scans, columns=["Scan ID", "Timestamp", "Total Items", "Total Value ($)"])
        
        # Display summary charts
        col1, col2 = st.columns(2)
        with col1:
            st.write("### Retail Stock Value Over Time")
            fig_val = px.line(df_scans, x="Timestamp", y="Total Value ($)", title="Inventory Valuation Trend", markers=True)
            st.plotly_chart(fig_val, use_container_width=True)
            
        with col2:
            st.write("### Total Item Count Over Time")
            fig_count = px.bar(df_scans, x="Timestamp", y="Total Items", title="Product Count Logs")
            st.plotly_chart(fig_count, use_container_width=True)
            
        st.write("### Historical Log")
        st.dataframe(df_scans, hide_index=True, use_container_width=True)
    else:
        st.info("No scan history logged to SQLite database yet.")

else:
    st.info("The live webcam feed component is scheduled for development in Phase 3.")
