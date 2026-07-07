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
        
        # Map raw COCO prediction names to our catalog inventory keys (bottle, box, cup, can)
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
        annotated_image = result.plot()  
        class_counts = {}
        for box in result.boxes:
            class_id = int(box.cls[0])
            raw_class_name = self.model.names[class_id]
            mapped_name = self.RETAIL_NAME_MAP.get(raw_class_name, raw_class_name)
            class_counts[mapped_name] = class_counts.get(mapped_name, 0) + 1
            
        annotated_image_rgb = cv2.cvtColor(annotated_image, cv2.COLOR_BGR2RGB)
        return annotated_image_rgb, class_counts

    def track_frame(self, frame, conf=0.25):
        try:
            results = self.model.track(frame, persist=True, tracker="bytetrack.yaml", verbose=False, conf=conf, classes=self.COCO_RETAIL_CLASSES)
        except Exception:
            # Fall back to standard prediction if the tracking engine is not supported or fails
            results = self.model(frame, verbose=False, conf=conf, classes=self.COCO_RETAIL_CLASSES)
            
        result = results[0]
        annotated_frame = result.plot()
        annotated_frame_rgb = cv2.cvtColor(annotated_frame, cv2.COLOR_BGR2RGB)

        active_tracks = {}
        if result.boxes is not None:
            clss = result.boxes.cls.int().tolist()
            if hasattr(result.boxes, 'id') and result.boxes.id is not None:
                ids = result.boxes.id.int().tolist()
                for obj_id, cls_id in zip(ids, clss):
                    raw_name = self.model.names[cls_id]
                    mapped_name = self.RETAIL_NAME_MAP.get(raw_name, raw_name)
                    active_tracks[str(obj_id)] = mapped_name
            else:
                for idx, cls_id in enumerate(clss):
                    raw_name = self.model.names[cls_id]
                    mapped_name = self.RETAIL_NAME_MAP.get(raw_name, raw_name)
                    active_tracks[f"det_{idx}"] = mapped_name

        return annotated_frame_rgb, active_tracks

# Quick self-test script block
if __name__ == "__main__":
    print("YOLOv8 Inventory Detector initialized successfully.")
