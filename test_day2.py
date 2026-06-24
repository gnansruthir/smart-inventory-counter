from db_manager import DBManager
import json

def run_day2_verification():
    print("--- Day 2 Verification Test ---")
    with open("sku_mapping.json", "r") as f:
        mapping = json.load(f)
    print(f"SKU Mappings loaded successfully. Registered classes: {list(mapping.keys())}")
    db = DBManager("data/test_inventory.db")
    print("Database connection and schema verification completed.")
    test_items = [
        {"sku_name": "Coca-Cola 250ml", "detected_class": "bottle", "count": 12, "unit_price": 1.99},
        {"sku_name": "Coffee Cup Ceramic", "detected_class": "cup", "count": 2, "unit_price": 4.50}
    ]
    total_val = sum(i["count"] * i["unit_price"] for i in test_items)
    total_items = sum(i["count"] for i in test_items)
    
    scan_id = db.log_scan(total_items, total_val, test_items)
    print(f"Test scan successfully logged to database. Assigned Scan ID: {scan_id}")
    all_scans = db.get_all_scans()
    print("Historical scans retrieved from SQLite:")
    for scan in all_scans:
        print(f" - Scan ID: {scan[0]} | Timestamp: {scan[1]} | Total Items: {scan[2]} | Total Value: ${scan[3]:.2f}")
        
    # Clean up test database
    import os
    if os.path.exists("data/test_inventory.db"):
        os.remove("data/test_inventory.db")
        print("Test database cleaned up successfully.")

if __name__ == "__main__":
    run_day2_verification()
