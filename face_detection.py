import cv2
import face_recognition
import time
import os
import models
import numpy as np

# Global variables
MODEL_PATH = 'static/model_195.h5'
# Read webcam feed for a frame every half a second
WEBCAM_FRAME_READ_TIME = 0.5 
# Read every third frame from uploaded video
VIDEO_FRAME_READ_RATE = 3 
CLASS_LABELS = {0: 'Anger', 1: 'Disgust', 2: 'Fear', 3: 'Happy', 4: 'Sad', 5: 'Surprise', 6: 'Neutral'}


def load_model():
    model = models.cnn_model_2()
    model.load_weights(MODEL_PATH)
    return model


def create_webcam_output():
    '''
        Not used in current Flask App, but could in the future :P
        Reads local webcam feed and processes a frame every 0.5 seconds (can modify using WEBCAM_FRAME_READ_TIME variable),
        Annotates result and displays it in real-time
    '''
    
    model = load_model()

    video_capture = cv2.VideoCapture(0)
    face_locations = []

    # Start timer
    start_time = time.time()

    while True:
        ret, frame = video_capture.read()

        # Reducing frame to 1/4 of its size. Used for faster execution
        small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
        rgb_small_frame = small_frame[:, :, ::-1]

        # Only process every other frame of video to save time
        # Check if 0.5 sec has passed
        if time.time() - start_time >= WEBCAM_FRAME_READ_TIME: 

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


def create_image_output(input_dir_path, output_dir_path, image_filenames):
    '''
        This function reads a directory of input images, runs the model and annotates each image with class_label and writes them to 
        output image directory

        Parameters:
            input_dir_path: Directory path of input images
            output_dir_path: The directory path of output images
            image_filenames: Filenames of images that have been uploaded by given user with given user_uuid (verified in app.py)
    '''

    # If there's no input images to process (because user only uploaded videos) then stop processing
    if len(os.listdir(input_dir_path)) == 0:
        return

    # Relatively time consuming step, so minimize calls to this as much as possible
    model = load_model() 

    # Iterate through each image in the input directory
    for file_name in image_filenames:

        full_filename = input_dir_path + '/' + file_name

        old_image = cv2.imread(full_filename)

        # Resizing image to height 500 while maintaining aspect ratio so that all images are brought to approx same size
        # while displaying on web page (can change height if required)
        image = resize_image_with_aspect_ratio(old_image, window_height=500)

        face_locations = face_recognition.face_locations(image)

        detect_emotion_and_annotate_frame(image, face_locations, model)

        # Save output image
        cv2.imwrite(output_dir_path + '/' + file_name, image)

    print("Output Images created")


def resize_image_with_aspect_ratio(image, window_height=500):
    '''
        Resizes image to fixed size while maintaining original image's aspect ratio. This is done so that different images with different sizes
        can be displayed on the same webpage in tabular format
    '''
    aspect_ratio = float(image.shape[1])/float(image.shape[0])
    window_width = window_height/aspect_ratio
    image = cv2.resize(image, (int(window_height), int(window_width)))
    return image


def create_video_output(input_dir_path, output_dir_path, video_filenames):
    '''
        This function reads a directory of input videos, runs the model and annotates each frame of each video with class_label and writes them to 
        output video directory.
        The VIDEO_FRAME_READ_RATE global variable determines how often a video's frame will be read for processing (annotation). This is done to save
        time on the overall processing as reading each frame is redundant
        According to current setting, every third frame of the video will be read for processing.

        Parameters:
            input_dir_path: Directory path of input video
            output_dir_path: The directory path of output video
            video_filenames: Filenames of videos that have been uploaded by given user with given user_uuid (verified in app.py)
    '''

    # If there's no input videos to process (because user only uploaded images) then stop processing
    if len(os.listdir(input_dir_path)) == 0:
        return
    
    # Relatively time consuming step, so minimize calls to this as much as possible
    model = load_model()

    # Iterate through each video in the input directory
    for file_name in video_filenames:

        full_file_name = input_dir_path + '/' + file_name

        out_file = output_dir_path + '/' + file_name.split('.')[0] + '.webm'

        input_video = cv2.VideoCapture(full_file_name)
        height = input_video.get(cv2.CAP_PROP_FRAME_HEIGHT)
        width = input_video.get(cv2.CAP_PROP_FRAME_WIDTH)

        # Create output_video using VP8 Format which creates .webm video and with fixed FPS = 10.0
        # Also, note that size format is (width, height) and not (height, width)
        
        output_video = cv2.VideoWriter(out_file, cv2.VideoWriter_fourcc(*'VP80'), 10.0, (int(width), int(height)))

        count = 0

        while input_video.isOpened():
            ret, frame = input_video.read()

            if ret is False:
                break
            
            # Read every third frame
            if count % VIDEO_FRAME_READ_RATE == 0:        

                # Resizing frame to 1/4th of its size to save time for detecting faces
                small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)

                face_locations = face_recognition.face_locations(small_frame)

                # Scale multiplier = 4 since 1/4 = 0.25
                # so we can obtain the actual face locations on the original frame by multiplying face_locations by 4
                detect_emotion_and_annotate_frame(frame, face_locations, model, scale_multiplier=4) 

                output_video.write(frame) # Write each frame to output_video

            count += 1

        input_video.release()
        output_video.release()

        print("Output Video created")


def prediction(image, model):
    ''' 
        This function runs the specified model on the given image to obtain the predicted emotion
        Pre-processing needs to be done to get the image into the format that is accepted by the model
        
        Current model requires images/frames in the format:
            (number_of_images, height, width, channels) as a grayscale image, so channels = 1

        So we first resize image to 48x48 then reshape it to (1, 48, 48, 1) because we only have a single image

        Parameters:
            image: Image to predict on
            model: Model that will run the prediction
    '''

    img = cv2.resize(image, (48, 48))
    
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    img = np.reshape(gray, (1, 48, 48, 1))
    
    predictions = model.predict_classes(img)
    print('Predictions:', CLASS_LABELS[predictions[0]])
    
    return CLASS_LABELS[predictions[0]]


def detect_emotion_and_annotate_frame(frame, face_locations, model, scale_multiplier=1):
    '''
        This function draws a rectangle/s on the face location/s
        Then it runs the model on the face location to obtain emotion prediction
        It then adds text representing the emotion predicted on the image a few pixels off of the bottom line of the corresponding rectangles

        Parameters:
            frame: Input video frame or image
            face_locations: List of face locations in the frame obtained by running the corresponding face_recognition module function on the frame
            model: Model that will be run on the frame for obtaining predicted emotion

            scale_multiplier: If the original frame was downscaled to obtain face_locations (for saving processing time) 
            then multiplying the face_locations by the downscaled multiplier can be done to obtain the actual face_locations on the original frame
            (see create_video_output function to see this logic in action)
    '''

    # For each face detected in the frame
    for (top, right, bottom, left) in face_locations:

        # Multiplying face location by the scale to get corresponding location on the original_frame (for webcam & video)
        top *= scale_multiplier
        right *= scale_multiplier
        bottom *= scale_multiplier
        left *= scale_multiplier

        # Draw a box around the face
        cv2.rectangle(frame, (left, top), (right, bottom), (0, 0, 255), 2)

        font = cv2.FONT_HERSHEY_DUPLEX

        # Get class_label result from prediction()
        class_label = prediction(frame[top: bottom, left: right][:, :, ::-1], model)

        # Draw a label with a name below the face
        cv2.putText(frame, class_label, (left + 6, bottom + 6), font, 1.5, (255, 255, 255), 1, cv2.LINE_AA)


