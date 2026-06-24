import streamlit as st
import cv2
import json
import os
import pandas as pd
from detector import InventoryDetector
from db_manager import DBManager
import plotly.express as px
from report_generator import generate_pdf_report, generate_csv_report



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
app_mode = st.sidebar.radio("Go to", ["Static Image Upload", "Webcam & Video Tracking", "Before/After Comparison", "SKU Management", "Alert Settings & Logs", "Analytics & History"])

# Alert notifier helper (simulated SMTP / Telegram)
def send_alert_notification(channel, recipient, message):
    # Log alert output to simulate SMTP/Telegram API dispatch
    st.info(f"🚀 [Notification Sent via {channel} to {recipient}]: {message}")

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
                # Store detected counts in session state to allow manual modifications
                if "adjusted_counts" not in st.session_state or st.button("🔄 Reset to AI Counts"):
                    st.session_state.adjusted_counts = counts.copy()

                # Add adjustment controls
                st.write("#### ✏️ Edit Quantities (Manual Override)")
                for cls_id in list(st.session_state.adjusted_counts.keys()):
                    mapping = sku_mapping.get(cls_id, {"sku_name": f"Unmapped ({cls_id})"})
                    st.session_state.adjusted_counts[cls_id] = st.number_input(
                        f"Quantity for {mapping['sku_name']}",
                        min_value=0,
                        value=int(st.session_state.adjusted_counts[cls_id]),
                        key=f"adj_{cls_id}"
                    )

                # Compile table mapping counts to SKUs using adjusted counts
                tally_data = []
                total_value = 0.0
                total_items = 0
                low_stock_triggered = []
                
                for detected_class, count in st.session_state.adjusted_counts.items():
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
                    if count < threshold:
                        is_low_stock = "⚠️ Low Stock"
                        low_stock_triggered.append(f"{sku_name} (Current: {count} | Min: {threshold})")
                    else:
                        is_low_stock = "✅ OK"
                    
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
                st.write("### Adjusted Summary")
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

                # Show visual warnings
                if low_stock_triggered:
                    st.error("### ⚠️ Low-Stock Alerts Detected!")
                    for item in low_stock_triggered:
                        st.markdown(f"- **{item}** requires replenishment.")
                
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
                        
                        # Trigger simulated notification if configurations exist
                        if low_stock_triggered and os.path.exists("alert_config.json"):
                            with open("alert_config.json", "r") as f:
                                alert_cfg = json.load(f)
                            if alert_cfg.get("email_enabled"):
                                send_alert_notification("Email/SMTP", alert_cfg["email_address"], f"Low Stock Warning: {', '.join(low_stock_triggered)}")
                            if alert_cfg.get("telegram_enabled"):
                                send_alert_notification("Telegram Bot", alert_cfg["telegram_chat_id"], f"Low Stock Warning: {', '.join(low_stock_triggered)}")
                    except Exception as e:
                        st.error(f"Failed to log scan: {e}")

                
                # Report downloads layout
                st.write("---")
                st.write("### 📝 Export Inventory Reports")
                col_pdf, col_csv = st.columns(2)
                with col_pdf:
                    try:
                        pdf_data = generate_pdf_report(tally_data, total_items, total_value)
                        st.download_button(
                            label="📄 Download PDF Report",
                            data=pdf_data,
                            file_name="inventory_report.pdf",
                            mime="application/pdf"
                        )
                    except Exception as ex:
                        st.error(f"Failed to build PDF download: {ex}")
                with col_csv:
                    try:
                        csv_data = generate_csv_report(tally_data)
                        st.download_button(
                            label="📊 Download CSV Report",
                            data=csv_data,
                            file_name="inventory_report.csv",
                            mime="text/csv"
                        )
                    except Exception as ex:
                        st.error(f"Failed to build CSV download: {ex}")
            else:
                st.info("No retail products detected in this snapshot.")


