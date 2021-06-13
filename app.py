#TODO:
# Output videos are saved as webm, so while sending video_filenames list to results page, ensure that all video filenames either have no extension
# or by default check for webm extension

# After polling is complete, the job result will contain video and image filenames list
# This has to be passed to Flask in order to render 
# https://stackoverflow.com/questions/54848244/passing-flask-list-to-html
# It could be possible that using session variables to store both the lists is the most optimal technique as you can now avoid
# making the URL look extra bulky

from flask import Flask, request, render_template, redirect, url_for, session, jsonify, send_from_directory
import os
from face_detection import create_image_output, create_video_output
from flask_dropzone import Dropzone
import shutil
import uuid

from rq import Queue
from rq.job import Job
from worker import conn

app = Flask(__name__)
app.secret_key = os.environ['SECRET_KEY']

# Redis Task Queue that will handle all jobs
queue = Queue(connection=conn)

# Set the upload folder for whatever we upload
APP_ROOT = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(APP_ROOT, 'static/uploads/')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Set input and output image and video absolute paths
IMAGES_INPUT_FOLDER_PATH = app.config['UPLOAD_FOLDER'] + 'images/input_images/'
IMAGES_OUTPUT_FOLDER_PATH = app.config['UPLOAD_FOLDER'] + 'images/output_images/'
VIDEOS_INPUT_FOLDER_PATH = app.config['UPLOAD_FOLDER'] + 'videos/input_videos/'
VIDEOS_OUTPUT_FOLDER_PATH = app.config['UPLOAD_FOLDER'] + 'videos/output_videos/'

# Configure dropzone
app.config['DROPZONE_UPLOAD_MULTIPLE'] = True
app.config['DROPZONE_ALLOWED_FILE_CUSTOM'] = True
app.config['DROPZONE_ALLOWED_FILE_TYPE'] = '.jpg, .png, .bmp, .jpeg, .mp4, .avi, .wmv, .flv, .mpeg'
app.config['DROPZONE_MAX_FILE_SIZE'] = 20 # 20 MB
app.config['DROPZONE_MAX_FILE'] = 50

# Set of extensions allowed
IMAGE_EXTENSIONS = {'bmp', 'jpg', 'png', 'jpeg', 'jpe'}
VIDEO_EXTENSIONS = {'mp4', 'avi', 'wmv', 'flv', 'mpeg'}

# Create a Dropzone (will be accessed in the HTML code)
dropzone = Dropzone(app)

@app.route('/')
@app.route('/home')
@app.route('/<error>')
def home(error=None):
	'''
		Route that is triggered when user reaches home page. 
		It is also reached when user form submission triggers a server-side error
		in which case the user will be redirected to home page with the appropriate error code.
		Whenever user enters home page for the first time, the session information is updated with a user UUID in order 
		to distinguish user's file uploads from other user's file uploads
	'''

	if 'user_uuid' not in session:
		# global uuid for user
		session['user_uuid'] = str(uuid.uuid4().hex)


	if error == 101:
		error = "NO FILE UPLOADED"

	return render_template('home.html', error=error)


# Check if filename is an allowed_image or an allowed_video
def allowed_image(filename):
	return '.' in filename and filename.split('.')[-1].lower() in IMAGE_EXTENSIONS


def allowed_video(filename):
	return '.' in filename and filename.split('.')[-1].lower() in VIDEO_EXTENSIONS


