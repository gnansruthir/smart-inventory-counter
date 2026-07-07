import cv2
import numpy as np
from ultralytics import YOLO

class InventoryDetector:
    def __init__(self, model_path="yolov8n.pt"):
        """
        Initializes the YOLOv8 model.
        """
        self.model = YOLO(model_path)
        
        # COCO Class IDs: 24 (backpack), 26 (handbag), 28 (suitcase), 39 (bottle), 41 (cup), 45 (bowl), 73 (book), 75 (vase)
        self.COCO_RETAIL_CLASSES = [24, 26, 28, 39, 41, 45, 73, 75]
        
        # Map raw COCO prediction names to our catalog inventory keys (bottle, box, cup)
        self.RETAIL_NAME_MAP = {
            "backpack": "box",
            "handbag": "box",
            "suitcase": "box",
            "book": "box",
            "bottle": "bottle",
            "vase": "bottle",
            "cup": "cup",
            "bowl": "cup"
        }

    def detect_image(self, image_path_or_buf, conf=0.25):
        """
        Runs object detection on an image.
        Returns the annotated image and counts of detected classes.
        """
        if isinstance(image_path_or_buf, str):
            image = cv2.imread(image_path_or_buf)
        else:
            # Decode image from buffer
            file_bytes = np.frombuffer(image_path_or_buf.read(), np.uint8)
            image = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)

        if image is None:
            raise ValueError("Could not read image source")
            
        results = self.model(image, conf=conf, classes=self.COCO_RETAIL_CLASSES)
        result = results[0]  
        
        # Draw custom bounding boxes manually to ignore any outside allowed classes
        annotated_image = image.copy()
        class_counts = {}
        
        if result.boxes is not None:
            boxes_data = result.boxes.xyxy.cpu().numpy()
            clss = result.boxes.cls.cpu().numpy().astype(int)
            confs = result.boxes.conf.cpu().numpy()
            
            for idx, box in enumerate(boxes_data):
                cls_id = clss[idx]
                raw_name = self.model.names[cls_id]
                
                if raw_name in self.RETAIL_NAME_MAP:
                    mapped_name = self.RETAIL_NAME_MAP[raw_name]
                    class_counts[mapped_name] = class_counts.get(mapped_name, 0) + 1
                    
                    # Draw box and label
                    x1, y1, x2, y2 = map(int, box)
                    conf_val = confs[idx]
                    label = f"{mapped_name} {conf_val:.2f}"
                    
                    # Blue for bottles, Purple for boxes, Green for cups
                    color = (255, 0, 0) # Blue
                    if mapped_name == "box":
                        color = (128, 0, 128) # Purple
                    elif mapped_name == "cup":
                        color = (0, 128, 0) # Green
                        
                    cv2.rectangle(annotated_image, (x1, y1), (x2, y2), color, 2)
                    cv2.putText(annotated_image, label, (x1, max(15, y1 - 5)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
            
        annotated_image_rgb = cv2.cvtColor(annotated_image, cv2.COLOR_BGR2RGB)
        return annotated_image_rgb, class_counts

    def track_frame(self, frame, conf=0.25):
        try:
            results = self.model.track(frame, persist=True, tracker="bytetrack.yaml", verbose=False, conf=conf, classes=self.COCO_RETAIL_CLASSES)
        except Exception:
            # Fall back to standard prediction if the tracking engine is not supported or fails
            results = self.model(frame, verbose=False, conf=conf, classes=self.COCO_RETAIL_CLASSES)
            
        result = results[0]
        
        # Draw custom bounding boxes manually to prevent plotting forbidden classes (like refrigerator, train)
        annotated_frame = frame.copy()
        active_tracks = {}
        
        if result.boxes is not None:
            boxes_data = result.boxes.xyxy.cpu().numpy()
            clss = result.boxes.cls.cpu().numpy().astype(int)
            confs = result.boxes.conf.cpu().numpy()
            ids = result.boxes.id.cpu().numpy().astype(int) if (hasattr(result.boxes, 'id') and result.boxes.id is not None) else None
            
            for idx, box in enumerate(boxes_data):
                cls_id = clss[idx]
                raw_name = self.model.names[cls_id]
                
                if raw_name in self.RETAIL_NAME_MAP:
                    mapped_name = self.RETAIL_NAME_MAP[raw_name]
                    obj_id = str(ids[idx]) if ids is not None else f"det_{idx}"
                    active_tracks[obj_id] = mapped_name
                    
                    # Draw box and label
                    x1, y1, x2, y2 = map(int, box)
                    conf_val = confs[idx]
                    label = f"{mapped_name} {conf_val:.2f}"
                    if ids is not None:
                        label = f"id:{ids[idx]} {label}"
                        
                    # Blue for bottles, Purple for boxes, Green for cups
                    color = (255, 0, 0) # Blue
                    if mapped_name == "box":
                        color = (128, 0, 128) # Purple
                    elif mapped_name == "cup":
                        color = (0, 128, 0) # Green
                        
                    cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), color, 2)
                    cv2.putText(annotated_frame, label, (x1, max(15, y1 - 5)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

        annotated_frame_rgb = cv2.cvtColor(annotated_frame, cv2.COLOR_BGR2RGB)
        return annotated_frame_rgb, active_tracks

# Quick self-test script block
if __name__ == "__main__":
    print("YOLOv8 Inventory Detector initialized successfully.")
