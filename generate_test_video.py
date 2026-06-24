import cv2
import numpy as np

def create_synthetic_video_h264(output_path="test_inventory.mp4", duration_seconds=5, fps=24):
    width, height = 640, 480
    
    # Try avc1 (H264) codec first for web compatibility, fallback to mp4v if it fails
    try:
        fourcc = cv2.VideoWriter_fourcc(*'avc1')
        out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
        if not out.isOpened():
            raise Exception("avc1 failed")
    except Exception:
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

    total_frames = duration_seconds * fps
    for i in range(total_frames):
        frame = np.ones((height, width, 3), dtype=np.uint8) * 40
        
        # Shelf lines
        cv2.line(frame, (50, 150), (590, 150), (100, 100, 100), 5)
        cv2.line(frame, (50, 320), (590, 320), (100, 100, 100), 5)
        
        # Item 1: Moving slightly to simulate motion tracking
        x_pos_1 = 150 + int(i * 1.5)
        # We will draw shapes that look like bottles/cups to give YOLO a chance to detect them
        # Let's draw a light blue bottle
        cv2.rectangle(frame, (x_pos_1, 60), (x_pos_1 + 40, 145), (200, 150, 50), -1) 
        
        # Item 2: Static green bottle
        cv2.rectangle(frame, (350, 60), (390, 145), (50, 200, 50), -1) 
        
        # Item 3: Static cup
        cv2.rectangle(frame, (250, 220), (290, 310), (100, 100, 200), -1)
        
        out.write(frame)
        
    out.release()
    print(f"H.264 compatible synthetic test video saved to: {output_path}")

if __name__ == "__main__":
    create_synthetic_video_h264()
