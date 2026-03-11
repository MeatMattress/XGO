import sys
sys.path.append('/home/pi/edgetpu-yolo')
from testDetect import DetectionSystem
from xgolib import XGO
import threading
import time

def control_movement(detection_system, dog):
    frame_center_x = 160  # Assuming the frame width is 320
    while True:
        is_person_found, person_bbox = detection_system.get_human_detection_status_with_bbox()
        if is_person_found:
            x1, y1, x2, y2 = person_bbox
            bbox_center_x = (x1 + x2) // 2

            if bbox_center_x < frame_center_x - 20:
                dog.turn(-50)  # Turn left
            elif bbox_center_x > frame_center_x + 20:
                dog.turn(50)  # Turn right
            else:
                dog.move('x',5)  # Move forward
        else:
            dog.stop()  # Stop moving if no person is detected
        time.sleep(0.5)

def main():
    dog = XGO(port='/dev/ttyAMA0', version="xgolite")
    detection_system = DetectionSystem()

    detection_thread = threading.Thread(target=detection_system.run_detection)
    movement_thread = threading.Thread(target=control_movement, args=(detection_system, dog))
    
    detection_thread.start()
    movement_thread.start()

    try:
        detection_thread.join()
        movement_thread.join()
    except KeyboardInterrupt:
        print("Shutting down...")
        sys.exit()

if __name__ == "__main__":
    main()
