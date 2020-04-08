import cv2
import face_recognition
import time
import os
import models
import numpy as np

# MODEL_NAME = 'Trained_ckplus_model.h5'
MODEL_NAME = 'model_195.h5'
class_labels = {0: 'Anger', 1: 'Disgust', 2: 'Fear', 3: 'Happy', 4: 'Sad', 5: 'Surprise', 6: 'Neutral'}

"""
Not used in current Flask App, but could in the future :P
Reads local webcam feed and processes a frame every 0.5 seconds (can modify using WEBCAM_FRAME_READ_TIME variable),
Annotates result and displays it in real-time
"""
def create_webcam_output():
    WEBCAM_FRAME_READ_TIME = 0.5

    model = load_model()

    video_capture = cv2.VideoCapture(0)
    face_locations = []

    # Start timer
    start_time = time.time()

    while True:
        ret, frame = video_capture.read()

        # Reducing frame to 1/2 of its size. Used for faster execution
        small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
        rgb_small_frame = small_frame[:, :, ::-1]

        # Only process every other frame of video to save time
        if time.time() - start_time >= WEBCAM_FRAME_READ_TIME:  # Check if 0.5 sec has passed

            # Find all the faces in the current frame of video
            face_locations = face_recognition.face_locations(rgb_small_frame)
            print(face_locations)

            # Set start timer
            start_time = time.time()

        # Annotate frame with right class label
        detect_emotion_and_annotate_frame(frame, face_locations[:2], model, scale_multiplier=4)

        # Display the resulting image
        cv2.imshow('Video', frame)

        # Hit 'q' on the keyboard to quit!
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    # Release handle to the webcam
    video_capture.release()
    cv2.destroyAllWindows()


def load_model():
    # model = models.model_h6()
    model = models.cnn_model_2()
    model.load_weights(MODEL_NAME)
    return model


"""
dir_path: Directory path of input images
output_file_path: The directory path of output images
This function reads a directory of input images, runs the model and annotates each with class_label and writes them to 
output image directory
"""
def create_image_output(dir_path, output_file_path, user_uuid):
    if len(os.listdir(dir_path)) == 0:
        return

    model = load_model() # Relatively time consuming step, so it is called here instead of annotate function

    for file_name in os.listdir(dir_path):
        if user_uuid not in file_name:
            continue

        full_filename = dir_path + '/' + file_name

        old_image = cv2.imread(full_filename)

        # Resizing image to height 500 while maintaining aspect ratio so that all images are brought to approx same size
        # while displaying on web page (can change height if required)
        image = resize_image_with_aspect_ratio(old_image, window_height=500)

        face_locations = face_recognition.face_locations(image)
        print(face_locations)

        detect_emotion_and_annotate_frame(image, face_locations, model, scale_multiplier=1)

        # Save output image
        cv2.imwrite(output_file_path + '/' + file_name, image)

    print("Output Images created")


def resize_image_with_aspect_ratio(image, window_height = 500):
    aspect_ratio = float(image.shape[1])/float(image.shape[0])
    window_width = window_height/aspect_ratio
    image = cv2.resize(image, (int(window_height), int(window_width)))
    return image


def create_video_output(dir_path, output_file_path, user_uuid):
    if len(os.listdir(dir_path)) == 0:
        return
    
    model = load_model() # Relatively time consuming step, so it is called here instead of annotate function

    for file_name in os.listdir(dir_path):
        if user_uuid not in file_name:
            continue

        full_file_name = dir_path + '/' + file_name

        out_file = output_file_path + '/' + file_name.split('.')[0] + '.webm'

        input_video = cv2.VideoCapture(full_file_name)
        height = input_video.get(cv2.CAP_PROP_FRAME_HEIGHT)
        width = input_video.get(cv2.CAP_PROP_FRAME_WIDTH)

        # Create output_video using 0x00000021 (H264 format) with fixed FPS = 15.0
        # Note: Do not use cv2.Video_fourcc code because it is bugged for H264
        # Also, note that size format is (width, height) and not (height, width)
        
        output_video = cv2.VideoWriter(out_file, cv2.VideoWriter_fourcc(*'VP80'), 10.0, (int(width), int(height)))

        count = 0

        while input_video.isOpened():
            ret, frame = input_video.read()

            if ret is False:
                break

            if count % 3 == 0:          
                # Resizing frame to 1/4th of its size to save time for detecting faces
                small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)

                face_locations = face_recognition.face_locations(small_frame)
                print(face_locations)

                detect_emotion_and_annotate_frame(frame, face_locations, model, scale_multiplier=4) # 1/4 = 0.25

                output_video.write(frame) # Write each frame to output_video

            count += 1

        input_video.release()
        output_video.release()

        print("Output Video created")


def detect_emotion_and_annotate_frame(frame, face_locations, model, scale_multiplier):
    # Display the results
    for (top, right, bottom, left) in face_locations:

        # Multiplying face location by the scale to get corresponding location on the original_frame (for webcam & video)
        top *= scale_multiplier
        right *= scale_multiplier
        bottom *= scale_multiplier
        left *= scale_multiplier

        # Draw a box around the face
        cv2.rectangle(frame, (left, top), (right, bottom), (0, 0, 255), 2)

        # Draw a label with a name below the face
        font = cv2.FONT_HERSHEY_DUPLEX

        # Get class_label result from prediction()
        class_label = prediction(frame[top: bottom, left: right][:, :, ::-1], model)

        cv2.putText(frame, class_label, (left + 6, bottom + 6), font, 1.5, (255, 255, 255), 1, cv2.LINE_AA)


def prediction(image, model):
    # Pre-processing to get image into proper format required for the model
    # Current model requires images in the format:
    # (number of images, height, width, channels) as a grayscale image, so channels = 1
    # So we first resize image to 48x48 then reshape it to (1, 48, 48, 1) because we only have a single image
    img = cv2.resize(image, (48, 48))
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    img = np.reshape(gray, (1, 48, 48, 1))
    predictions = model.predict_classes(img)
    print('Predictions:', class_labels[predictions[0]])
    return class_labels[predictions[0]]