@app.route('/uploads', methods=['POST'])
def upload_file():
	'''
		Flask Dropzone upload route
		Write stuff
	'''
	file_object = request.files
	
	for f in file_object:
		file = request.files.get(f)
		
		if 'user_uuid' in session: 
			# Generate unique filename for the uploaded file (image or video) using the following format:
			# user_uuid + first 5 characters of file_uuid + extension format
			user_uuid = session['user_uuid']
			file_uuid = str(uuid.uuid4().hex)[:5]
			filename = user_uuid + file_uuid + '.' + file.filename.split('.')[-1]

			# If file is an allowed image or video then save it in their respective input folder
			if allowed_image(filename):
				file.save(os.path.join(IMAGES_INPUT_FOLDER_PATH, filename))

			elif allowed_video(filename):
				file.save(os.path.join(VIDEOS_INPUT_FOLDER_PATH, filename))

			else:
				# If file format is not supported, then return with an error message with a 4xx status code
				# This error will be displayed on the Flask Dropzone by default
				# "Unsupported File Format" = Error message
				# 415 = "Unsupport Media Type" error code
				return "Unsupported File Format", 415

	return "UPLOADING", 200


@app.route('/jobs', methods=['POST'])
def jobs():
	'''
		This route is triggered when "Display Results" button is clicked on the home page
		

	'''
	response_object = {
		'status': "fail",
		"error_code": ""
	}


	# Check whether user has visited home page first to get user_uuid before coming to results
	if 'user_uuid' in session:
		user_uuid = session['user_uuid']

		# Checking for whether user has uploaded any image or video file
		image_filenames = []
		video_filenames = []

		# Collect all the output filenames in their respective lists
		for filename in os.listdir(IMAGES_INPUT_FOLDER_PATH):
			if user_uuid in filename:
				image_filenames.append(filename)
		
		for filename in os.listdir(VIDEOS_INPUT_FOLDER_PATH):
			if user_uuid in filename:
				video_filenames.append(filename)

		# If no images and videos were uploaded to the dropzone, then both these lists would be empty
		# In this case, redirect to home page and display Error Message
		if len(image_filenames) == 0 and len(video_filenames) == 0:
			return redirect(url_for('home', error="101"))
		
		# Enqueue the prediction job on the Redis Task Queue
		# The result_ttl=5000 line argument tells RQ how long to hold on to the result of the job for, 
		# 5,000 seconds in this case. 
		job = queue.enqueue_call(
			func='app.create_output', 
			args=(image_filenames, video_filenames),
			result_ttl=5000)

		print(job.get_id())

		response_object = {
			"status": "success",
			"job_id": job.get_id()
		}

		# Respond to request by Client with success code indicating that job has started
		return jsonify(response_object), 202


		# Render the results page
		# return render_template('results.html', output_images=image_filenames, output_videos=video_filenames)

	return jsonify(response_object), 302

# This route will render the results.html template
# Temporary solution is using the session variables to obtain filename lists.
@app.route('/results', methods=['GET'])
def results():
	pass

def create_output(image_filenames, video_filenames):
	'''
		Wrapper function that executes both image and video output prediction functions
		This is done so that both tasks can be wrapped into the same Redis Job which helps avoid timing issues
		and besides it is only the Video input that will actually cause delay in web-app functioning, so it doesn't make much sense
		to create a second job only for processing Image input
	'''

	# Process the input images and/or videos and save them to the respective output folders
	create_image_output(IMAGES_INPUT_FOLDER_PATH, IMAGES_OUTPUT_FOLDER_PATH, image_filenames)
	create_video_output(VIDEOS_INPUT_FOLDER_PATH, VIDEOS_OUTPUT_FOLDER_PATH, video_filenames)

	# WRITE RESPONSE_OBJECT HERE
	# PERHAPS ADD BOTH LISTS TO SESSION DICT AT THIS POINT
	# response_object should contain, success, user_uuid, both filename lists


@app.route('/results/<file_type>/<file_name>')
def send_file(file_type, file_name):
	'''
		This route is to send images and videos to UI after resizing it properly (which cannot be done on the front-end side)
	'''
	if file_type == "image":
		return send_from_directory(IMAGES_OUTPUT_FOLDER_PATH, file_name)

	# IMPORTANT
	# For videos, remove extension and append webm as the final extension
	if file_type == "video":
		return send_from_directory(VIDEOS_OUTPUT_FOLDER_PATH, file_name)


if __name__ == "__main__":
	app.run()
