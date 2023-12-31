import cv2
import numpy as np
from PIL import Image
import tensorflow as tf

# Load the TFLite model
interpreter = tf.lite.Interpreter(model_path='model.tflite')
interpreter.allocate_tensors()

# Get input and output details
input_details = interpreter.get_input_details()
output_details = interpreter.get_output_details()

# Define the class labels
class_labels = ['safe driving','texting - right','talking on the phone - right','texting - left','talking on the phone - left','operating the radio','drinking','reaching behind','hair and makeup','talking to passenger']

# Define the font and text color for the predicted class label
font = cv2.FONT_HERSHEY_SIMPLEX
font_scale = 0.5
text_color = (0, 255, 0)

# Initialize the video capture object with the default camera
cap = cv2.VideoCapture(0)

while True:
    # Read a frame from the video capture object
    ret, frame = cap.read()

    # Convert the frame to a PIL Image
    image = Image.fromarray(frame)

    # Resize the image to the required input size of the model
    image = image.resize((280, 200))

    # Convert the image to a numpy array
    image_array = np.array(image)

    # Expand the dimensions of the array to match the expected input shape of the model
    image_array = np.expand_dims(image_array, axis=0)

    # Normalize the pixel values of the image
    image_array = image_array / 255.0

    # Convert the input tensor to the expected data type
    input_data = tf.convert_to_tensor(image_array, dtype=input_details[0]['dtype'])

    # Set the tensor data into the input tensor
    interpreter.set_tensor(input_details[0]['index'], input_data)

    # Run inference
    interpreter.invoke()

    # Get the output tensor and make predictions
    output_data = interpreter.get_tensor(output_details[0]['index'])
    predicted_class_index = np.argmax(output_data[0])
    predicted_class = class_labels[predicted_class_index]
    accuracy = output_data[0][predicted_class_index]

    # Draw a green rectangle border around the image
    border_color = (0, 255, 0)
    border_size = 2
    frame = cv2.rectangle(frame, (0, 0), (frame.shape[1], frame.shape[0]), border_color, border_size)

    # Add the predicted class label and its accuracy to the frame
    if accuracy*100 >= 78:
        text = f"{predicted_class} ({accuracy*100:.2f} %)"
    else:
        text = ''
    text_size, _ = cv2.getTextSize(text, font, font_scale, border_size)
    text_x = int((frame.shape[1] - text_size[0]) / 2)
    text_y = int(frame.shape[0] - text_size[1] - 10)
    frame = cv2.putText(frame, text, (text_x, text_y), font, font_scale, text_color, border_size)

    # Display the frame
    cv2.imshow('Prediction', frame)

    # Check if the user pressed the 'q' key to quit
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Release the video capture object and close the display window
cap.release()
cv2.destroyAllWindows()