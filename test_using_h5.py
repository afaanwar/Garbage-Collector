import cv2
import time
from tensorflow.keras.models import load_model
from PIL import Image
import numpy as np
from realsense_camera import *
import tensorflow_hub as hub

print("launched")

# Load the saved model
model = load_model('keras_model1.h5', compile=False)
print("model loaded")

# Define the class labels
class_labels = ['Paper', 'Metal', 'Plastic','Glass', 'Empty']
# Define the font and text color for the predicted class label
font = cv2.FONT_HERSHEY_SIMPLEX
font_scale = 0.5
text_color = (0, 255, 0)

rs = RealsenseCamera()

import serial

def most_common(lst):
    if not lst:
        return None  # Handle the case of an empty list

    most_common_element = None
    max_count = 0

    for item in lst:
        count = 0
        for element in lst:
            if element == item:
                count += 1
        if count > max_count:
            most_common_element = item
            max_count = count

    return most_common_element

def is_card_number(data):
    if "Unknown" not in data:
        return any(char.isdigit() for char in data)

import json

def main():
    for i in range(11):  # Try USB devices from /dev/ttyUSB0 to /dev/ttyUSB10
        port = f"/dev/ttyUSB{i}"
        try:
            ser = serial.Serial(port, 115200)  # Adjust baud rate as needed
            while True:
                print("read")
                data = ser.readline().decode("utf-8").strip()  # Read data from the serial port
                print(str(data))
                if is_card_number(data):
                    try:
                        done = False
                        response = {"ID": int(str(data)[11:]),"Plastic": 0, "Glass": 0, "Paper": 0, "Metal": 0}
                        while not done:
                            p = []
                            print(response)
                            print("Card number found:", int(str(data)[11:]))
                            for i in range(10):
                                # Read a frame from the video capture object
                                ret, bgr_frame, depth_frame = rs.get_frame_stream()
                                # Convert the frame to a PIL Image
                                image = Image.fromarray(bgr_frame, 'RGB')

                                # Resize the image to the required input size of the model
                                image = image.resize((224, 224))

                                # Convert the image to a numpy array
                                image_array = np.array(image)

                                # Expand the dimensions of the array to match the expected input shape of the model
                                image_array = np.expand_dims(image_array, axis=0)

                                # Normalize the pixel values of the image
                                image_array = image_array / 250.0

                                # Make predictions using the loaded model
                                predictions = model.predict(image_array)

                                # Get the predicted class and its probability
                                predicted_class_index = np.argmax(predictions[0])
                                predicted_class = class_labels[predicted_class_index]
                                accuracy = predictions[0][predicted_class_index]
                                print(predicted_class)
                                # Draw a green rectangle border around the image
                                border_color = (0, 255, 0)
                                border_size = 2
                                bgr_frame = cv2.rectangle(bgr_frame, (0, 0), (bgr_frame.shape[1], bgr_frame.shape[0]), border_color, border_size)

                                # Add the predicted class label and its accuracy to the frame
                                if accuracy*100 >= 78:
                                    text = f"{predicted_class} ({accuracy*100:.2f})"
                                else:
                                    text = ''

                                p.append(predicted_class) 
                                print(p, most_common(p))
                                text_size, _= cv2.getTextSize(text,font, font_scale,border_size)
                                text_x =  int((bgr_frame.shape[1] - text_size[0]) / 2)
                                text_y =  int((bgr_frame.shape[0] - text_size[1]) - 10)
                                bgr_frame = cv2.putText(bgr_frame, text, (text_x, text_y), font, font_scale, text_color, border_size)
                                
                                # Display the frame
                                #cv2.imshow('Prediction', bgr_frame)
                                
                                # Check if the user pressed the 'q' key to quit
                                if cv2.waitKey(1) & 0xFF == ord('q'):
                                    break
                            if most_common(p) == "Empty":
                                done = True
                            else:
                                ser.write(str(most_common(p)).encode())
                                time.sleep(8)
                        #ser.write(str([x for i,x in response]).encode())
                        ser.write(b'Done')
                        #ser.write(b'{"ID": 520176, "Plastic": 0, "Metal": 0, "Paper": 0, "Glass": 0}\r\n')
                    except Exception as e:
                        #ser.write(b'Done')
                        print(e)
                else:
                    print("No card number found in the data.")
                    pass

        except serial.SerialException:
            print(f"Failed to connect to {port}")
            pass

main()
