import sys
sys.path.append('/home/pi/edgetpu-yolo')
from detect import DetectionSystem
from xgolib import XGO
import threading
import time

def control_claw(detection_system, dog):
    while True:
        is_person_found = detection_system.get_human_detection_status()
        if is_person_found:
            dog.claw(0)
        else:
            dog.claw(255)
        time.sleep(1)

def main():
    dog = XGO(port='/dev/ttyAMA0', version="xgolite")
    detection_system = DetectionSystem()

    detection_thread = threading.Thread(target=detection_system.run_detection)
    detection_thread.start()

    claw_thread = threading.Thread(target=control_claw, args=(detection_system, dog))
    claw_thread.start()

    detection_thread.join()
    claw_thread.join()

if __name__ == "__main__":
    main()
