# 📦 Smart Inventory Counter

An automated, computer vision-powered retail inventory counting system. This project uses **YOLOv8** for real-time object detection and tracking, presenting results via an interactive **Streamlit** dashboard.

---

## 🚀 Core Features

- **Object Detection & Counting:** Automatically detects and tallies retail product categories (bottles, cups, cans, boxes) from uploaded images, videos, and live webcam captures.
- **ByteTrack Tracking Backend:** De-duplicates item counts across frames in video streams by allocating persistent tracking IDs.
- **SKU Mapping Catalog:** Translates raw categories into actual product inventory SKU metadata (names, unit prices, warning thresholds) via a settings panel.
- **Persistent Scan Logging:** Automatically logs scanning session history, itemization logs, and computed retail valuations to a local **SQLite** database.
- **Low-Stock Alert Manager:** Features warning signals and a dedicated Alerts Panel mapping stock deficits and reorder requests, with email and Telegram notification simulators.
- **Before/After Comparisons:** Performs side-by-side snapshot comparison scans (e.g., Morning vs. Evening) to estimate items sold and computed revenue.
- **Exporting Tools:** Exports scan summaries as stylized PDF reports or CSV logs.

---

## 🛠️ Technology Stack

- **Computer Vision:** Ultralytics YOLOv8, ByteTrack, OpenCV
- **Interface & Visualizations:** Streamlit, Plotly, HTML/CSS
- **Storage:** SQLite, JSON configuration
- **Document Exporter:** ReportLab, Pandas

---

## 📅 Daily Implementation Log (June 6 – June 28)

### **Phase 1: Foundation & Detections**
- **Day 1 (June 6):** Workspace setup, requirements initialization, and static image scanner implementation with YOLOv8.
- **Day 2 (June 8):** Dynamic JSON SKU configuration mapping layer and SQLite persistent database schema setup.
- **Day 3 (June 10):** Native YOLOv8 ByteTrack integration and OpenCV video processing frame reader loop.
- **Day 4 (June 11):** Low-stock visual warning triggers and Morning vs. Evening shelf comparison scan calculations.
- **Day 5 (June 12):** ReportLab PDF document layout structures and pandas CSV reporting download triggers.

### **Phase 2: Live Inputs & Catalog Extensions**
- **Day 6 (June 13):** Built-in browser webcam snapshot scanning utilizing Streamlit camera input controls.
- **Day 7 (June 14):** Interactive inventory count adjustment inputs allowing supervisors to manually override AI counts.
- **Day 8 (June 15):** SKU catalog association deletions and SQLite database logs reset danger zone button.
- **Day 9 (June 16):** Analytics logs date-range query filters updating Plotly trend visualizations.
- **Day 10 (June 17):** Scan ID history search input tools and CSV log sheet data exporter.

### **Phase 3: Deep Audits & Layout Upgrades**
- **Day 11 (June 18):** Drill-down database listings dropdown to audit itemized counts inside past scan sessions.
- **Day 12 (June 19):** Upgraded active SKU mappings display into interactive grid cards with custom emojis and CSS styling.
- **Day 13 (June 20):** SQL query helpers to target and delete single scanning sessions from database history logs.
- **Day 14 (June 21):** Dynamic Plotly visualization format configuration parameters (Area, Line, Bar).
- **Day 15 (June 22):** Dedicated Stock Alerts tab reporting replenishment lists and PDF/CSV Purchase Orders.

### **Phase 4: Operations & Resiliency Utilities**
- **Day 16 (June 23):** Built persistent SQL Alert History tables tracking warning occurrences over time with Plotly alert frequency analytics.
- **Day 17 (June 24):** Added multi-theme custom color palettes (Classic Indigo, Forest Emerald, Sunset Amber, Crimson Coral) to all Plotly analytics.
- **Day 18 (June 25):** Implemented executive-level stats metrics cards at the top of the analytics dashboard (Total Scans, Peak Value, Average Valuation, Stock Alerts).
- **Day 19 (June 26):** Created dynamic procurement quantity overrides on the alerts panel, updating estimated costs and CSV PO exports in real-time.
- **Day 20 (June 27):** Developed SKU catalog JSON backup downloads and drag-and-drop config sheet restoration/imports.
- **Day 21 (June 28):** Project documentation cleanup and consolidated daily implementation logs.


---

## ⚙️ Quick Start

1. **Clone the repository:**
   ```bash
   git clone https://github.com/gnansruthir/smart-inventory-counter.git
   cd smart-inventory-counter
   ```
2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
3. **Run the Streamlit application:**
   ```bash
   streamlit run app.py
   ```
