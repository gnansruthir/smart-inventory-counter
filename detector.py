import cv2
import numpy as np
from ultralytics import YOLO

class InventoryDetector:
    def __init__(self, model_path="yolov8n.pt"):
        """
        Initializes the YOLOv8 model.
        """
        
        self.model = YOLO(model_path)

    def detect_image(self, image_path_or_buf):
        """
        Runs object detection on an image.
        Returns the annotated image and counts of detected classes.
        
        if isinstance(image_path_or_buf, str):
            image = cv2.imread(image_path_or_buf)
        else:
            # Decode image from buffer
            file_bytes = np.frombuffer(image_path_or_buf.read(), np.uint8)
            image = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)

        if image is None:
            raise ValueError("Could not read image source")

        # Run inference
        results = self.model(image)
        result = results[0]  # YOLO returns a list of results

        # Copy image for drawing bounding boxes
        annotated_image = result.plot()  # Ultralytics built-in plot function

        # Count objects
        class_counts = {}
        for box in result.boxes:
            class_id = int(box.cls[0])
            class_name = self.model.names[class_id]
            class_counts[class_name] = class_counts.get(class_name, 0) + 1

        # Convert annotated image from BGR (OpenCV) to RGB (Streamlit expects RGB)
        annotated_image_rgb = cv2.cvtColor(annotated_image, cv2.COLOR_BGR2RGB)

        return annotated_image_rgb, class_counts

# Quick self-test script block
if __name__ == "__main__":
    print("YOLOv8 Inventory Detector initialized successfully.")