elif app_mode == "Webcam & Video Tracking":
    st.subheader("📹 Video Tracking & Live Webcam Inventory")
    
    input_source = st.radio("Choose Input Source", ["Pre-recorded Video File", "Live Webcam Shelf Snapshot"])

    if input_source == "Pre-recorded Video File":
        st.write("Process pre-recorded videos to track inventory items. Unique IDs will prevent double-counting of objects.")
        uploaded_video = st.file_uploader("Upload video file...", type=["mp4", "avi", "mov"])
        
        if uploaded_video is not None and detector is not None:
            temp_file_path = "temp_video.mp4"
            with open(temp_file_path, "wb") as f:
                f.write(uploaded_video.read())
                
            video_cap = cv2.VideoCapture(temp_file_path)
            st_frame = st.empty()
            st_stats = st.empty()
            tracked_objects = {}
            
            while video_cap.isOpened():
                ret, frame = video_cap.read()
                if not ret:
                    break
                    
                annotated_frame, active_tracks = detector.track_frame(frame)
                for track_id, class_name in active_tracks.items():
                    tracked_objects[track_id] = class_name
                    
                st_frame.image(annotated_frame, use_container_width=True)
                
                class_counts = {}
                for class_name in tracked_objects.values():
                    class_counts[class_name] = class_counts.get(class_name, 0) + 1
                    
                tally_data = []
                total_value = 0.0
                total_items = 0
                
                for detected_class, count in class_counts.items():
                    mapping = sku_mapping.get(detected_class, {
                        "sku_name": f"Unmapped ({detected_class})",
                        "price": 0.0,
                        "low_stock_threshold": 0
                    })
                    sku_name = mapping["sku_name"]
                    price = mapping["price"]
                    subtotal = count * price
                    total_value += subtotal
                    total_items += count
                    
                    tally_data.append({
                        "SKU Name": sku_name,
                        "Total Tracked": count,
                        "Price": f"${price:.2f}",
                        "Total Value": f"${subtotal:.2f}"
                    })
                    
                with st_stats.container():
                    st.write("### Real-time Tracking Statistics")
                    st.markdown(f"**Total Unique Items Tracked:** {total_items} | **Cumulative Valuation:** ${total_value:.2f}")
                    if tally_data:
                        st.dataframe(pd.DataFrame(tally_data), hide_index=True, use_container_width=True)
                        
            video_cap.release()
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)
                
            if st.button("💾 Log Video Scanning Results to DB"):
                db_items = []
                class_counts = {}
                for class_name in tracked_objects.values():
                    class_counts[class_name] = class_counts.get(class_name, 0) + 1
                    
                total_value = 0.0
                total_items = 0
                for detected_class, count in class_counts.items():
                    mapping = sku_mapping.get(detected_class, {
                        "sku_name": f"Unmapped ({detected_class})",
                        "price": 0.0,
                        "low_stock_threshold": 0
                    })
                    sku_name = mapping["sku_name"]
                    price = mapping["price"]
                    total_value += count * price
                    total_items += count
                    db_items.append({
                        'sku_name': sku_name,
                        'detected_class': detected_class,
                        'count': count,
                        'unit_price': price
                    })
                try:
                    db_manager.log_scan(total_items, total_value, db_items)
                    st.success("Successfully logged track counts to SQLite!")
                except Exception as e:
                    st.error(f"Failed to log: {e}")

    else:
        st.write("Capture a snapshot of your physical shelf directly using your device's camera to run item detections.")
        webcam_image = st.camera_input("Capture shelf snapshot via webcam")
        
        if webcam_image is not None and detector is not None:
            col1, col2 = st.columns([2, 1])
            with col1:
                st.write("### Webcam Frame Capture")
                with st.spinner("Processing webcam frame..."):
                    try:
                        annotated_image, counts = detector.detect_image(webcam_image)
                        st.image(annotated_image, caption="Processed Webcam Snapshot", use_container_width=True)
                    except Exception as e:
                        st.error(f"Error processing frame: {e}")
                        counts = {}
            with col2:
                st.write("### Current Counts & Evaluation")
                if counts:
                    tally_data = []
                    total_value = 0.0
                    total_items = 0
                    low_stock_triggered = []
                    
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
                        
                        if count < threshold:
                            is_low_stock = "⚠️ Low Stock"
                            low_stock_triggered.append(f"{sku_name} (Current: {count} | Min: {threshold})")
                        else:
                            is_low_stock = "✅ OK"
                        
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
                    
                    st.markdown(f"**Total Items:** {total_items} | **Valuation:** ${total_value:.2f}")
                    st.dataframe(pd.DataFrame(tally_data)[["SKU Name", "Count", "Price ($)", "Subtotal", "Status"]], hide_index=True, use_container_width=True)
                    
                    if low_stock_triggered:
                        st.error("⚠️ Low stock items found!")
                        for warning in low_stock_triggered:
                            st.markdown(f"- {warning}")
                            
                    if st.button("💾 Log Webcam Scan to DB"):
                        db_items = [{'sku_name': item['SKU Name'], 'detected_class': item['Detected Class'], 'count': item['Count'], 'unit_price': item['_raw_price']} for item in tally_data]
                        try:
                            db_manager.log_scan(total_items, total_value, db_items)
                            st.success("Logged scan successfully!")
                        except Exception as e:
                            st.error(f"Failed to log: {e}")
                else:
                    st.info("No items detected in webcam snapshot.")


