import streamlit as st
import pandas as pd
import os
import json
import cv2
import numpy as np
import plotly.express as px
import base64
from datetime import datetime
from db_manager import DBManager
from detector import InventoryDetector
from report_generator import generate_pdf_report, generate_csv_report

st.set_page_config(
    page_title="Smart Inventory Counter System",
   
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize database manager and YOLO model
SKU_FILE = "sku_mapping.json"
db_manager = DBManager()

def load_sku_mapping():
    if os.path.exists(SKU_FILE):
        with open(SKU_FILE, "r") as f:
            return json.load(f)
    return {}

def save_sku_mapping(mapping):
    with open(SKU_FILE, "w") as f:
        json.dump(mapping, f, indent=2)

sku_mapping = load_sku_mapping()

@st.cache_resource
def get_detector():
    return InventoryDetector()

try:
    detector = get_detector()
except Exception as e:
    st.error(f"Failed to load YOLOv8 model: {e}")
    detector = None

def get_base64_image(image_path):
    if os.path.exists(image_path):
        with open(image_path, "rb") as f:
            data = f.read()
        return base64.b64encode(data).decode()
    return ""

bg_base64 = get_base64_image("landing_bg.png")

# Session States Configuration
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "user_role" not in st.session_state:
    st.session_state.user_role = None
if "current_page" not in st.session_state:
    st.session_state.current_page = "Landing"

if "app_theme" not in st.session_state:
    st.session_state.app_theme = "Light Mode"

if not st.session_state.logged_in and bg_base64:
    bg_style = f"""
        .stApp {{
            background-image: url("data:image/png;base64,{bg_base64}");
            background-size: cover;
            background-position: center;
            background-repeat: no-repeat;
            background-attachment: fixed;
        }}
        .main {{
            background-color: transparent !important;
        }}
    """
else:
    if st.session_state.app_theme == "Dark Mode":
        bg_style = """
            .stApp {
                background-color: #0b0f19 !important;
            }
            .main {
                background-color: #0b0f19 !important;
                color: #f1f5f9 !important;
            }
            h1, h2, h3, h4, h5, h6, label, p, span, div, strong {
                color: #f1f5f9 !important;
            }
            div[data-testid="stMetricValue"] > div {
                color: #f1f5f9 !important;
            }
            .metric-card {
                background-color: #1e293b !important;
                border: 1px solid #334155 !important;
            }
        """
    else:
        bg_style = """
            .stApp {
                background-color: #ffffff !important;
            }
            .main {
                background-color: #ffffff !important;
                color: #0f172a !important;
            }
        """


# Custom premium styling
st.markdown(f"""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@400;600;700&family=Inter:wght@400;500;600&display=swap');
        html, body, [class*="css"] {{
            font-family: 'Inter', sans-serif;
        }}
        {bg_style}
        h1, h2, h3, h4, h5, h6 {{
            font-family: 'Outfit', sans-serif;
            font-weight: 700;
            color: #0f172a;
        }}
        .stButton>button {{
            background: linear-gradient(135deg, #7c3aed 0%, #4f46e5 100%);
            color: white;
            border-radius: 10px;
            border: none;
            padding: 10px 20px;
            font-weight: 600;
            box-shadow: 0 4px 14px 0 rgba(124, 58, 237, 0.4);
            transition: all 0.3s ease;
        }}
        .stButton>button:hover {{
            transform: translateY(-2px);
            box-shadow: 0 6px 20px 0 rgba(124, 58, 237, 0.6);
        }}
        .header-container {{
            background: transparent !important;
            padding: 1rem;
            margin-bottom: 1.5rem;
            border: none !important;
            backdrop-filter: none !important;
            text-align: center;
        }}
        .header-container h1 {{
            color: #1e1b4b !important;
            font-size: 4.25rem !important;
            margin: 0 !important;
            text-shadow: 2px 2px 0px #ffffff, -2px -2px 0px #ffffff, 2px -2px 0px #ffffff, -2px 2px 0px #ffffff, 0px 4px 10px rgba(124, 58, 237, 0.7);
            animation: floatAnimation 4s ease-in-out infinite;
        }}
        .metric-card {{
            background: #ffffff;
            padding: 1.5rem;
            border-radius: 14px;
            border: 1px solid #e2e8f0;
            margin-bottom: 15px;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
        }}
        
        @keyframes floatAnimation {{
            0% {{ transform: translateY(0px); }}
            50% {{ transform: translateY(-8px); }}
            100% {{ transform: translateY(0px); }}
        }}
        
        /* Floating layout for login box */
        div[data-testid="stForm"] {{
            animation: floatAnimation 4s ease-in-out infinite;
            background-color: #ffffff !important;
            border: 2px solid #7c3aed !important;
            border-radius: 16px !important;
            box-shadow: 0 10px 40px rgba(124, 58, 237, 0.6) !important;
            padding: 2rem !important;
        }}

        /* Force black tabs labels */
        button[data-baseweb="tab"] {{
            color: #000000 !important;
        }}
        button[data-baseweb="tab"] p {{
            color: #000000 !important;
            font-weight: 600 !important;
        }}

        /* Force black text for Username and Password widget labels */
        div[data-testid="stWidgetLabel"] label,
        div[data-testid="stWidgetLabel"] p,
        label,
        span[data-testid="stWidgetLabel"] {{
            color: #000000 !important;
            font-weight: 600 !important;
        }}

        /* Force light background and black text inside input fields and dropdowns */
        input, select, textarea, [data-baseweb="input"], [data-baseweb="select"] > div, button[role="combobox"] span {{
            background-color: #f1f5f9 !important;
            color: #000000 !important;
            -webkit-text-fill-color: #000000 !important;
            border: 1px solid #cbd5e1 !important;
        }}




    </style>
""", unsafe_allow_html=True)


if not st.session_state.logged_in:
    st.markdown("""
        <div class='header-container' style='text-align: center;'>
            <h1 style='font-size: 3rem; margin: 0;'>Smart Inventory Counter System</h1>
        </div>
    """, unsafe_allow_html=True)
    
    col_left, col_center, col_right = st.columns([1.3, 1.0, 1.3])
    with col_center:
        tab_signin, tab_signup = st.tabs(["Sign In", "Sign Up"])
        
        with tab_signin:
            with st.form("signin_form"):
                username = st.text_input("Username", key="signin_username")
                password = st.text_input("Password", type="password", key="signin_password")
                submit_signin = st.form_submit_button("Sign In")
                
                if submit_signin:
                    role = db_manager.authenticate_user(username, password)
                    if role:
                        st.session_state.logged_in = True
                        st.session_state.user_role = role
                        st.session_state.current_page = "Dashboard"
                        db_manager.log_audit(role, f"User {username} logged in successfully")
                        st.success(f"Welcome {role}! Loading panel...")
                        st.rerun()
                    else:
                        st.error("Account not found. Please create an account first.")

                        
        with tab_signup:
            with st.form("signup_form"):
                reg_username = st.text_input("Choose Username", key="signup_username")
                reg_password = st.text_input("Choose Password", type="password", key="signup_password")
                reg_role = st.selectbox("Select Your Role", ["Owner", "Staff"], key="signup_role")
                submit_signup = st.form_submit_button("Create Account")
                
                if submit_signup:
                    if not reg_username or not reg_password:
                        st.warning("Please specify both a username and password.")
                    elif reg_role == "Owner" and (reg_username != "admin" or reg_password != "admin123"):
                        st.error("Invalid registration credentials for Owner role.")
                    elif reg_role == "Staff" and (reg_username != "staff" or reg_password != "staff123"):
                        st.error("Invalid registration credentials for Staff role.")
                    else:
                        success = db_manager.add_user(reg_username, reg_password, reg_role)
                        if success:
                            db_manager.log_audit(reg_role, f"New user account registered: {reg_username}")
                            st.success("Account created successfully! You can now sign in using the Sign In tab.")
                        else:
                            st.success("Account already created! You can now sign in using the Sign In tab.")





# ----------------- Logged-in Panel -----------------
else:
    # Sidebar Page Navigation config based on roles
    st.sidebar.write(f"Logged in: **{st.session_state.user_role}**")
    
    if st.session_state.user_role == "Owner":
        menu_options = [
            "🏠 Owner Dashboard", 
            "📋 Inventory List",
            "📷 Static Image Upload", 
            "📹 Live Detection", 
            "⚖️ Before/After Comparison",
            "⚙️ SKU Management", 
            "📈 Reports & Analytics", 
            "🔔 Notifications & Alerts", 
            "📜 Audit Logs", 
            "🔧 Settings"
        ]
    else:
        menu_options = [
            "🏠 Staff Dashboard", 
            "📋 Inventory List",
            "📷 Static Image Upload", 
            "📹 Live Detection", 
            "🔔 Notifications & Alerts", 
            "🔧 Settings"
        ]
        
    app_mode = st.sidebar.radio("Navigate View", menu_options)
    
    if st.sidebar.button("🚪 Logout"):
        db_manager.log_audit(st.session_state.user_role, f"User {st.session_state.user_role.lower()} logged out")
        st.session_state.logged_in = False
        st.session_state.user_role = None
        st.session_state.current_page = "Landing"
        st.rerun()

    # Define standard classes threshold configurations check helper
    def check_low_stock():
        scans = db_manager.get_all_scans()
        low_stock_alerts = []
        if scans:
            latest_id = scans[0][0]
            details = db_manager.get_scan_details(latest_id)
            for item in details:
                sku_name, class_id, count, price = item
                threshold = sku_mapping.get(class_id, {}).get("low_stock_threshold", 0)
                if count < threshold:
                    low_stock_alerts.append(f"{sku_name} (Count: {count} | Min: {threshold})")
        return low_stock_alerts

    # ----------------- Dashboard (Owner / Staff) -----------------
    if "Dashboard" in app_mode:
        st.subheader(f"🏠 {st.session_state.user_role} Dashboard")
        
        # Pull latest summaries from SQLite
        scans = db_manager.get_all_scans()
        total_scans = len(scans)
        latest_val = scans[0][3] if scans else 0.0
        alerts = check_low_stock()
        
        # Display key summary cards
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown(f"""
                <div class="metric-card">
                    <span style="color: #94a3b8; font-size: 0.85rem;">TOTAL LOGGED SCANS</span>
                    <h2>{total_scans}</h2>
                </div>
            """, unsafe_allow_html=True)
        with col2:
            st.markdown(f"""
                <div class="metric-card">
                    <span style="color: #94a3b8; font-size: 0.85rem;">LATEST SHELF VALUE</span>
                    <h2 style="color: #10b981;">${latest_val:.2f}</h2>
                </div>
            """, unsafe_allow_html=True)
        with col3:
            alert_color = "#ef4444" if alerts else "#10b981"
            alert_text = f"{len(alerts)} Warnings" if alerts else "All OK"
            st.markdown(f"""
                <div class="metric-card">
                    <span style="color: #94a3b8; font-size: 0.85rem;">ALERT STATUS</span>
                    <h2 style="color: {alert_color};">{alert_text}</h2>
                </div>
            """, unsafe_allow_html=True)

        if alerts:
            st.error("### ⚠️ Active Replenishment Warnings")
            for warning in alerts:
                st.markdown(f"- {warning}")
        else:
            st.success("All current shelf inventories are optimal!")

        st.write("---")
        st.write("#### Quick Actions")
        if st.session_state.user_role == "Owner":
            st.info("As Owner, you can add new product mappings in SKU settings, generate reports, or inspect audit logs.")
        else:
            st.info("As Staff, use the sidebar to scan shelves, capture webcam snapshots, and report shelf counts.")

    # ----------------- Inventory List -----------------
    elif app_mode == "📋 Inventory List":
        st.subheader("📋 Central Inventory List")
        scans = db_manager.get_all_scans()
        if scans:
            latest_id = scans[0][0]
            st.write(f"Displaying current stock tallies based on latest **Scan ID: {latest_id}**")
            details = db_manager.get_scan_details(latest_id)
            if details:
                records = []
                for item in details:
                    sku_name, class_id, count, price = item
                    threshold = sku_mapping.get(class_id, {}).get("low_stock_threshold", 0)
                    status = "⚠️ Low Stock" if count < threshold else "✅ OK"
                    records.append({
                        "Product Name": sku_name,
                        "Class ID": class_id,
                        "Current Count": count,
                        "Price": f"${price:.2f}",
                        "Alert Min Target": threshold,
                        "Status": status
                    })
                st.dataframe(pd.DataFrame(records), hide_index=True, use_container_width=True)
                
                # Owner-only edit controls
                if st.session_state.user_role == "Owner":
                    st.write("---")
                    st.write("### ✏️ Edit Product Target thresholds")
                    with st.form("edit_thresholds_form"):
                        cls_to_edit = st.selectbox("Select YOLO Class to edit", options=list(sku_mapping.keys()), format_func=lambda x: sku_mapping[x]["sku_name"])
                        new_threshold = st.number_input("New Warning Limit threshold value", min_value=0, value=int(sku_mapping[cls_to_edit]["low_stock_threshold"]) if cls_to_edit else 5)
                        save_thresh_btn = st.form_submit_button("Update Product Warning threshold")
                        if save_thresh_btn and cls_to_edit:
                            sku_mapping[cls_to_edit]["low_stock_threshold"] = int(new_threshold)
                            save_sku_mapping(sku_mapping)
                            db_manager.log_audit("Owner", f"Modified threshold limit for {cls_to_edit} to {new_threshold}")
                            st.success(f"Successfully updated threshold for {sku_mapping[cls_to_edit]['sku_name']} to {new_threshold}!")
                            st.rerun()
        else:
            st.info("No scanning data logged yet. Run a static image scan to populate records.")


    # ----------------- Static Image Upload -----------------
    elif app_mode == "📷 Static Image Upload":
        st.subheader("📷 Static Image Scanner")
        uploaded_file = st.file_uploader("Upload shelf photograph...", type=["jpg", "jpeg", "png"])
        
        if uploaded_file is not None and detector is not None:
            col1, col2 = st.columns([2, 1])
            with col1:
                st.write("### Shelf Detection View")
                with st.spinner("Analyzing image..."):
                    try:
                        annotated_image, counts = detector.detect_image(uploaded_file)
                        st.image(annotated_image, use_container_width=True)
                    except Exception as ex:
                        st.error(f"Detection failed: {ex}")
                        counts = {}
            with col2:
                st.write("### AI Prediction Tallies")
                if counts:
                    if "adjusted_counts" not in st.session_state:
                        st.session_state.adjusted_counts = counts.copy()
                    
                    st.write("#### ✏️ Override Tallies")
                    for cls_id in list(st.session_state.adjusted_counts.keys()):
                        st.session_state.adjusted_counts[cls_id] = st.number_input(
                            f"Class: {cls_id}",
                            min_value=0,
                            value=int(st.session_state.adjusted_counts[cls_id])
                        )
                        
                    # Calculate sums
                    tally_data = []
                    total_value = 0.0
                    total_items = 0
                    low_stock_triggered = []
                    for cls_id, count in st.session_state.adjusted_counts.items():
                        mapping = sku_mapping.get(cls_id, {"sku_name": f"Unmapped ({cls_id})", "price": 0.0, "low_stock_threshold": 0})
                        sku_name = mapping["sku_name"]
                        price = mapping["price"]
                        subtotal = count * price
                        total_value += subtotal
                        total_items += count
                        tally_data.append({
                            "SKU Name": sku_name,
                            "Count": count,
                            "Subtotal": subtotal,
                            "_price": price,
                            "_class": cls_id
                        })
                        
                    st.write(f"**Total Valuation:** ${total_value:.2f}")
                    if st.button("💾 Log Scan to SQLite"):
                        db_items = []
                        for x in tally_data:
                            db_items.append({
                                'sku_name': x['SKU Name'],
                                'detected_class': x['_class'],
                                'count': x['Count'],
                                'unit_price': x['_price']
                            })
                        db_manager.log_scan(total_items, total_value, db_items)
                        db_manager.log_audit(st.session_state.user_role, f"Logged static image scan containing {total_items} items")
                        st.success("Logged successfully!")
                        st.session_state.pop("adjusted_counts", None)
                        st.rerun()

    # ----------------- Live Detection -----------------
    elif app_mode == "📹 Live Detection":
        st.subheader("📹 Real-time Tracking Feed")
        input_source = st.selectbox("Select Tracker Input Stream", ["Webcam Live Input", "Upload Video File"])
        
        if input_source == "Webcam Live Input":
            st.write("Capture shelf snapshots via your webcam device camera:")
            webcam_image = st.camera_input("Take snap")
            if webcam_image is not None and detector is not None:
                annotated_img, counts = detector.detect_image(webcam_image)
                st.image(annotated_img, use_container_width=True)
                
                tally_data = []
                total_value = 0.0
                total_items = 0
                for cls_id, count in counts.items():
                    mapping = sku_mapping.get(cls_id, {"sku_name": f"Unmapped ({cls_id})", "price": 0.0})
                    total_value += count * mapping["price"]
                    total_items += count
                    tally_data.append({
                        'sku_name': mapping["sku_name"],
                        'detected_class': cls_id,
                        'count': count,
                        'unit_price': mapping["price"]
                    })
                if st.button("💾 Log Webcam Snap to Database"):
                    db_manager.log_scan(total_items, total_value, tally_data)
                    db_manager.log_audit(st.session_state.user_role, f"Logged webcam snapshot scan containing {total_items} items")
                    st.success("Webcam scan saved!")
                    st.rerun()
                    
        else:
            uploaded_video = st.file_uploader("Upload video file...", type=["mp4", "avi", "mov"])
            if uploaded_video is not None:
                temp_file_path = "temp_uploaded_video.mp4"
                with open(temp_file_path, "wb") as f:
                    f.write(uploaded_video.read())
                    
                video_cap = cv2.VideoCapture(temp_file_path)
                st_frame = st.empty()
                tracked_objects = {}
                
                while video_cap.isOpened():
                    ret, frame = video_cap.read()
                    if not ret:
                        break
                    annotated_frame, active_tracks = detector.track_frame(frame)
                    for track_id, class_name in active_tracks.items():
                        tracked_objects[track_id] = class_name
                    st_frame.image(annotated_frame, use_container_width=True)
                video_cap.release()
                os.remove(temp_file_path)
                
                # Format tracked items
                class_counts = {}
                for cls_name in tracked_objects.values():
                    class_counts[cls_name] = class_counts.get(cls_name, 0) + 1
                total_items = sum(class_counts.values())
                total_val = sum(class_counts[cls] * sku_mapping.get(cls, {"price":0.0})["price"] for cls in class_counts)
                
                st.write(f"**Unique Items Tracked:** {total_items} | **Valuation:** ${total_val:.2f}")
                if st.button("💾 Log Video Track to SQL"):
                    db_items = [{'sku_name': sku_mapping.get(cls, {"sku_name": cls})["sku_name"], 'detected_class': cls, 'count': val, 'unit_price': sku_mapping.get(cls, {"price":0.0})["price"]} for cls, val in class_counts.items()]
                    db_manager.log_scan(total_items, total_val, db_items)
                    db_manager.log_audit(st.session_state.user_role, f"Logged tracking video log containing {total_items} items")
                    st.success("Video track logged!")
                    st.rerun()

    # ----------------- SKU Management -----------------
    elif app_mode == "⚙️ SKU Management":
        st.subheader("⚙️ Catalog Configuration Settings")
        if st.session_state.user_role != "Owner":
            st.error("Authorized Owner role is required to modify SKU mappings.")
        else:
            with st.form("add_sku_form"):
                st.write("### Add / Update SKU Mapping")
                class_name = st.text_input("YOLO Class ID (e.g. 'bottle', 'cup')").lower().strip()
                sku_name = st.text_input("Product Name (e.g. 'Pepsi 500ml')")
                price = st.number_input("Retail Unit Price ($)", min_value=0.0, step=0.01)
                threshold = st.number_input("Low Stock Threshold Alert", min_value=0, step=1)
                submit_btn = st.form_submit_button("Save SKU Config")
                
                if submit_btn and class_name and sku_name:
                    sku_mapping[class_name] = {
                        "sku_name": sku_name,
                        "price": price,
                        "low_stock_threshold": int(threshold)
                    }
                    save_sku_mapping(sku_mapping)
                    db_manager.log_audit("Owner", f"Added/Updated SKU Mapping for class: {class_name}")
                    st.success("Successfully configured SKU mapping!")
                    st.rerun()

            with st.form("delete_sku_form"):
                st.write("### Delete SKU Mapping")
                class_to_delete = st.selectbox("Select YOLO Class to delete", options=[""] + list(sku_mapping.keys()))
                delete_btn = st.form_submit_button("Delete SKU Config")
                if delete_btn and class_to_delete:
                    del sku_mapping[class_to_delete]
                    save_sku_mapping(sku_mapping)
                    db_manager.log_audit("Owner", f"Deleted SKU Mapping for class: {class_to_delete}")
                    st.success("SKU Mapping deleted!")
                    st.rerun()

    # ----------------- Before/After Comparison -----------------
    elif app_mode == "⚖️ Before/After Comparison":
        st.subheader("⚖️ Shelf Comparison Audit")
        col_img1, col_img2 = st.columns(2)
        with col_img1:
            st.write("#### Baseline Snapshot (Morning)")
            img1 = st.file_uploader("Upload baseline snapshot...", type=["jpg","png","jpeg"], key="c_img1")
        with col_img2:
            st.write("#### Target Snapshot (Evening)")
            img2 = st.file_uploader("Upload target snapshot...", type=["jpg","png","jpeg"], key="c_img2")
            
        if img1 and img2:
            col_res1, col_res2 = st.columns(2)
            with col_res1:
                annotated1, counts1 = detector.detect_image(img1)
                st.image(annotated1, caption="Baseline Shelf", use_container_width=True)
            with col_res2:
                annotated2, counts2 = detector.detect_image(img2)
                st.image(annotated2, caption="Target Shelf", use_container_width=True)
                
            all_classes = set(list(counts1.keys()) + list(counts2.keys()))
            diff_data = []
            total_rev = 0.0
            for cls_id in all_classes:
                cnt1 = counts1.get(cls_id, 0)
                cnt2 = counts2.get(cls_id, 0)
                sold = max(0, cnt1 - cnt2)
                mapping = sku_mapping.get(cls_id, {"sku_name": cls_id, "price": 0.0})
                rev = sold * mapping["price"]
                total_rev += rev
                diff_data.append({
                    "SKU Name": mapping["sku_name"],
                    "Baseline Count": cnt1,
                    "Target Count": cnt2,
                    "Quantity Sold": sold,
                    "Estimated Revenue": f"${rev:.2f}"
                })
            st.dataframe(pd.DataFrame(diff_data), hide_index=True, use_container_width=True)
            st.write(f"**Total Revenue Generated:** ${total_rev:.2f}")

    # ----------------- Reports & Analytics -----------------
    elif app_mode == "📈 Reports & Analytics":
        st.subheader("📈 Analytics & Reporting Dashboard")
        if st.session_state.user_role != "Owner":
            st.error("Owner clearance is required to view financial reports.")
        else:
            scans = db_manager.get_all_scans()
            if scans:
                df_scans = pd.DataFrame(scans, columns=["Scan ID", "Timestamp", "Total Items", "Total Value ($)"])
                st.write("### Valuation Trends Over Time")
                fig_trend = px.line(df_scans, x="Timestamp", y="Total Value ($)", title="Retail Shelf Value Trends", markers=True)
                st.plotly_chart(fig_trend, use_container_width=True)
                
                st.write("### Past Scanning Logs")
                st.dataframe(df_scans, hide_index=True, use_container_width=True)
                
                # Exporters
                csv_history = df_scans.to_csv(index=False)
                st.download_button(
                    label="📥 Export History Log to CSV",
                    data=csv_history,
                    file_name="retail_history_logs.csv",
                    mime="text/csv"
                )
            else:
                st.info("No scanning history recorded in SQLite.")

    # ----------------- Notifications & Alerts -----------------
    elif app_mode == "🔔 Notifications & Alerts":
        st.subheader("🔔 Low-Stock Alerts Panel")
        alerts = check_low_stock()
        
        if alerts:
            st.error(f"⚠️ {len(alerts)} Inventory items are below their target targets:")
            for item in alerts:
                st.write(f"- {item}")
        else:
            st.success("All catalog products are fully stocked!")

        if st.session_state.user_role == "Owner":
            st.write("---")
            st.write("### ⚙️ Configure Warning Notification Channels")
            CONFIG_FILE = "alert_config.json"
            if os.path.exists(CONFIG_FILE):
                with open(CONFIG_FILE, "r") as f:
                    alert_config = json.load(f)
            else:
                alert_config = {
                    "email_enabled": False,
                    "email_address": "manager@store.com",
                    "telegram_enabled": False,
                    "telegram_chat_id": "@SmartInventoryAlerts"
                }
                
            with st.form("owner_alert_config_form"):
                email_enabled = st.checkbox("Enable Automated Email Reports (SMTP)", value=alert_config["email_enabled"])
                email_address = st.text_input("Manager Email Address", value=alert_config["email_address"])
                telegram_enabled = st.checkbox("Enable Instant Telegram Mobile Push Alerts", value=alert_config["telegram_enabled"])
                telegram_chat_id = st.text_input("Telegram Chat ID / Username", value=alert_config["telegram_chat_id"])
                save_cfg = st.form_submit_button("Save Notification Settings")
                
                if save_cfg:
                    new_cfg = {
                        "email_enabled": email_enabled,
                        "email_address": email_address,
                        "telegram_enabled": telegram_enabled,
                        "telegram_chat_id": telegram_chat_id
                    }
                    with open(CONFIG_FILE, "w") as f:
                        json.dump(new_cfg, f, indent=2)
                    db_manager.log_audit("Owner", "Updated notification channel configurations")
                    st.success("Successfully saved notification channel credentials!")
                    st.rerun()


    # ----------------- Audit Logs -----------------
    elif app_mode == "📜 Audit Logs":
        st.subheader("📜 System Audit Logs")
        if st.session_state.user_role != "Owner":
            st.error("Owner validation is required to view operations audit logs.")
        else:
            logs = db_manager.get_audit_logs()
            if logs:
                df_logs = pd.DataFrame(logs, columns=["Log ID", "Timestamp", "User Role", "Action Description"])
                st.dataframe(df_logs, hide_index=True, use_container_width=True)
            else:
                st.info("No audit logs logged in database.")

    elif app_mode == "🔧 Settings":
        st.subheader("🔧 System Configurations")
        
        # Theme Settings Toggle (Available to both Owner and Staff)
        st.write("---")
        st.write("### 🌓 Display Theme Preferences")
        theme_choice = st.selectbox(
            "Select Dashboard Color Scheme Theme", 
            ["Light Mode", "Dark Mode"], 
            index=0 if st.session_state.app_theme == "Light Mode" else 1
        )
        if theme_choice != st.session_state.app_theme:
            st.session_state.app_theme = theme_choice
            st.rerun()

        # Backup section
        st.write("---")
        st.write("### 💾 Backup & Restore Catalog Mappings")
        col_b1, col_b2, col_b3 = st.columns(3)
        with col_b1:
            st.write("Export Configurations")
            json_backup_str = json.dumps(sku_mapping, indent=2)
            st.download_button("📤 Download Backup (.json)", data=json_backup_str, file_name="sku_mapping_backup.json", mime="application/json")
        with col_b2:
            st.write("Restore Configurations")
            uploaded_backup = st.file_uploader("Upload JSON", type=["json"])
            if uploaded_backup is not None:
                try:
                    restored_map = json.load(uploaded_backup)
                    save_sku_mapping(restored_map)
                    st.success("SKU Catalog configurations restored!")
                except Exception as e:
                    st.error(f"Restore failed: {e}")
        with col_b3:
            st.write("Bulk Import Catalog")
            uploaded_csv = st.file_uploader("Upload CSV", type=["csv"])
            if uploaded_csv is not None:
                try:
                    df = pd.read_csv(uploaded_csv)
                    for _, row in df.iterrows():
                        sku_mapping[str(row["YOLO Class ID"]).strip().lower()] = {
                            "sku_name": str(row["Product Name"]).strip(),
                            "price": float(row["Price"]),
                            "low_stock_threshold": int(row["Threshold"])
                        }
                    save_sku_mapping(sku_mapping)
                    st.success("Successfully imported items from CSV!")
                except Exception as e:
                    st.error(f"CSV import failed: {e}")

        # Danger zone
        if st.session_state.user_role == "Owner":
            st.write("---")
            st.write("### ⚠️ Admin Reset Operations")
            if st.button("🗑️ Reset SQLite Database Records"):
                db_manager.clear_all_scans()
                db_manager.log_audit("Owner", "Reset and wiped SQLite database records")
                st.success("SQLite logs database reset successfully!")
                st.rerun()

