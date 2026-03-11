import os
import sys
import logging
import time
from pathlib import Path
import glob
import json

import numpy as np
import cv2
import yaml
from PIL import Image
import xgoscreen.LCD_2inch as LCD_2inch

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from edgetpumodel import EdgeTPUModel
from utils import resize_and_pad, get_image_tensor, save_one_json, coco80_to_coco91_class

class DetectionSystem:
    def __init__(self):
        self.model_path = '/home/pi/edgetpu-yolo/yolov5s-int8_edgetpu_160.tflite'
        self.names_path = '/home/pi/edgetpu-yolo/data/coco.yaml'
        self.conf_thresh = 0.25
        self.iou_thresh = 0.45
        self.device = 0  # Default camera index
        self.model = EdgeTPUModel(self.model_path, self.names_path, self.conf_thresh, self.iou_thresh)
        self.input_size = self.model.get_image_size()
        self.human_detected = False

        # Initialize display
        self.display = LCD_2inch.LCD_2inch()
        self.display.clear()

    def run_detection(self):
        cam = cv2.VideoCapture(self.device)
        if not cam.isOpened():
            logger.error("Failed to open camera")
            return

        try:
            while True:
                res, frame = cam.read()
                if not res:
                    logger.error("Failed to read frame from camera")
                    break
                
                full_image, net_image, pad = get_image_tensor(frame, self.input_size[0])
                preds = self.model.forward(net_image)
                self.human_detected = self.is_person_found(preds)

                # Process predictions to get coordinates in original image size
                processed_preds = self.model.process_predictions(preds[0], full_image, pad)
                
                # Convert the frame to a PIL image and display it on the XGO screen
                pil_image = Image.fromarray(cv2.cvtColor(full_image, cv2.COLOR_BGR2RGB))
                pil_image = pil_image.resize((self.display.height, self.display.width))
                self.display.ShowImage(pil_image)

                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
        finally:
            cam.release()
            cv2.destroyAllWindows()
            
    def is_person_found(self, det):
        person_index = 0  # Assuming 'person' class ID is 0
        # Iterate over each detection array in det
        for detection in det:
            for entry in detection:
                if int(entry[5]) == person_index:
                    print("Person detected!")  # Print message when a person is found
                    return True
        print("No person detected.")  # Print message when no person is found
        return False

    def get_human_detection_status(self):
        return self.human_detected

if __name__ == "__main__":
    detection = DetectionSystem()
    detection.run_detection()

