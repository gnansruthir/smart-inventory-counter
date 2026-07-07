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
base_dir = os.path.dirname(os.path.abspath(__file__))
SKU_FILE = os.path.join(base_dir, "sku_mapping.json")
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
    import importlib
    import detector
    importlib.reload(detector)
    return detector.InventoryDetector()

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

if "app_lang" not in st.session_state:
    st.session_state.app_lang = "English"

# Translation Dictionary
TRANSLATIONS = {
    "English": {
        "title": "Smart Inventory Counter System",
        "Sign In": "Sign In",
        "Sign Up": "Sign Up",
        "Username": "Username",
        "Password": "Password",
        "Choose Username": "Choose Username",
        "Choose Password": "Choose Password",
        "Select Your Role": "Select Your Role",
        "Create Account": "Create Account",
        "Owner": "Owner",
        "Staff": "Staff",
        "Logged in": "Logged in",
        "Navigate View": "Navigate View",
        "Logout": "Logout",
        "Welcome": "Welcome",
        "Loading panel...": "Loading panel...",
        "Account not found": "Account not found. Please create an account first.",
        "Specify username password": "Please specify both a username and password.",
        "Invalid owner credentials": "Invalid registration credentials for Owner role.",
        "Invalid staff credentials": "Invalid registration credentials for Staff role.",
        "Account created successfully": "Account created successfully! You can now sign in using the Sign In tab.",
        "Account already created": "Account already created! You can now sign in using the Sign In tab.",
        "TOTAL LOGGED SCANS": "TOTAL LOGGED SCANS",
        "LATEST SHELF VALUE": "LATEST SHELF VALUE",
        "ALERT STATUS": "ALERT STATUS",
        "Warnings": "Warnings",
        "All OK": "All OK",
        "Active Replenishment Warnings": "Active Replenishment Warnings",
        "Optimal shelf inventories": "All current shelf inventories are optimal!",
        "Owner Dashboard": "Owner Dashboard",
        "Staff Dashboard": "Staff Dashboard",
        "Video Detection": "Video Detection",
        "Image Detection": "Image Detection",
        "Items Count": "Items Count",
        "Reports & Analytics": "Reports & Analytics",
        "Low stock count": "Low stock count",
        "Audit Logs": "Audit Logs",
        "Settings": "Settings",
        "Product Name": "Product Name",
        "Class ID": "Class ID",
        "Current Count": "Current Count",
        "Price": "Price",
        "Min count to be in shelf": "Min count to be in shelf",
        "Status": "Status",
        "Low Stock": "Low Stock",
        "Optimal Stock": "Optimal Stock",
        "Edit Product Target thresholds": "Edit Product Target thresholds",
        "Select YOLO Class to edit": "Select YOLO Class to edit",
        "New Warning Limit threshold value": "New Warning Limit threshold value",
        "Update Product Warning threshold": "Update Product Warning threshold",
        "Successfully updated threshold": "Successfully updated threshold for",
        "to": "to",
        "No scanning data logged yet": "No scanning data logged yet. Run a static image scan to populate records.",
        "Static Image Scanner": "Image Scan",
        "Upload shelf photograph": "Upload shelf photograph...",
        "Shelf Detection View": "Shelf Detection View",
        "Analyzing image": "Analyzing image...",
        "Detection failed": "Detection failed",
        "AI Prediction Tallies": "AI Prediction Tallies",
        "Override Tallies": "Override Tallies",
        "Class": "Class",
        "Total Valuation": "Total Valuation",
        "Log Scan to SQLite": "Log Scan to SQLite",
        "Logged successfully": "Logged successfully!",
        "Real-time Tracking Feed": "Video Scan",
        "Select Tracker Input Stream": "Select Tracker Input Stream",
        "Webcam Live Input": "Webcam Live Input",
        "Upload Video File": "Upload Video File",
        "Capture shelf snapshots": "Capture shelf snapshots via your webcam device camera:",
        "Take snap": "Take snap",
        "Log Webcam Snap to Database": "Log Webcam Snap to Database",
        "Webcam scan saved": "Webcam scan saved!",
        "Upload video file": "Upload video file...",
        "Unique Items Tracked": "Items Counted",
        "Valuation": "Total Value",
        "Log Video Track to SQL": "Log Video Track to SQL",
        "Video track logged": "Video track logged!",
        "Validated": "Validated",
        "Catalog Configuration Settings": "Item List",
        "Authorized Owner role required": "Authorized Owner role is required to modify SKU mappings.",
        "Add / Update SKU Mapping": "Add / Update Item",
        "YOLO Class ID": "Item",
        "Product Name Input": "Product Name (e.g. 'Pepsi 500ml')",
        "Retail Unit Price (₹)": "Retail Unit Price (₹)",
        "Low Stock Threshold Alert": "Min Item",
        "Save SKU Config": "Save Item",
        "Successfully configured SKU mapping": "Successfully configured SKU mapping!",
        "Delete SKU Mapping": "Delete Item",
        "Select YOLO Class to delete": "Select YOLO Class to delete",
        "Delete SKU Config": "Delete Item",
        "SKU Mapping deleted": "SKU Mapping deleted!",
        "Shelf Comparison Audit": "Shelf Comparison Audit",
        "Baseline Snapshot (Morning)": "Baseline Snapshot (Morning)",
        "Upload baseline snapshot": "Upload baseline snapshot...",
        "Target Snapshot (Evening)": "Target Snapshot (Evening)",
        "Upload target snapshot": "Upload target snapshot...",
        "Baseline Shelf": "Baseline Shelf",
        "Target Shelf": "Target Shelf",
        "Baseline Count": "Baseline Count",
        "Target Count": "Target Count",
        "Quantity Sold": "Quantity Sold",
        "Estimated Revenue": "Estimated Revenue",
        "Total Revenue Generated": "Total Revenue Generated",
        "Analytics & Reporting Dashboard": "Analytics & Reporting Dashboard",
        "Owner clearance required": "Owner clearance is required to view financial reports.",
        "Valuation Trends Over Time": "Valuation Trends Over Time",
        "Retail Shelf Value Trends": "Retail Shelf Value Trends",
        "Past Scanning Logs": "Past Scanning Logs",
        "Export History Log to CSV": "Export History Log to CSV",
        "No scanning history recorded": "No scanning history recorded in SQLite.",
        "Inventory items below target": "Inventory items are below their target targets:",
        "All catalog products stocked": "All catalog products are fully stocked!",
        "Configure Warning Notification Channels": "Configure Warning Notification Channels",
        "Enable Automated Email Reports": "Enable Automated Email Reports (SMTP)",
        "Manager Email Address": "Manager Email Address",
        "Enable Instant Telegram Mobile Push Alerts": "Enable Instant Telegram Mobile Push Alerts",
        "Telegram Chat ID": "Telegram Chat ID / Username",
        "Save Notification Settings": "Save Notification Settings",
        "Successfully saved notification channel": "Successfully saved notification channel credentials!",
        "System Audit Logs": "System Audit Logs",
        "Owner validation required": "Owner validation is required to view operations audit logs.",
        "No audit logs": "No audit logs logged in database.",
        "System Configurations": "System Configurations",
        "Display Theme Preferences": "Display Theme Preferences",
        "Select Dashboard Color Scheme Theme": "Select Dashboard Color Scheme Theme",
        "Light Mode": "Light Mode",
        "Dark Mode": "Dark Mode",
        "Backup & Restore Catalog Mappings": "Backup & Restore Catalog Mappings",
        "Export Configurations": "Export Configurations",
        "Download Backup": "Download Backup (.json)",
        "Restore Configurations": "Restore Configurations",
        "Upload JSON": "Upload JSON",
        "SKU Catalog configurations restored": "SKU Catalog configurations restored!",
        "Restore failed": "Restore failed",
        "Bulk Import Catalog": "Bulk Import Catalog",
        "Upload CSV": "Upload CSV",
        "Successfully imported items from CSV": "Successfully imported items from CSV!",
        "CSV import failed": "CSV import failed",
        "Admin Reset Operations": "Admin Reset Operations",
        "Reset SQLite Database Records": "Reset SQLite Database Records",
        "SQLite logs database reset successfully": "SQLite logs database reset successfully!",
        "Scan ID": "Scan ID",
        "Timestamp": "Timestamp",
        "Total Items": "Total Items",
        "Total Value (₹)": "Total Value (₹)",
        "Before/After Comparison": "Before/After Comparison",
        "Sensitivity": "Model Sensitivity (Lower values detect items more easily)",
        "Low stock alert toast": "Low stock detected! Please restock the shelf.",
        "Scan Summary Breakdown": "Summary",
        "items": "items",
        "Scan History Logs": "Scan History Logs",
        "Current SKU Catalog": "Current Items",
        "Deleted SKUs History": "Deleted SKU History",
        "Export Reports Title": "Export Latest Scan Report",
        "Export PDF": "Export PDF",
        "Export CSV": "Export CSV",
        "Item List": "Item List",
        "Items Counted": "Items Counted",
        "Total Value": "Total Value",
        "Item": "Item",
        "Min Item": "Min Item"
    },
    "Tamil": {
        "title": "ஸ்மார்ட் சரக்குக் கணக்கீட்டு அமைப்பு",
        "Sign In": "உள்நுழைக",
        "Sign Up": "பதிவு செய்க",
        "Username": "பயனர் பெயர்",
        "Password": "கடவுச்சொல்",
        "Choose Username": "பயனர் பெயரைத் தேர்ந்தெடுக்கவும்",
        "Choose Password": "கடவுச்சொல்லைத் தேர்ந்தெடுக்கவும்",
        "Select Your Role": "உங்கள் பங்கினைத் தேர்ந்தெடுக்கவும்",
        "Create Account": "கணக்கை உருவாக்கு",
        "Owner": "உரிமையாளர்",
        "Staff": "பணியாளர்",
        "Logged in": "உள்நுழைந்துள்ளவர்",
        "Navigate View": "வழிசெலுத்தல் பார்வை",
        "Logout": "வெளியேறு",
        "Welcome": "வரவேற்கிறோம்",
        "Loading panel...": "பேனல் ஏற்றப்படுகிறது...",
        "Account not found": "கணக்கு காணப்படவில்லை. முதலில் ஒரு கணக்கை உருவாக்கவும்.",
        "Specify username password": "பயனர் பெயர் மற்றும் கடவுச்சொல் இரண்டையும் குறிப்பிடவும்.",
        "Invalid owner credentials": "உரிமையாளர் பங்கிற்கான தவறான பதிவுச் சான்றுகள்.",
        "Invalid staff credentials": "பணியாளர் பங்கிற்கான தவறான பதிவுச் சான்றுகள்.",
        "Account created successfully": "கணக்கு வெற்றிகரமாக உருவாக்கப்பட்டது! உள்நுழைவு தாவலைப் பயன்படுத்தி இப்போது உள்நுழையலாம்.",
        "Account already created": "கணக்கு ஏற்கனவே உருவாக்கப்பட்டது! உள்நுழைவு தாவலைப் பயன்படுத்தி இப்போது உள்நுழையலாம்.",
        "TOTAL LOGGED SCANS": "மொத்த பதிவு செய்யப்பட்ட ஸ்கான்கள்",
        "LATEST SHELF VALUE": "சமீபத்திய அலமாரி மதிப்பு",
        "ALERT STATUS": "எச்சரிக்கை நிலை",
        "Warnings": "எச்சரிக்கைகள்",
        "All OK": "அனைத்தும் சரி",
        "Active Replenishment Warnings": "செயலில் உள்ள மறு நிரப்பல் எச்சரிக்கைகள்",
        "Optimal shelf inventories": "அனைத்து தற்போதைய அலமாரி சரக்குகளும் உகந்ததாக உள்ளன!",
        "Owner Dashboard": "உரிமையாளர் டாஷ்போர்டு",
        "Staff Dashboard": "பணியாளர் டாஷ்போர்டு",
        "Video Detection": "வீடியோ கண்டறிதல்",
        "Image Detection": "படம் கண்டறிதல்",
        "Items Count": "பொருட்கள் எண்ணிக்கை",
        "Reports & Analytics": "அறிக்கைகள் & பகுப்பாய்வு",
        "Low stock count": "குறைந்த இருப்பு எண்ணிக்கை",
        "Audit Logs": "தணிக்கை பதிவுகள்",
        "Settings": "அமைப்புகள்",
        "Product Name": "தயாரிப்பு பெயர்",
        "Class ID": "வகுப்பு ஐடி",
        "Current Count": "தற்போதைய எண்ணிக்கை",
        "Price": "விலை",
        "Min count to be in shelf": "அலமாரியில் இருக்க வேண்டிய குறைந்தபட்ச எண்ணிக்கை",
        "Status": "நிலை",
        "Low Stock": "குறைந்த இருப்பு",
        "Optimal Stock": "சரியான இருப்பு",
        "Edit Product Target thresholds": "தயாரிப்பு இலக்கு வரம்புகளைத் திருத்துக",
        "Select YOLO Class to edit": "திருத்த வேண்டிய YOLO வகுப்பைத் தேர்ந்தெடுக்கவும்",
        "New Warning Limit threshold value": "புதிய எச்சரிக்கை வரம்பு மதிப்பு",
        "Update Product Warning threshold": "தயாரிப்பு எச்சரிக்கை வரம்பைப் புதுப்பிக்கவும்",
        "Successfully updated threshold": "வெற்றிகரமாக புதுப்பிக்கப்பட்ட வரம்பு",
        "to": "இதற்கு",
        "No scanning data logged yet": "இன்னும் ஸ்கேன் தரவு எதுவும் பதிவு செய்யப்படவில்லை. பதிவுகளை நிரப்ப ஒரு நிலையான பட ஸ்கேன் இயக்கவும்.",
        "Static Image Scanner": "படம் ஸ்கேன்",
        "Upload shelf photograph": "அலமாரி புகைப்படத்தைப் பதிவேற்றவும்...",
        "Shelf Detection View": "அலமாரி கண்டறிதல் பார்வை",
        "Analyzing image": "படம் பகுப்பாய்வு செய்யப்படுகிறது...",
        "Detection failed": "கண்டறிதல் தோல்வியடைந்தது",
        "AI Prediction Tallies": "AI கணிப்பு எண்ணிக்கை",
        "Override Tallies": "எண்ணிக்கைகளை மேலெழுதவும்",
        "Class": "வகுப்பு",
        "Total Valuation": "மொத்த மதிப்பீடு",
        "Log Scan to SQLite": "ஸ்கானை SQLite இல் பதிவு செய்க",
        "Logged successfully": "வெற்றிகரமாக பதிவு செய்யப்பட்டது!",
        "Real-time Tracking Feed": "வீடியோ ஸ்கேன்",
        "Select Tracker Input Stream": "கண்காணிப்பு உள்ளீட்டு ஸ்ட்ரீமைத் தேர்ந்தெடுக்கவும்",
        "Webcam Live Input": "வெப்கேமரா நேரடி உள்ளீடு",
        "Upload Video File": "வீடியோ கோப்பைப் பதிவேற்றவும்",
        "Capture shelf snapshots": "உங்கள் வெப்கேமரா சாதன கேமரா மூலம் அலமாரி படங்களை எடுக்கவும்:",
        "Take snap": "படம் எடுக்கவும்",
        "Log Webcam Snap to Database": "வெப்கேம் படத்தை தரவுத்தளத்தில் பதிவு செய்க",
        "Webcam scan saved": "வெப்கேம் ஸ்கேன் சேமிக்கப்பட்டது!",
        "Upload video file": "வீடியோ கோப்பைப் பதிவேற்றவும்...",
        "Unique Items Tracked": "கணக்கிடப்பட்ட பொருட்கள்",
        "Valuation": "மொத்த மதிப்பு",
        "Log Video Track to SQL": "வீடியோ கண்காணிப்பை SQL இல் பதிவு செய்க",
        "Video track logged": "வீடியோ கண்காணிப்பு பதிவு செய்யப்பட்டது!",
        "Validated": "சரிபார்க்கப்பட்டது",
        "Catalog Configuration Settings": "பொருட்கள் பட்டியல்",
        "Authorized Owner role required": "SKU மேப்பிங்கை மாற்ற அங்கீகரிக்கப்பட்ட உரிமையாளர் பங்கு தேவை.",
        "Add / Update SKU Mapping": "பொருளைச் சேர் / புதுப்பி",
        "YOLO Class ID": "பொருள்",
        "Product Name Input": "தயாரிப்பு பெயர் (எ.கா. 'Pepsi 500ml')",
        "Retail Unit Price (₹)": "சில்லறை அலகு விலை (₹)",
        "Low Stock Threshold Alert": "குறைந்தபட்ச பொருட்கள்",
        "Save SKU Config": "பொருளைச் சேமி",
        "Successfully configured SKU mapping": "SKU மேப்பிங் வெற்றிகரமாக கட்டமைக்கப்பட்டது!",
        "Delete SKU Mapping": "பொருளை நீக்கு",
        "Select YOLO Class to delete": "நீக்க வேண்டிய YOLO வகுப்பைத் தேர்ந்தெடுக்கவும்",
        "Delete SKU Config": "பொருளை நீக்கு",
        "SKU Mapping deleted": "SKU மேப்பிங் நீக்கப்பட்டது!",
        "Shelf Comparison Audit": "அலமாரி ஒப்பீட்டு தணிக்கை",
        "Baseline Snapshot (Morning)": "அடிப்படை படம் (காலை)",
        "Upload baseline snapshot": "அடிப்படை படத்தைப் பதிவேற்றவும்...",
        "Target Snapshot (Evening)": "இலக்கு படம் (மாலை)",
        "Upload target snapshot": "இலக்கு படத்தைப் பதிவேற்றவும்...",
        "Baseline Shelf": "அடிப்படை அலமாரி",
        "Target Shelf": "இலக்கு அலமாரி",
        "Baseline Count": "அடிப்படை எண்ணிக்கை",
        "Target Count": "இலக்கு எண்ணிக்கை",
        "Quantity Sold": "விற்கப்பட்ட அளவு",
        "Estimated Revenue": "மதிப்பிடப்பட்ட வருவாய்",
        "Total Revenue Generated": "ஈட்டப்பட்ட மொத்த வருவாய்",
        "Analytics & Reporting Dashboard": "பகுப்பாய்வு & அறிக்கை டாஷ்போர்டு",
        "Owner clearance required": "நிதி அறிக்கைகளைப் பார்க்க உரிமையாளர் அனுமதி தேவை.",
        "Valuation Trends Over Time": "காலப்போக்கில் மதிப்பு போக்குகள்",
        "Retail Shelf Value Trends": "சில்லறை அலமாரி மதிப்பு போக்குகள்",
        "Past Scanning Logs": "கடந்த கால ஸ்கேனிங் பதிவுகள்",
        "Export History Log to CSV": "வரலாற்றுப் பதிவை CSV கோப்பாக ஏற்றுமதி செய்க",
        "No scanning history recorded": "SQLite-இல் ஸ்கேனிங் வரலாறு எதுவும் பதிவு செய்யப்படவில்லை.",
        "Inventory items below target": "சரக்கு பொருட்கள் அவற்றின் இலக்கு வரம்பிற்கு கீழே உள்ளன:",
        "All catalog products stocked": "அனைத்து தயாரிப்புகளும் முழுமையாக இருப்பு வைக்கப்பட்டுள்ளன!",
        "Configure Warning Notification Channels": "எச்சரிக்கை அறிவிப்பு சேனல்களை கட்டமைக்கவும்",
        "Enable Automated Email Reports": "தானியங்கி மின்னஞ்சல் அறிக்கைகளை இயக்கு (SMTP)",
        "Manager Email Address": "மேலாளர் மின்னஞ்சல் முகவரி",
        "Enable Instant Telegram Mobile Push Alerts": "உடனடி தந்தி (Telegram) புஷ் எச்சரிக்கைகளை இயக்கு",
        "Telegram Chat ID": "டெலிகிராம் அரட்டை ஐடி / பயனர் பெயர்",
        "Save Notification Settings": "அறிவிப்பு அமைப்புகளைச் சேமிக்கவும்",
        "Successfully saved notification channel": "அறிவிப்பு சேனல் சான்றுகள் வெற்றிகரமாக சேமிக்கப்பட்டன!",
        "System Audit Logs": "அமைப்பு தணிக்கை பதிவுகள்",
        "Owner validation required": "செயல்பாட்டு தணிக்கை பதிவுகளைப் பார்க்க உரிமையாளர் சரிபார்ப்பு தேவை.",
        "No audit logs": "தரவுத்தளத்தில் தணிக்கை பதிவுகள் எதுவும் இல்லை.",
        "System Configurations": "அமைப்பு கட்டமைப்புகள்",
        "Display Theme Preferences": "காட்சி தீம் விருப்பங்கள்",
        "Select Dashboard Color Scheme Theme": "டாஷ்போர்டு வண்ண தீமினைத் தேர்ந்தெடுக்கவும்",
        "Light Mode": "ஒளி பயன்முறை (Light Mode)",
        "Dark Mode": "இருண்ட பயன்முறை (Dark Mode)",
        "Backup & Restore Catalog Mappings": "பட்டியல் மேப்பிங் காப்புப்பிரதி & மீட்டமைப்பு",
        "Export Configurations": "கட்டமைப்புகளை ஏற்றுமதி செய்க",
        "Download Backup": "காப்புப்பிரதியைப் பதிவிறக்குக (.json)",
        "Restore Configurations": "கட்டமைப்புகளை மீட்டமைக்கவும்",
        "Upload JSON": "JSON ஐப் பதிவேற்றவும்",
        "SKU Catalog configurations restored": "SKU பட்டியல் கட்டமைப்புகள் மீட்டெடுக்கப்பட்டன!",
        "Restore failed": "மீட்டமைப்பு தோல்வியடைந்தது",
        "Bulk Import Catalog": "பட்டியலை மொத்தமாக இறக்குமதி செய்க",
        "Upload CSV": "CSV ஐப் பதிவேற்றவும்",
        "Successfully imported items from CSV": "CSV கோப்பிலிருந்து பொருட்கள் வெற்றிகரமாக இறக்குமதி செய்யப்பட்டன!",
        "CSV import failed": "CSV இறக்குமதி தோல்வியடைந்தது",
        "Admin Reset Operations": "நிர்வாகி மீட்டமைப்பு செயல்பாடுகள்",
        "Reset SQLite Database Records": "SQLite தரவுத்தள பதிவுகளை மீட்டமைக்கவும்",
        "SQLite logs database reset successfully": "SQLite பதிவுகள் தரவுத்தளம் வெற்றிகரமாக மீட்டமைக்கப்பட்டது!",
        "Scan ID": "ஸ்கான் ஐடி",
        "Timestamp": "நேர முத்திரை",
        "Total Items": "மொத்த பொருட்கள்",
        "Total Value (₹)": "மொத்த மதிப்பு (₹)",
        "Before/After Comparison": "முன்பு/பின்பு ஒப்பீடு",
        "Sensitivity": "மாதிரி உணர்திறன் (குறைந்த மதிப்பு பொருட்களை எளிதாகக் கண்டறியும்)",
        "Low stock alert toast": "குறைந்த இருப்பு கண்டறியப்பட்டது! அலமாரியை நிரப்பவும்.",
        "Scan Summary Breakdown": "சுருக்கம்",
        "items": "பொருட்கள்",
        "Scan History Logs": "ஸ்கேன் வரலாறு பதிவுகள்",
        "Current SKU Catalog": "தற்போதைய பொருட்கள்",
        "Deleted SKUs History": "நீக்கப்பட்ட SKU வரலாறு",
        "Export Reports Title": "சமீபத்திய ஸ்கேன் அறிக்கையை ஏற்றுமதி செய்க",
        "Export PDF": "PDF ஆக ஏற்றுமதி செய்க",
        "Export CSV": "CSV ஆக ஏற்றுமதி செய்க",
        "Item List": "பொருட்கள் பட்டியல்",
        "Items Counted": "கணக்கிடப்பட்ட பொருட்கள்",
        "Total Value": "மொத்த மதிப்பு",
        "Item": "பொருள்",
        "Min Item": "குறைந்தபட்ச பொருட்கள்"
    }
}

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
                background-color: #000000 !important;
            }
            .main {
                background-color: #000000 !important;
                color: #ffffff !important;
            }
            [data-testid="stAppViewBlockContainer"] h1, 
            [data-testid="stAppViewBlockContainer"] h2, 
            [data-testid="stAppViewBlockContainer"] h3, 
            [data-testid="stAppViewBlockContainer"] h4, 
            [data-testid="stAppViewBlockContainer"] h5, 
            [data-testid="stAppViewBlockContainer"] h6, 
            [data-testid="stAppViewBlockContainer"] p, 
            [data-testid="stAppViewBlockContainer"] label, 
            [data-testid="stAppViewBlockContainer"] span, 
            [data-testid="stAppViewBlockContainer"] li, 
            [data-testid="stAppViewBlockContainer"] strong, 
            [data-testid="stAppViewBlockContainer"] small,
            [data-testid="stMetricValue"] > div,
            [data-testid="stMetricLabel"] > div {
                color: #ffffff !important;
            }
            .metric-card {
                background-color: #111111 !important;
                border: 1px solid #333333 !important;
            }
            section[data-testid="stSidebar"] {
                background-color: #111111 !important;
            }
            section[data-testid="stSidebar"] *,
            [data-testid="stSidebar"] *,
            div[data-testid="stRadio"] *,
            div[role="radiogroup"] *,
            [data-baseweb="radio"] * {
                color: #ffffff !important;
                -webkit-text-fill-color: #ffffff !important;
            }
            .main input, .main select, .main textarea, .main [data-baseweb="input"], .main [data-baseweb="select"] > div, .main button[role="combobox"] span {
                background-color: #222222 !important;
                color: #ffffff !important;
                -webkit-text-fill-color: #ffffff !important;
                border: 1px solid #444444 !important;
            }
            [data-testid="stFileUploaderDropzone"] {
                background-color: #1e293b !important;
                border: 2px dashed #475569 !important;
            }
            [data-testid="stFileUploaderDropzone"] * {
                color: #ffffff !important;
            }
        """
    else:
        bg_style = """
            .stApp {
                background-color: #ffffff !important;
            }
            .main {
                background-color: #ffffff !important;
                color: #000000 !important;
            }
            .block-container *,
            [data-testid="stAppViewBlockContainer"] *,
            .stMarkdown *,
            div[data-testid="stMetricValue"] *,
            div[data-testid="stMetricLabel"] * {
                color: #000000 !important;
            }
            .metric-card {
                background-color: #ffffff !important;
                border: 1px solid #cbd5e1 !important;
            }
            section[data-testid="stSidebar"] *,
            [data-testid="stSidebar"] *,
            div[data-testid="stRadio"] *,
            div[role="radiogroup"] *,
            [data-baseweb="radio"] * {
                color: #ffffff !important;
                -webkit-text-fill-color: #ffffff !important;
            }
            .main input, .main select, .main textarea, .main [data-baseweb="input"], .main [data-baseweb="select"] > div, .main button[role="combobox"] span {
                background-color: #f1f5f9 !important;
                color: #000000 !important;
                -webkit-text-fill-color: #000000 !important;
                border: 1px solid #cbd5e1 !important;
            }
            [data-testid="stFileUploaderDropzone"] {
                background-color: #f8fafc !important;
                border: 2px dashed #cbd5e1 !important;
            }
            [data-testid="stFileUploaderDropzone"] * {
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
        .stButton>button,
        [data-testid="stFormSubmitButton"] button {{
            background-color: #7c3aed !important;
            background: #7c3aed !important;
            color: #ffffff !important;
            border-radius: 8px !important;
            border: none !important;
            padding: 8px 16px !important;
            box-shadow: none !important;
            transition: none !important;
            transform: none !important;
        }}
        .stButton>button *,
        [data-testid="stFormSubmitButton"] button * {{
            color: #ffffff !important;
            -webkit-text-fill-color: #ffffff !important;
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
            background-color: #ffffff !important;
            border: 1px solid #cbd5e1 !important;
            border-radius: 12px !important;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05) !important;
            padding: 1.5rem !important;
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

# Language switcher at the top right of the page
col_main_top, col_lang_top = st.columns([8, 2])
with col_lang_top:
    lang_select = st.selectbox(
        "Language / மொழி",
        options=["English", "Tamil"],
        index=0 if st.session_state.app_lang == "English" else 1
    )
    if lang_select != st.session_state.app_lang:
        st.session_state.app_lang = lang_select
        st.rerun()


if not st.session_state.logged_in:
    st.markdown(f"""
        <div class='header-container' style='text-align: center;'>
            <h1 style='font-size: 3rem; margin: 0;'>{TRANSLATIONS[st.session_state.app_lang]["title"]}</h1>
        </div>
    """, unsafe_allow_html=True)
    
    col_left, col_center, col_right = st.columns([1.3, 1.0, 1.3])
    with col_center:
        tab_signin, tab_signup = st.tabs([TRANSLATIONS[st.session_state.app_lang]["Sign In"], TRANSLATIONS[st.session_state.app_lang]["Sign Up"]])
        
        with tab_signin:
            with st.form("signin_form"):
                username = st.text_input(TRANSLATIONS[st.session_state.app_lang]["Username"], key="signin_username")
                password = st.text_input(TRANSLATIONS[st.session_state.app_lang]["Password"], type="password", key="signin_password")
                submit_signin = st.form_submit_button(TRANSLATIONS[st.session_state.app_lang]["Sign In"])
                
                if submit_signin:
                    username = username.strip()
                    password = password.strip()
                    role = db_manager.authenticate_user(username, password)
                    if role:
                        st.session_state.logged_in = True
                        st.session_state.user_role = role
                        st.session_state.current_page = "Dashboard"
                        db_manager.log_audit(role, f"User {username} logged in successfully")
                        translated_role = TRANSLATIONS[st.session_state.app_lang][role]
                        welcome_msg = TRANSLATIONS[st.session_state.app_lang]["Welcome"]
                        loading_msg = TRANSLATIONS[st.session_state.app_lang]["Loading panel..."]
                        st.success(f"{welcome_msg} {translated_role}! {loading_msg}")
                        st.rerun()
                    else:
                        st.error(TRANSLATIONS[st.session_state.app_lang]["Account not found"])

        with tab_signup:
            with st.form("signup_form"):
                reg_username = st.text_input(TRANSLATIONS[st.session_state.app_lang]["Choose Username"], key="signup_username")
                reg_password = st.text_input(TRANSLATIONS[st.session_state.app_lang]["Choose Password"], type="password", key="signup_password")
                reg_role = st.selectbox(TRANSLATIONS[st.session_state.app_lang]["Select Your Role"], [TRANSLATIONS[st.session_state.app_lang]["Owner"], TRANSLATIONS[st.session_state.app_lang]["Staff"]], key="signup_role")
                submit_signup = st.form_submit_button(TRANSLATIONS[st.session_state.app_lang]["Create Account"])
                
                if submit_signup:
                    reg_username = reg_username.strip()
                    reg_password = reg_password.strip()
                    # Database needs raw English role string ("Owner" or "Staff")
                    raw_reg_role = "Owner" if reg_role == TRANSLATIONS[st.session_state.app_lang]["Owner"] else "Staff"

                    if not reg_username or not reg_password:
                        st.warning(TRANSLATIONS[st.session_state.app_lang]["Specify username password"])
                    elif raw_reg_role == "Owner" and (reg_username != "admin" or reg_password != "admin123"):
                        st.error(TRANSLATIONS[st.session_state.app_lang]["Invalid owner credentials"])
                    elif raw_reg_role == "Staff" and (reg_username != "staff" or reg_password != "staff123"):
                        st.error(TRANSLATIONS[st.session_state.app_lang]["Invalid staff credentials"])
                    else:
                        success = db_manager.add_user(reg_username, reg_password, raw_reg_role)
                        if success:
                            db_manager.log_audit(raw_reg_role, f"New user account registered: {reg_username}")
                            st.success(TRANSLATIONS[st.session_state.app_lang]["Account created successfully"])
                        else:
                            st.success(TRANSLATIONS[st.session_state.app_lang]["Account already created"])


# ----------------- Logged-in Panel -----------------
else:
    # Sidebar Page Navigation config based on roles
    translated_logged_role = TRANSLATIONS[st.session_state.app_lang][st.session_state.user_role]
    st.sidebar.write(f"{TRANSLATIONS[st.session_state.app_lang]['Logged in']}: **{translated_logged_role}**")
    
    if st.session_state.user_role == "Owner":
        menu_options = [
            "Owner Dashboard", 
            "Video Detection", 
            "Image Detection", 
            "Items Count"
        ]
    else:
        menu_options = [
            "Staff Dashboard", 
            "Video Detection", 
            "Image Detection"
        ]

    # Map the English options to the app_mode values used in the conditional checks
    menu_map = {
        "Owner Dashboard": "Owner Dashboard",
        "Staff Dashboard": "Staff Dashboard",
        "Video Detection": "Video Detection",
        "Image Detection": "Image Detection",
        "Items Count": "Items Count"
    }

    app_mode_raw = st.sidebar.radio(
        TRANSLATIONS[st.session_state.app_lang]["Navigate View"], 
        menu_options,
        format_func=lambda x: TRANSLATIONS[st.session_state.app_lang].get(x, x)
    )
    app_mode = menu_map.get(app_mode_raw, app_mode_raw)
    
    if st.sidebar.button(TRANSLATIONS[st.session_state.app_lang]["Logout"]):
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
        alerts = check_low_stock()
        if alerts:
            st.toast(TRANSLATIONS[st.session_state.app_lang]["Low stock alert toast"])
        st.subheader(TRANSLATIONS[st.session_state.app_lang][st.session_state.user_role + " Dashboard"])
        
        # Pull latest summaries from SQLite
        scans = db_manager.get_all_scans()
        total_scans = len(scans)
        latest_val = scans[0][3] if scans else 0.0
        
        # Display key summary cards
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown(f"""
                <div class="metric-card">
                    <span style="color: #94a3b8; font-size: 0.85rem;">{TRANSLATIONS[st.session_state.app_lang]["TOTAL LOGGED SCANS"]}</span>
                    <h2>{total_scans}</h2>
                </div>
            """, unsafe_allow_html=True)
        with col2:
            st.markdown(f"""
                <div class="metric-card">
                    <span style="color: #94a3b8; font-size: 0.85rem;">{TRANSLATIONS[st.session_state.app_lang]["LATEST SHELF VALUE"]}</span>
                    <h2 style="color: #10b981;">₹{latest_val:.2f}</h2>
                </div>
            """, unsafe_allow_html=True)
        with col3:
            alert_color = "#ef4444" if alerts else "#10b981"
            alert_text = f"{len(alerts)} {TRANSLATIONS[st.session_state.app_lang]['Warnings']}" if alerts else TRANSLATIONS[st.session_state.app_lang]["All OK"]
            st.markdown(f"""
                <div class="metric-card">
                    <span style="color: #94a3b8; font-size: 0.85rem;">{TRANSLATIONS[st.session_state.app_lang]["ALERT STATUS"]}</span>
                    <h2 style="color: {alert_color};">{alert_text}</h2>
                </div>
            """, unsafe_allow_html=True)

        if scans:
            latest_id = scans[0][0]
            details = db_manager.get_scan_details(latest_id)
            if details:
                records = []
                for item in details:
                    _, class_id, count, price = item
                    sku_name = sku_mapping.get(class_id, {}).get("sku_name", class_id)
                    threshold = sku_mapping.get(class_id, {}).get("low_stock_threshold", 0)
                    status = TRANSLATIONS[st.session_state.app_lang]["Low Stock"] if count < threshold else TRANSLATIONS[st.session_state.app_lang]["Optimal Stock"]
                    records.append({
                        TRANSLATIONS[st.session_state.app_lang]["Product Name"]: sku_name,
                        TRANSLATIONS[st.session_state.app_lang]["Current Count"]: count,
                        TRANSLATIONS[st.session_state.app_lang]["Price"]: f"₹{price:.2f}",
                        TRANSLATIONS[st.session_state.app_lang]["Min count to be in shelf"]: threshold,
                        TRANSLATIONS[st.session_state.app_lang]["Status"]: status
                    })
                st.dataframe(pd.DataFrame(records), hide_index=True, use_container_width=True)
            
            st.write("---")
            st.write(f"### {TRANSLATIONS[st.session_state.app_lang]['Scan History Logs']}")
            records = []
            for scan in scans:
                scan_id, timestamp, total_items, total_value = scan
                details = db_manager.get_scan_details(scan_id)
                product_list = []
                if details:
                    for item in details:
                        _, class_id, count, _ = item
                        mapped_name = sku_mapping.get(class_id, {}).get("sku_name", class_id)
                        product_list.append(f"{mapped_name} ({count})")
                product_str = ", ".join(product_list)
                records.append({
                    TRANSLATIONS[st.session_state.app_lang]["Scan ID"]: scan_id,
                    TRANSLATIONS[st.session_state.app_lang]["Timestamp"]: timestamp,
                    TRANSLATIONS[st.session_state.app_lang]["Product Name"]: product_str,
                    TRANSLATIONS[st.session_state.app_lang]["Total Items"]: total_items,
                    TRANSLATIONS[st.session_state.app_lang]["Total Value (₹)"]: total_value
                })
            df_scans = pd.DataFrame(records)
            st.dataframe(df_scans, hide_index=True, use_container_width=True)

    # ----------------- Image Detection -----------------
    elif app_mode == "Image Detection":
        st.subheader(TRANSLATIONS[st.session_state.app_lang]["Static Image Scanner"])
        conf_val = 0.50
        uploaded_file = st.file_uploader(TRANSLATIONS[st.session_state.app_lang]["Upload shelf photograph"], type=["jpg", "jpeg", "png"])
        
        if uploaded_file is not None and detector is not None:
            col1, col2 = st.columns([2, 1])
            with col1:
                st.write("### " + TRANSLATIONS[st.session_state.app_lang]["Shelf Detection View"])
                with st.spinner(TRANSLATIONS[st.session_state.app_lang]["Analyzing image"]):
                    try:
                        annotated_image, counts = detector.detect_image(uploaded_file, conf=conf_val)
                        st.image(annotated_image, use_container_width=True)
                        if counts:
                            has_low_stock = False
                            for cls_id, count in counts.items():
                                threshold = sku_mapping.get(cls_id, {}).get("low_stock_threshold", 0)
                                if count < threshold:
                                    has_low_stock = True
                                    break
                            if has_low_stock:
                                st.toast(TRANSLATIONS[st.session_state.app_lang]["Low stock alert toast"])
                    except Exception as ex:
                        st.error(f"{TRANSLATIONS[st.session_state.app_lang]['Detection failed']}: {ex}")
                        counts = {}
            with col2:
                st.write("### " + TRANSLATIONS[st.session_state.app_lang]["AI Prediction Tallies"])
                if counts:
                    if "adjusted_counts" not in st.session_state:
                        st.session_state.adjusted_counts = counts.copy()
                    
                    st.write("#### ✏️ " + TRANSLATIONS[st.session_state.app_lang]["Override Tallies"])
                    for cls_id in list(st.session_state.adjusted_counts.keys()):
                        st.session_state.adjusted_counts[cls_id] = st.number_input(
                            f"{TRANSLATIONS[st.session_state.app_lang]['Class']}: {cls_id}",
                            min_value=0,
                            value=int(st.session_state.adjusted_counts[cls_id])
                        )
                        
                    # Calculate sums
                    tally_data = []
                    total_value = 0.0
                    total_items = 0
                    low_stock_triggered = []
                    for cls_id, count in st.session_state.adjusted_counts.items():
                        mapping = sku_mapping.get(cls_id, {"sku_name": cls_id, "price": 0.0, "low_stock_threshold": 0})
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
                        
                    st.write(f"**{TRANSLATIONS[st.session_state.app_lang]['Unique Items Tracked']}:** {total_items} | **{TRANSLATIONS[st.session_state.app_lang]['Valuation']}:** ₹{total_value:.2f}")
                    
                    # Auto-log scan to SQLite
                    current_key = f"{uploaded_file.name}_{total_items}_{total_value}"
                    if st.session_state.get("last_auto_logged_key") != current_key:
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
                        st.session_state.last_auto_logged_key = current_key
                        st.success(TRANSLATIONS[st.session_state.app_lang]["Logged successfully"])


    # ----------------- Video Detection -----------------
    elif app_mode == "Video Detection":
        st.subheader(TRANSLATIONS[st.session_state.app_lang]["Real-time Tracking Feed"])
        conf_val = 0.50
        uploaded_video = st.file_uploader(TRANSLATIONS[st.session_state.app_lang]["Upload video file"], type=["mp4", "avi", "mov"])
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
                annotated_frame, active_tracks = detector.track_frame(frame, conf=conf_val)
                for track_id, class_name in active_tracks.items():
                    tracked_objects[track_id] = class_name
                st_frame.image(annotated_frame, use_container_width=True)
            video_cap.release()
            os.remove(temp_file_path)
            
            # Format tracked items
            class_counts = {}
            for cls_name in tracked_objects.values():
                class_counts[cls_name] = class_counts.get(cls_name, 0) + 1
            
            video_items = []
            for cls, count in class_counts.items():
                sku_info = sku_mapping.get(cls, {"sku_name": cls, "price": 0.0})
                video_items.append({
                    "sku_name": sku_info.get("sku_name", cls),
                    "detected_class": cls,
                    "count": count,
                    "unit_price": sku_info.get("price", 0.0)
                })
            
            total_items = sum(item["count"] for item in video_items)
            total_val = sum(item["count"] * item["unit_price"] for item in video_items)
            
            st.write(f"**{TRANSLATIONS[st.session_state.app_lang]['Unique Items Tracked']}:** {total_items} | **{TRANSLATIONS[st.session_state.app_lang]['Valuation']}:** ₹{total_val:.2f}")
            st.write(f"### {TRANSLATIONS[st.session_state.app_lang]['Scan Summary Breakdown']}")
            for item in video_items:
                st.write(f"- **{item['sku_name']}**: {item['count']} {TRANSLATIONS[st.session_state.app_lang]['items']}")
            
            # Automatic database logging
            video_key = f"{uploaded_video.name}_{total_items}_{total_val}"
            if st.session_state.get("last_auto_logged_video") != video_key:
                db_items = [{
                    'sku_name': item['sku_name'],
                    'detected_class': item['detected_class'],
                    'count': item['count'],
                    'unit_price': item['unit_price']
                } for item in video_items]
                db_manager.log_scan(total_items, total_val, db_items)
                db_manager.log_audit(st.session_state.user_role, f"Logged tracking video log containing {total_items} items")
                st.session_state.last_auto_logged_video = video_key


    # ----------------- SKU Management -----------------
    elif app_mode == "Items Count":
        st.subheader(TRANSLATIONS[st.session_state.app_lang]["Catalog Configuration Settings"])
        if st.session_state.user_role != "Owner":
            st.error(TRANSLATIONS[st.session_state.app_lang]["Authorized Owner role required"])
        else:
            # Current SKU Catalog table
            st.write("### " + TRANSLATIONS[st.session_state.app_lang]["Current SKU Catalog"])
            catalog_data = []
            for class_id, details in sku_mapping.items():
                catalog_data.append({
                    TRANSLATIONS[st.session_state.app_lang]["YOLO Class ID"]: class_id,
                    TRANSLATIONS[st.session_state.app_lang]["Product Name"]: details.get("sku_name", ""),
                    TRANSLATIONS[st.session_state.app_lang]["Retail Unit Price (₹)"]: details.get("price", 0.0),
                    TRANSLATIONS[st.session_state.app_lang]["Low Stock Threshold Alert"]: details.get("low_stock_threshold", 0)
                })
            catalog_df = pd.DataFrame(catalog_data)
            st.dataframe(catalog_df, use_container_width=True)

            # Export Latest Scan Report section
            st.write("### " + TRANSLATIONS[st.session_state.app_lang]["Export Reports Title"])
            scans = db_manager.get_all_scans()
            if scans:
                latest_id = scans[0][0]
                latest_total_items = scans[0][2]
                latest_total_value = scans[0][3]
                details = db_manager.get_scan_details(latest_id)
                
                tally_data = []
                for item in details:
                    sku_name, class_id, count, price = item
                    threshold = sku_mapping.get(class_id, {}).get("low_stock_threshold", 0)
                    status = TRANSLATIONS[st.session_state.app_lang]["Low Stock"] if count < threshold else TRANSLATIONS[st.session_state.app_lang]["Optimal Stock"]
                    tally_data.append({
                        "sku_name": sku_name,
                        "class_id": class_id,
                        "count": count,
                        "price": price,
                        "min_item": threshold,
                        "status": status
                    })
                
                pdf_buffer = generate_pdf_report(
                    tally_data=tally_data,
                    total_items=latest_total_items,
                    total_value=latest_total_value,
                    translations=TRANSLATIONS,
                    lang=st.session_state.app_lang
                )
                csv_data = generate_csv_report(
                    tally_data=tally_data,
                    translations=TRANSLATIONS,
                    lang=st.session_state.app_lang
                )
                
                col_btn1, col_btn2 = st.columns(2)
                with col_btn1:
                    st.download_button(
                        label=TRANSLATIONS[st.session_state.app_lang]["Export PDF"],
                        data=pdf_buffer,
                        file_name="latest_scan_report.pdf",
                        mime="application/pdf"
                    )
                with col_btn2:
                    st.download_button(
                        label=TRANSLATIONS[st.session_state.app_lang]["Export CSV"],
                        data=csv_data,
                        file_name="latest_scan_report.csv",
                        mime="text/csv"
                    )
            else:
                st.info(TRANSLATIONS[st.session_state.app_lang]["No scanning history recorded"])

            with st.form("add_sku_form"):
                st.write("### " + TRANSLATIONS[st.session_state.app_lang]["Add / Update SKU Mapping"])
                class_name = st.text_input(TRANSLATIONS[st.session_state.app_lang]["YOLO Class ID"]).lower().strip()
                sku_name = st.text_input(TRANSLATIONS[st.session_state.app_lang]["Product Name Input"])
                price = st.number_input(TRANSLATIONS[st.session_state.app_lang]["Retail Unit Price (₹)"], min_value=0.0, step=0.01)
                threshold = st.number_input(TRANSLATIONS[st.session_state.app_lang]["Low Stock Threshold Alert"], min_value=0, step=1)
                submit_btn = st.form_submit_button(TRANSLATIONS[st.session_state.app_lang]["Save SKU Config"])
                
                if submit_btn and class_name and sku_name:
                    sku_mapping[class_name] = {
                        "sku_name": sku_name,
                        "price": price,
                        "low_stock_threshold": int(threshold)
                    }
                    save_sku_mapping(sku_mapping)
                    db_manager.log_audit("Owner", f"Added/Updated SKU Mapping for class: {class_name}")
                    st.success(TRANSLATIONS[st.session_state.app_lang]["Successfully configured SKU mapping"])
                    st.rerun()

            with st.form("delete_sku_form"):
                st.write("### " + TRANSLATIONS[st.session_state.app_lang]["Delete SKU Mapping"])
                class_to_delete = st.selectbox(TRANSLATIONS[st.session_state.app_lang]["Select YOLO Class to delete"], options=[""] + list(sku_mapping.keys()))
                delete_btn = st.form_submit_button(TRANSLATIONS[st.session_state.app_lang]["Delete SKU Config"])
                if delete_btn and class_to_delete:
                    del sku_mapping[class_to_delete]
                    save_sku_mapping(sku_mapping)
                    db_manager.log_audit("Owner", f"Deleted SKU Mapping for class: {class_to_delete}")
                    st.success(TRANSLATIONS[st.session_state.app_lang]["SKU Mapping deleted"])
                    st.rerun()

            # Deleted SKUs History section
            st.write("### " + TRANSLATIONS[st.session_state.app_lang]["Deleted SKUs History"])
            audit_logs = db_manager.get_audit_logs()
            deleted_logs = []
            for log in audit_logs:
                # log structure: (id, timestamp, user_role, action)
                if "Deleted SKU Mapping" in log[3]:
                    deleted_logs.append({
                        "Timestamp": log[1],
                        "User Role": log[2],
                        "Action Details": log[3]
                    })
            deleted_df = pd.DataFrame(deleted_logs)
            st.dataframe(deleted_df, use_container_width=True)

    # ----------------- Before/After Comparison -----------------
    elif app_mode == "Before/After Comparison":
        st.subheader(TRANSLATIONS[st.session_state.app_lang]["Shelf Comparison Audit"])
        col_img1, col_img2 = st.columns(2)
        with col_img1:
            st.write("#### " + TRANSLATIONS[st.session_state.app_lang]["Baseline Snapshot (Morning)"])
            img1 = st.file_uploader(TRANSLATIONS[st.session_state.app_lang]["Upload baseline snapshot"], type=["jpg","png","jpeg"], key="c_img1")
        with col_img2:
            st.write("#### " + TRANSLATIONS[st.session_state.app_lang]["Target Snapshot (Evening)"])
            img2 = st.file_uploader(TRANSLATIONS[st.session_state.app_lang]["Upload target snapshot"], type=["jpg","png","jpeg"], key="c_img2")
            
        if img1 and img2:
            col_res1, col_res2 = st.columns(2)
            with col_res1:
                annotated1, counts1 = detector.detect_image(img1)
                st.image(annotated1, caption=TRANSLATIONS[st.session_state.app_lang]["Baseline Shelf"], use_container_width=True)
            with col_res2:
                annotated2, counts2 = detector.detect_image(img2)
                st.image(annotated2, caption=TRANSLATIONS[st.session_state.app_lang]["Target Shelf"], use_container_width=True)
                
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
                    TRANSLATIONS[st.session_state.app_lang]["Product Name"]: mapping["sku_name"],
                    TRANSLATIONS[st.session_state.app_lang]["Baseline Count"]: cnt1,
                    TRANSLATIONS[st.session_state.app_lang]["Target Count"]: cnt2,
                    TRANSLATIONS[st.session_state.app_lang]["Quantity Sold"]: sold,
                    TRANSLATIONS[st.session_state.app_lang]["Estimated Revenue"]: f"₹{rev:.2f}"
                })
            st.dataframe(pd.DataFrame(diff_data), hide_index=True, use_container_width=True)
            st.write(f"**{TRANSLATIONS[st.session_state.app_lang]['Total Revenue Generated']}:** ₹{total_rev:.2f}")

    # ----------------- Reports & Analytics -----------------
    elif app_mode == "Reports & Analytics":
        st.subheader(TRANSLATIONS[st.session_state.app_lang]["Analytics & Reporting Dashboard"])
        if st.session_state.user_role != "Owner":
            st.error(TRANSLATIONS[st.session_state.app_lang]["Owner clearance required"])
        else:
            scans = db_manager.get_all_scans()
            if scans:
                df_scans = pd.DataFrame(scans, columns=[
                    TRANSLATIONS[st.session_state.app_lang]["Scan ID"], 
                    TRANSLATIONS[st.session_state.app_lang]["Timestamp"], 
                    TRANSLATIONS[st.session_state.app_lang]["Total Items"], 
                    TRANSLATIONS[st.session_state.app_lang]["Total Value (₹)"]
                ])
                st.write("### " + TRANSLATIONS[st.session_state.app_lang]["Valuation Trends Over Time"])
                fig_trend = px.line(
                    df_scans, 
                    x=TRANSLATIONS[st.session_state.app_lang]["Timestamp"], 
                    y=TRANSLATIONS[st.session_state.app_lang]["Total Value (₹)"], 
                    title=TRANSLATIONS[st.session_state.app_lang]["Retail Shelf Value Trends"], 
                    markers=True
                )
                st.plotly_chart(fig_trend, use_container_width=True)
                
                st.write("### " + TRANSLATIONS[st.session_state.app_lang]["Past Scanning Logs"])
                st.dataframe(df_scans, hide_index=True, use_container_width=True)
                
                # Exporters
                csv_history = df_scans.to_csv(index=False)
                st.download_button(
                    label="📥 " + TRANSLATIONS[st.session_state.app_lang]["Export History Log to CSV"],
                    data=csv_history,
                    file_name="retail_history_logs.csv",
                    mime="text/csv"
                )
            else:
                st.info(TRANSLATIONS[st.session_state.app_lang]["No scanning history recorded"])



    # ----------------- Audit Logs -----------------
    elif app_mode == "Audit Logs":
        st.subheader(TRANSLATIONS[st.session_state.app_lang]["System Audit Logs"])
        if st.session_state.user_role != "Owner":
            st.error(TRANSLATIONS[st.session_state.app_lang]["Owner validation required"])
        else:
            logs = db_manager.get_audit_logs()
            if logs:
                df_logs = pd.DataFrame(logs, columns=["Log ID", "Timestamp", "User Role", "Action Description"])
                st.dataframe(df_logs, hide_index=True, use_container_width=True)
            else:
                st.info(TRANSLATIONS[st.session_state.app_lang]["No audit logs"])

    elif app_mode == "Settings":
        st.subheader(TRANSLATIONS[st.session_state.app_lang]["System Configurations"])
        
        # Theme Settings Toggle (Available to both Owner and Staff)
        st.write("---")
        st.write("### 🌓 " + TRANSLATIONS[st.session_state.app_lang]["Display Theme Preferences"])
        theme_choice = st.selectbox(
            TRANSLATIONS[st.session_state.app_lang]["Select Dashboard Color Scheme Theme"], 
            [TRANSLATIONS[st.session_state.app_lang]["Light Mode"], TRANSLATIONS[st.session_state.app_lang]["Dark Mode"]], 
            index=0 if st.session_state.app_theme == "Light Mode" else 1
        )
        # Convert translated choice back to English key
        raw_theme_choice = "Light Mode" if theme_choice == TRANSLATIONS[st.session_state.app_lang]["Light Mode"] else "Dark Mode"
        if raw_theme_choice != st.session_state.app_theme:
            st.session_state.app_theme = raw_theme_choice
            st.rerun()

        # Backup section
        st.write("---")
        st.write("### 💾 " + TRANSLATIONS[st.session_state.app_lang]["Backup & Restore Catalog Mappings"])
        col_b1, col_b2, col_b3 = st.columns(3)
        with col_b1:
            st.write(TRANSLATIONS[st.session_state.app_lang]["Export Configurations"])
            json_backup_str = json.dumps(sku_mapping, indent=2)
            st.download_button(TRANSLATIONS[st.session_state.app_lang]["Download Backup"], data=json_backup_str, file_name="sku_mapping_backup.json", mime="application/json")
        with col_b2:
            st.write(TRANSLATIONS[st.session_state.app_lang]["Restore Configurations"])
            uploaded_backup = st.file_uploader(TRANSLATIONS[st.session_state.app_lang]["Upload JSON"], type=["json"])
            if uploaded_backup is not None:
                try:
                    restored_map = json.load(uploaded_backup)
                    save_sku_mapping(restored_map)
                    st.success(TRANSLATIONS[st.session_state.app_lang]["SKU Catalog configurations restored"])
                except Exception as e:
                    st.error(f"{TRANSLATIONS[st.session_state.app_lang]['Restore failed']}: {e}")
        with col_b3:
            st.write(TRANSLATIONS[st.session_state.app_lang]["Bulk Import Catalog"])
            uploaded_csv = st.file_uploader(TRANSLATIONS[st.session_state.app_lang]["Upload CSV"], type=["csv"])
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
                    st.success(TRANSLATIONS[st.session_state.app_lang]["Successfully imported items from CSV"])
                except Exception as e:
                    st.error(f"{TRANSLATIONS[st.session_state.app_lang]['CSV import failed']}: {e}")

        # Danger zone
        if st.session_state.user_role == "Owner":
            st.write("---")
            st.write("### ⚠️ " + TRANSLATIONS[st.session_state.app_lang]["Admin Reset Operations"])
            if st.button(TRANSLATIONS[st.session_state.app_lang]["Reset SQLite Database Records"]):
                db_manager.clear_all_scans()
                db_manager.log_audit("Owner", "Reset and wiped SQLite database records")
                st.success(TRANSLATIONS[st.session_state.app_lang]["SQLite logs database reset successfully"])
                st.rerun()
