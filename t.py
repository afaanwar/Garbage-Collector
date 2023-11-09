import cv2
from tensorflow.keras.models import load_model
from PIL import Image
import numpy as np
from realsense_camera import *
import tensorflow_hub as hub

print("launched")

# Load the saved model
model = load_model('keras_model.h5', compile=False)
print("model loaded")

# Define the class labels
class_labels = ['paper', 'metal', 'plastic','white-glass']
# Define the font and text color for the predicted class label
font = cv2.FONT_HERSHEY_SIMPLEX
font_scale = 0.5
text_color = (0, 255, 0)

rs = RealsenseCamera()

while True:
    # Read a frame from the video capture object
    ret, bgr_frame , depth_frame = rs.get_frame_stream()

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
    print(text)
    text_size, _ = cv2.getTextSize(text, font, font_scale, border_size)
    text_x = int((bgr_frame.shape[1] - text_size[0]) / 2)
    text_y = int(bgr_frame.shape[0] - text_size[1] - 10)
    bgr_frame = cv2.putText(bgr_frame, text, (text_x, text_y), font, font_scale, text_color, border_size)

    # Display the frame
    cv2.imshow('Prediction', bgr_frame)

    # Check if the user pressed the 'q' key to quit
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Release the video capture object and close the display window
cap.release()
cv2.destroyAllWindows()

