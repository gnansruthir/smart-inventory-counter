# 📦 Smart Inventory Counter

An automated, computer vision-powered retail inventory counting system. This project uses **YOLOv8** for real-time object detection and tracking, presenting results via an interactive **Streamlit** dashboard.

**🚀 Live Demo:** [smart-inventory-counter.streamlit.app](https://smart-inventory-counter-jkmwvlbfhayngzuef3xpgz.streamlit.app/)

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
