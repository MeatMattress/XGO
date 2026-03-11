import cv2
import numpy as np
import tflite_runtime.interpreter as tflite
from pycoral.utils.edgetpu import make_interpreter, run_inference
import threading

# Global variable for the frame
frame = None
lock = threading.Lock()

def capture_video():
    global frame
    cap = cv2.VideoCapture(0)  # Change the index if you are using a different camera
    while True:
        ret, new_frame = cap.read()
        if not ret:
            break
        with lock:
            frame = new_frame

def run_inference_thread(interpreter, labels):
    global frame
    while True:
        if frame is not None:
            with lock:
                current_frame = frame.copy()

            # Prepare the frame for inference
            input_shape = input_details[0]['shape']
            height, width = input_shape[1], input_shape[2]
            image_resized = cv2.resize(current_frame, (width, height))
            input_data = np.expand_dims(image_resized, axis=0).astype(np.uint8)

            # Run detection
            boxes, class_ids, scores, count = detect_objects(interpreter, input_data)
            draw_detections(current_frame, boxes, class_ids, scores, count, labels)

            # Display the frame with detections
            cv2.imshow('Object Detection', current_frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

def detect_objects(interpreter, image):
    run_inference(interpreter, image.tobytes())
    output_data = interpreter.tensor(output_details[0]['index'])()[0]
    boxes = []
    class_ids = []
    scores = []

    scale = output_details[0]['quantization_parameters']['scales'][0]
    zero_point = output_details[0]['quantization_parameters']['zero_points'][0]

    for detection in output_data:
        score = scale * (detection[4] - zero_point)
        if score > 0.5:
            ymin = scale * (detection[0] - zero_point)
            xmin = scale * (detection[1] - zero_point)
            ymax = scale * (detection[2] - zero_point)
            xmax = scale * (detection[3] - zero_point)
            class_id = np.argmax(detection[5:])
            boxes.append([ymin, xmin, ymax, xmax])
            class_ids.append(class_id)
            scores.append(score)
    return np.array(boxes), np.array(class_ids), np.array(scores), len(boxes)

def draw_detections(image, boxes, class_ids, scores, count, labels):
    for i in range(count):
        ymin, xmin, ymax, xmax = boxes[i]
        xmin = int(xmin * image.shape[1])
        xmax = int(xmax * image.shape[1])
        ymin = int(ymin * image.shape[0])
        ymax = int(ymax * image.shape[0])
        class_id = int(class_ids[i])
        label = labels[class_id]
        score = scores[i]
        cv2.rectangle(image, (xmin, ymin), (xmax, ymax), (0, 255, 0), 2)
        cv2.putText(image, f'{label} {score:.2f}', (xmin, ymin - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

# Load the TFLite model with Edge TPU delegate
model_path = '../../model/yolov5s-int8_edgetpu.tflite'
interpreter = make_interpreter(model_path)
interpreter.allocate_tensors()

# Get model input and output details
input_details = interpreter.get_input_details()
output_details = interpreter.get_output_details()

labels = ['person', 'bicycle', 'car', 'motorcycle', 'airplane', 'bus', 'train', 'truck', 'boat', 'traffic light', 'fire hydrant', 'stop sign', 'parking meter', 'bench', 'bird', 'cat', 'dog', 'horse', 'sheep', 'cow', 'elephant', 'bear', 'zebra', 'giraffe', 'backpack', 'umbrella', 'handbag', 'tie', 'suitcase', 'frisbee', 'skis', 'snowboard', 'sports ball', 'kite', 'baseball bat', 'baseball glove', 'skateboard', 'surfboard', 'tennis racket', 'bottle', 'wine glass', 'cup', 'fork', 'knife', 'spoon', 'bowl', 'banana', 'apple', 'sandwich', 'orange', 'broccoli', 'carrot', 'hot dog', 'pizza', 'donut', 'cake', 'chair', 'couch', 'potted plant', 'bed', 'dining table', 'toilet', 'tv', 'laptop', 'mouse', 'remote', 'keyboard', 'cell phone', 'microwave', 'oven', 'toaster', 'sink', 'refrigerator', 'book', 'clock', 'vase', 'scissors', 'teddy bear', 'hair drier', 'toothbrush']

video_thread = threading.Thread(target=capture_video)
inference_thread = threading.Thread(target=run_inference_thread, args=(interpreter, labels))

video_thread.start()
inference_thread.start()

video_thread.join()
inference_thread.join()
