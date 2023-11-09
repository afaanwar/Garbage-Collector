import tkinter as tk
from tkinter import ttk
import cv2
import time
from tensorflow.keras.models import load_model
from PIL import Image, ImageTk
import numpy as np
from realsense_camera import *
import threading
import queue
import serial
import json

# Load the saved model
model = load_model('keras_model1.h5', compile=False)
class_labels = ['Paper', 'Metal', 'Plastic', 'Glass', 'Empty']
font = cv2.FONT_HERSHEY_SIMPLEX
font_scale = 0.5
text_color = (0, 255, 0)

rs = RealsenseCamera()

class App:
    def __init__(self, root):
        self.root = root
        self.data = [{"ID": "Wait", "Prediction": "None", "Name": "None", "Points": 0}]
        self.root.title("Environmental UI Example")
        self.root.attributes('-fullscreen', True)  # Make the window full screen

        # Set up variables for dynamic updating
        self.name_var = tk.StringVar()
        self.id_var = tk.StringVar()
        self.prediction_var = tk.StringVar()
        self.total_points_var = tk.StringVar()

        # Load your logo (replace 'logo.png' with your actual logo file)
        self.logo_image = tk.PhotoImage(file='logo.png')

        # Create a frame for the four boxes
        self.boxes_frame = ttk.Frame(root, padding=10)
        self.boxes_frame.grid(row=1, column=0, columnspan=4)

        # Create and place the logo at the top center
        self.logo_label = tk.Label(root, image=self.logo_image, bg='#F0F0F0')  # Match the background color
        self.logo_label.grid(row=0, column=0, columnspan=4, pady=10)

        # Create and place the four boxes side by side
        ttk.Label(self.boxes_frame, text="Name", font=("Helvetica", 14)).grid(row=0, column=0, padx=10)
        ttk.Label(self.boxes_frame, text="ID", font=("Helvetica", 14)).grid(row=0, column=1, padx=10)
        ttk.Label(self.boxes_frame, text="Prediction", font=("Helvetica", 14)).grid(row=0, column=2, padx=10)
        ttk.Label(self.boxes_frame, text="Total Points", font=("Helvetica", 14)).grid(row=0, column=3, padx=10)

        ttk.Label(self.boxes_frame, textvariable=self.name_var, font=("Helvetica", 14), relief="solid", padding=5).grid(row=1, column=0, padx=10)
        ttk.Label(self.boxes_frame, textvariable=self.id_var, font=("Helvetica", 14), relief="solid", padding=5).grid(row=1, column=1, padx=10)
        ttk.Label(self.boxes_frame, textvariable=self.prediction_var, font=("Helvetica", 14), relief="solid", padding=5).grid(row=1, column=2, padx=10)
        ttk.Label(self.boxes_frame, textvariable=self.total_points_var, font=("Helvetica", 14), relief="solid", padding=5).grid(row=1, column=3, padx=10)

        # Initialize the data
        self.update_data()

        # Create a thread to run the main function
        self.thread_stop_event = threading.Event()
        self.thread = threading.Thread(target=self.run_main_function)
        self.thread.start()

    def update_data(self):
        # Replace these values with your actual data
        self.name_var.set("عبدارحمن")
        self.id_var.set(self.data[-1]["ID"])
        self.prediction_var.set(self.data[-1]["Prediction"])
        self.total_points_var.set(self.data[-1]["Points"])

        # Schedule the next update after 1000 milliseconds (1 second)
        self.root.after(1000, self.update_data)

    def run_main_function(self):
        # Call the main function with the provided code
        main(self.data)

    def on_close(self):
        # Stop the thread when the application is closed
        self.thread_stop_event.set()
        self.root.destroy()


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

def main(data_gui):
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
                        data_gui.append({"ID": int(str(data)[11:]), "Prediction": 0, "Points": 0})
                        while not done:
                            p = []
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
                                bgr_frame = cv2.rectangle(bgr_frame, (0, 0), (bgr_frame.shape[1], bgr_frame.shape[0]),
                                                          border_color, border_size)

                                # Add the predicted class label and its accuracy to the frame
                                if accuracy * 100 >= 78:
                                    text = f"{predicted_class} ({accuracy * 100:.2f})"
                                else:
                                    text = ''

                                p.append(predicted_class)
                                print(p, most_common(p))
                                text_size, _ = cv2.getTextSize(text, font, font_scale, border_size)
                                text_x = int((bgr_frame.shape[1] - text_size[0]) / 2)
                                text_y = int((bgr_frame.shape[0] - text_size[1]) - 10)
                                bgr_frame = cv2.putText(bgr_frame, text, (text_x, text_y), font, font_scale, text_color,
                                                        border_size)

                                # Display the frame
                                # cv2.imshow('Prediction', bgr_frame)

                                # Check if the user pressed the 'q' key to quit
                                if cv2.waitKey(1) & 0xFF == ord('q'):
                                    break
                            if most_common(p) == "Empty":
                                done = True
                            else:
                                data_gui[-1]["Prediction"] = most_common(p)
                                data_gui[-1]["Points"] += 1
                                ser.write(str(most_common(p)).encode())
                                time.sleep(8)
                        # ser.write(str([x for i,x in response]).encode())
                        ser.write(b'Done')
                        # ser.write(b'{"ID": 520176, "Plastic": 0, "Metal": 0, "Paper": 0, "Glass": 0}\r\n')
                    except Exception as e:
                        #ser.write(b'Done')
                        print(e)
                else:
                    print("No card number found in the data.")
                    pass

        except serial.SerialException:
            print(f"Failed to connect to {port}")
            pass


if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.protocol("WM_DELETE_WINDOW", app.on_close)
    root.mainloop()

