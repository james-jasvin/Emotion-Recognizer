#TODO:
#Fully debug Session variables

from flask import Flask, request, render_template, redirect, url_for, session, jsonify, send_from_directory
import os
from face_detection import create_image_output, create_video_output
from flask_dropzone import Dropzone
import uuid

from rq import Queue
from rq.job import Job
from worker import conn

app = Flask(__name__)
app.secret_key = os.urandom(24)

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

# Check if filename is an allowed_image or an allowed_video
def allowed_image(filename):
	return '.' in filename and filename.split('.')[-1].lower() in IMAGE_EXTENSIONS

def allowed_video(filename):
	return '.' in filename and filename.split('.')[-1].lower() in VIDEO_EXTENSIONS


@app.route('/')
@app.route('/home')
@app.route('/<error>')
@app.route('/home/<error>')
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

	return render_template('home.html', error=error)


@app.route('/uploads', methods=['POST'])
def upload_file():
	'''
		Flask Dropzone upload route
		When a file is dropped on the Dropzone, that file will be processed by this route asynchronously
		Steps done by the route,
		Generates unique filename, checks whether file format is allowed or not and then saves file in the correct input folder
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
		It uses user_uuid to parse the input directories and identify which are the user uploaded files
		If no files were uploaded by user then just redirect to home
		If files were uploaded then start the Redis job, store filenames in the session dictionary
		and return the job_id back to the client.
	'''
	response_object = {
		"status": "fail",
		"error_code": "102"
	}

	print(session)

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
			response_object['error_code'] = 101
			return jsonify(response_object), 302
		
		# Enqueue the prediction job on the Redis Task Queue
		# The result_ttl=5000 line argument tells RQ how long to hold on to the result of the job for, 
		# 5,000 seconds in this case. 
		job = queue.enqueue_call(
			func='app.create_output', 
			args=(image_filenames, video_filenames),
			result_ttl=5000)

		# Store the image and video filename lists in the session dictionary
		# This is because the output files will also have the same names and these lists can be 
		# accessed once the Redis job finishes processing and then be rendered on the results page
		session['image_filenames'] = image_filenames
		session['video_filenames'] = video_filenames

		print(job.get_id())

		response_object = {
			"status": "success",
			"job_id": job.get_id()
		}

		# Respond to request by Client with success code indicating that job has started
		return jsonify(response_object), 202

	return jsonify(response_object), 302


@app.route('/jobs/<job_key>', methods=['GET'])
def get_results(job_key):
	'''
		Route that returns job status of given job to the requesting Client. Used for polling the submitted job by the Client
		
		Parameters:
			job_key (str): The job id of the job to return status for
			
		Returns:
			response_object (JSON): If job exists then status is success, else status is error
			If job exists, then job status can be fetched using response_object['data']['job_status']
			The result of the job can be fetched for a completed job using,
			response_object['data']['job_result']
	'''
	job = Job.fetch(job_key, connection=conn)
	
	# If job exists then return job id and status along with result
	# But result will only be present if job has actually finished
	# So this logic checking will be done by the poller function at client-side
	if job:
		response_object = {
			"status": "success",
			"data": {
				"job_id": job.get_id(),
				"job_status": job.get_status(),
				"job_result": job.result,
			},
		}
	else:
		response_object = {"status": "error"}

	return jsonify(response_object)


@app.route('/results', methods=['GET'])
def results():
	'''
		This route will render the results.html template
		It takes the list of output image and video filenames as parameters
		This is why they were stored in the session dictionary in the jobs route
	'''
	return render_template('results.html', output_images=session['image_filenames'], output_videos=session['video_filenames'])


@app.route('/results/<file_type>/<file_name>')
def send_file(file_type, file_name):
	'''
		This route is to send images and videos to UI after resizing it properly (which cannot be done on the front-end side)

		Parameters:
		file_type: Indicates whether file is "image" or "video"
		file_name: Unique name of file, same for input as well as output files
	'''
	if file_type == "image":
		return send_from_directory(IMAGES_OUTPUT_FOLDER_PATH, file_name)

	# For videos, remove extension and append webm as the final extension because we convert all videos to webm format
	if file_type == "video":
		webm_file_name = file_name.split('.')[0] + '.webm'
		return send_from_directory(VIDEOS_OUTPUT_FOLDER_PATH, webm_file_name)


def create_output(image_filenames, video_filenames):
	'''
		Wrapper function that executes both image and video output prediction functions
		This is done so that both tasks can be wrapped into the same Redis Job which helps avoid timing issues
		and besides it is only the Video input that will actually cause delay in web-app functioning, so it doesn't make much sense
		to create a second job only for processing Image input

		Parameters:
		image_filenames: List of input image filenames, same filenames are used for output images
		video_filenames: Same but for input videos
	'''

	# Process the input images and/or videos and save them to the respective output folders
	create_image_output(IMAGES_INPUT_FOLDER_PATH, IMAGES_OUTPUT_FOLDER_PATH, image_filenames)
	create_video_output(VIDEOS_INPUT_FOLDER_PATH, VIDEOS_OUTPUT_FOLDER_PATH, video_filenames)

	# Job result JSON
	# This will be sent to the client once the Redis job finishes
	# Contains the image and video filenames as parameters which are redundant at this point because they are used in the session dictionary anyways
	# But I'm keeping it here in case the session method has some flaws down the line
	response_object = {
		"status": "success",
		"image_filenames": image_filenames,
		"video_filenames": video_filenames
	}

	return response_object


if __name__ == "__main__":
	app.run()