elif app_mode == "Before/After Comparison":
    st.subheader("⚖️ Shelf Comparison (Morning vs. Evening)")
    st.write("Upload two snapshots of the same shelf to estimate items sold and computed revenue.")
    
    col_img1, col_img2 = st.columns(2)
    
    with col_img1:
        st.write("#### 1. Baseline Shelf (e.g., Morning)")
        img1_file = st.file_uploader("Upload morning snapshot...", type=["jpg", "png", "jpeg"], key="morning_scan")
        
    with col_img2:
        st.write("#### 2. Current Shelf (e.g., Evening)")
        img2_file = st.file_uploader("Upload evening snapshot...", type=["jpg", "png", "jpeg"], key="evening_scan")
        
    if img1_file and img2_file and detector is not None:
        col_res1, col_res2 = st.columns(2)
        
        with col_res1:
            annotated1, counts1 = detector.detect_image(img1_file)
            st.image(annotated1, caption="Morning Shelf Scan", use_container_width=True)
            
        with col_res2:
            annotated2, counts2 = detector.detect_image(img2_file)
            st.image(annotated2, caption="Evening Shelf Scan", use_container_width=True)
            
        # Calculation of diff
        all_classes = set(list(counts1.keys()) + list(counts2.keys()))
        diff_data = []
        total_revenue_est = 0.0
        
        for cls_id in all_classes:
            cnt1 = counts1.get(cls_id, 0)
            cnt2 = counts2.get(cls_id, 0)
            sold = max(0, cnt1 - cnt2)
            
            mapping = sku_mapping.get(cls_id, {"sku_name": f"Unmapped ({cls_id})", "price": 0.0})
            price = mapping["price"]
            revenue = sold * price
            total_revenue_est += revenue
            
            diff_data.append({
                "SKU Name": mapping["sku_name"],
                "Morning Count": cnt1,
                "Evening Count": cnt2,
                "Estimated Sold": sold,
                "Unit Price": f"${price:.2f}",
                "Estimated Revenue": f"${revenue:.2f}"
            })
            
        st.write("### 📊 Difference Sales Analysis")
        st.dataframe(pd.DataFrame(diff_data), hide_index=True, use_container_width=True)
        st.markdown(f"#### 💰 Estimated Revenue Generated between Scans: **${total_revenue_est:.2f}**")

