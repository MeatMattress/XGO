import numpy as np
from tflite_runtime.interpreter import Interpreter
from tflite_runtime.interpreter import load_delegate
import cv2

# Load the TensorFlow Lite model with Edge TPU delegate
interpreter = Interpreter(model_path='../../model/Model.tflite',
                          experimental_delegates=[load_delegate('libedgetpu.so.1.0')])

# Allocate tensors
interpreter.allocate_tensors()

# Get input and output tensors
input_details = interpreter.get_input_details()
output_details = interpreter.get_output_details()

# Set the model input shape
input_shape = input_details[0]['shape']

def preprocess(image):
    """ Preprocess the input image """
    image_resized = cv2.resize(image, (input_shape[2], input_shape[3]))
    image_resized = np.transpose(image_resized, (2, 0, 1))  # Change shape from (H, W, C) to (C, H, W)
    image_resized = np.expand_dims(image_resized, axis=0)
    return image_resized.astype(np.float32)

def infer(image):
    """ Run inference on the input image """
    input_data = preprocess(image)
    interpreter.set_tensor(input_details[0]['index'], input_data)
    interpreter.invoke()
    output_data = interpreter.get_tensor(output_details[0]['index'])
    return output_data

def main():
    # Replace with your own video or image input
    cap = cv2.VideoCapture(0)  # For webcam

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # Run inference
        output = infer(frame)

        # Process the output as needed
        # For example, drawing bounding boxes on the frame
        # Add your custom post-processing code here

        # Display the frame with inference results
        cv2.imshow('Inference', frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == '__main__':
    main()