elif app_mode == "SKU Management":
    st.subheader("⚙️ SKU Catalog Configuration")
    st.write("Configure details mapping YOLO classification classes to retail SKUs.")
    
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

    # Form to delete mappings
    with st.form("delete_sku_form"):
        st.write("### Delete SKU Mapping")
        class_to_delete = st.selectbox("Select YOLO Class to delete", options=[""] + list(sku_mapping.keys()))
        delete_btn = st.form_submit_button("Delete SKU Config")
        if delete_btn and class_to_delete:
            del sku_mapping[class_to_delete]
            save_sku_mapping(sku_mapping)
            st.success(f"Removed SKU mapping for class '{class_to_delete}'.")
            st.rerun()

    st.write("### Active SKU Catalog")
    if sku_mapping:
        icons_map = {
            "bottle": "🥤",
            "cup": "☕",
            "box": "📦",
            "can": "🥫",
            "packet": "✉️",
            "bowl": "🥣"
        }
        
        cols = st.columns(3)
        for i, (cls_name, info) in enumerate(sku_mapping.items()):
            col_idx = i % 3
            with cols[col_idx]:
                icon = icons_map.get(cls_name, "🛍️")
                st.markdown(f"""
                    <div style="background-color: #1e293b; padding: 1.25rem; border-radius: 8px; border: 1px solid #334155; margin-bottom: 15px;">
                        <div style="font-size: 2rem; margin-bottom: 5px;">{icon}</div>
                        <h4 style="margin: 0; color: #f8fafc;">{info['sku_name']}</h4>
                        <p style="margin: 5px 0; color: #94a3b8; font-size: 0.85rem;">Class ID: <code>{cls_name}</code></p>
                        <div style="display: flex; justify-content: space-between; margin-top: 10px;">
                            <span style="color: #10b981; font-weight: bold;">${info['price']:.2f}</span>
                            <span style="color: #f59e0b; font-size: 0.85rem;">Min Alert: {info['low_stock_threshold']}</span>
                        </div>
                    </div>
                """, unsafe_allow_html=True)
                
        st.write("---")
        st.write("#### Catalog Table View")
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



elif app_mode == "Alert Settings & Logs":
    st.subheader("🔔 Notification Channels & System Alerts")
    
    # Load or initialize alert configs
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
        
    with st.form("alert_config_form"):
        st.write("### Configure Warning Triggers")
        email_enabled = st.checkbox("Enable Automated Email Reports (SMTP)", value=alert_config["email_enabled"])
        email_address = st.text_input("Manager Email Address", value=alert_config["email_address"])
        
        telegram_enabled = st.checkbox("Enable Instant Telegram Mobile Push Alerts", value=alert_config["telegram_enabled"])
        telegram_chat_id = st.text_input("Telegram Chat ID / Username", value=alert_config["telegram_chat_id"])
        
        save_cfg = st.form_submit_button("Save Notification Settings")
        if save_cfg:
            alert_config = {
                "email_enabled": email_enabled,
                "email_address": email_address,
                "telegram_enabled": telegram_enabled,
                "telegram_chat_id": telegram_chat_id
            }
            with open(CONFIG_FILE, "w") as f:
                json.dump(alert_config, f, indent=2)
            st.success("Successfully saved notification channel credentials!")

    # Database reset danger section
    st.write("---")
    st.write("### ⚠️ Danger Zone")
    
    st.write("#### Delete a Specific Scan Record")
    scans_list = db_manager.get_all_scans()
    if scans_list:
        scan_ids = [s[0] for s in scans_list]
        with st.form("delete_single_scan_form"):
            scan_id_to_del = st.selectbox("Select Scan ID to delete", options=[""] + scan_ids)
            del_single_btn = st.form_submit_button("🗑️ Delete Selected Scan")
            if del_single_btn and scan_id_to_del:
                try:
                    db_manager.delete_single_scan(scan_id_to_del)
                    st.success(f"Successfully deleted Scan ID: {scan_id_to_del}!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Failed to delete scan: {e}")
    else:
        st.info("No scans available to delete.")
        
    st.write("#### Reset Entire Database")
    st.warning("Clearing database scan history is irreversible!")
    if st.button("🗑️ Reset & Clear Scan Database Logs"):
        try:
            db_manager.clear_all_scans()
            st.success("Successfully cleared all scanning history records!")
        except Exception as e:
            st.error(f"Failed to clear database logs: {e}")



elif app_mode == "Analytics & History":
    st.subheader("📈 Historical Trends & Scan Logs")
    st.write("Analyze previous scans stored inside the SQLite database.")
    
    scans = db_manager.get_all_scans()
    
    if scans:
        df_scans = pd.DataFrame(scans, columns=["Scan ID", "Timestamp", "Total Items", "Total Value ($)"])
        df_scans["ParsedDate"] = pd.to_datetime(df_scans["Timestamp"]).dt.date
        
        st.write("### 🔍 Filter Scan History")
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            start_date = st.date_input("Start Date", value=df_scans["ParsedDate"].min())
        with col_f2:
            end_date = st.date_input("End Date", value=df_scans["ParsedDate"].max())
            
        df_filtered = df_scans[(df_scans["ParsedDate"] >= start_date) & (df_scans["ParsedDate"] <= end_date)]
        
        if not df_filtered.empty:
            col1, col2 = st.columns(2)
            with col1:
                st.write("### Retail Stock Value Over Time")
                fig_val = px.line(df_filtered, x="Timestamp", y="Total Value ($)", title="Inventory Valuation Trend", markers=True)
                st.plotly_chart(fig_val, use_container_width=True)
                
            with col2:
                st.write("### Total Item Count Over Time")
                fig_count = px.bar(df_filtered, x="Timestamp", y="Total Items", title="Product Count Logs")
                st.plotly_chart(fig_count, use_container_width=True)
                
            st.write("### Historical Log")
            search_query = st.text_input("🔍 Search logs by Scan ID...", value="")
            
            df_display = df_filtered.copy()
            if search_query.strip():
                df_display = df_display[df_display["Scan ID"].astype(str).str.contains(search_query.strip())]
                
            st.dataframe(df_display[["Scan ID", "Timestamp", "Total Items", "Total Value ($)"]], hide_index=True, use_container_width=True)
            
            # Export history log button
            csv_history = df_display[["Scan ID", "Timestamp", "Total Items", "Total Value ($)"]].to_csv(index=False)
            st.download_button(
                label="📥 Export History Log to CSV",
                data=csv_history,
                file_name="inventory_history_logs.csv",
                mime="text/csv"
            )
            
            # Drill-down details section
            st.write("---")
            st.write("### 🔍 Itemized Scan Drill-Down")
            selected_scan_id = st.selectbox(
                "Select a Scan ID to inspect detailed product listings",
                options=df_display["Scan ID"].tolist()
            )
            
            if selected_scan_id:
                details = db_manager.get_scan_details(selected_scan_id)
                if details:
                    df_details = pd.DataFrame(details, columns=["SKU Name", "Class ID", "Count", "Unit Price"])
                    df_details["Subtotal"] = df_details["Count"] * df_details["Unit Price"]
                    
                    # Formatting values for presentation
                    df_details["Unit Price"] = df_details["Unit Price"].map(lambda x: f"${x:.2f}")
                    df_details["Subtotal"] = df_details["Subtotal"].map(lambda x: f"${x:.2f}")
                    
                    st.dataframe(df_details, hide_index=True, use_container_width=True)
                else:
                    st.info("No item details found for the selected Scan ID.")

        else:
            st.warning("No records found in the selected date range.")

    else:
        st.info("No scan history logged to SQLite database yet.")



else:
    st.info("The live webcam feed component is scheduled for development in Phase 3.")
