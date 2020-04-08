from flask import Flask, request, render_template, redirect, url_for, session
import os
from werkzeug.utils import secure_filename
from flask import send_from_directory
from face_detection import create_image_output, create_video_output
from flask_dropzone import Dropzone
import shutil
import uuid

app = Flask(__name__)
# app.secret_key = os.urandom(24)
app.secret_key = os.environ['SECRET_KEY']

# Set the upload folder for whatever we upload
APP_ROOT = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(APP_ROOT, 'static/uploads/')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Set input and output image and video absolute paths
images_input_folder_path = app.config['UPLOAD_FOLDER'] + 'images/input_images/'
images_output_folder_path = app.config['UPLOAD_FOLDER'] + 'images/output_images/'
videos_input_folder_path = app.config['UPLOAD_FOLDER'] + 'videos/input_videos/'
videos_output_folder_path = app.config['UPLOAD_FOLDER'] + 'videos/output_videos/'

# Configure dropzone
app.config['DROPZONE_UPLOAD_MULTIPLE'] = True
app.config['DROPZONE_ALLOWED_FILE_CUSTOM'] = True
app.config['DROPZONE_ALLOWED_FILE_TYPE'] = '.jpg, .png, .bmp, .jpeg, .mp4, .avi, .wmv, .flv, .mpeg'
app.config['DROPZONE_MAX_FILE_SIZE'] = 100
app.config['DROPZONE_MAX_FILE'] = 50

# Set of extensions allowed
IMAGE_EXTENSIONS = {'bmp', 'jpg', 'png', 'jpeg', 'jpe'}
VIDEO_EXTENSIONS = {'mp4', 'avi', 'wmv', 'flv', 'mpeg'}

# Create a Dropzone (will be accessed in the HTML code)
dropzone = Dropzone(app)

@app.route('/')
@app.route('/<error>')
def home(error=None):
	# global user_uuid
	session['user_uuid'] = str(uuid.uuid4().hex)
	return render_template('home.html', error=error)


# Check if filename is an allowed_image or an allowed_video
def allowed_image(filename):
	return '.' in filename and filename.split('.')[-1].lower() in IMAGE_EXTENSIONS


def allowed_video(filename):
	return '.' in filename and filename.split('.')[-1].lower() in VIDEO_EXTENSIONS


@app.route('/uploads', methods=['GET', 'POST'])
def upload_file():
	if request.method == 'POST':
		file_object = request.files
		
		for f in file_object:
			file = request.files.get(f)

			# General good practice of security while using filenames of user uploaded files
			# https://flask.palletsprojects.com/en/1.1.x/quickstart/#file-uploads
			print(session)
			if 'user_uuid' in session: 
				user_uuid = session['user_uuid']
				file_uuid = str(uuid.uuid4().hex)[:5]
				# filename = secure_filename(file.filename)
				filename = user_uuid + file_uuid + '.' + file.filename.split('.')[-1]

				# If file is an allowed image or video then save it in their respective input folder
				if allowed_image(filename):
					file.save(os.path.join(images_input_folder_path, filename))

				if allowed_video(filename):
					file.save(os.path.join(videos_input_folder_path, filename))

		return "UPLOADING"

	# If it wasn't a POST request then just redirect to the home page
	return redirect(url_for('home'))


# This route is triggered when "Display Results button is clicked on the home page
@app.route('/results')
def results():

	# Whenever uploads are to be processed, clear the image and video output folders, in order to prevent previous
	# outputs from being processed
	# delete_directory_files(images_output_folder_path)
	user_uuid = session['user_uuid']

	create_image_output(dir_path=images_input_folder_path, output_file_path=images_output_folder_path, user_uuid=user_uuid)

	# Delete the images and videos input folders, in order to prevent it being processed for next request
	# delete_directory_files(images_input_folder_path)

	output_images = []
	output_videos = []

	for filename in os.listdir(images_output_folder_path):
		if user_uuid in filename:
			output_images.append(filename)
	
	# output_images = os.listdir(images_output_folder_path)

	# Repeat the same with videos as well
	# delete_directory_files(videos_output_folder_path)
	create_video_output(dir_path=videos_input_folder_path, output_file_path=videos_output_folder_path, user_uuid=user_uuid)
	# delete_directory_files(videos_input_folder_path)

	for filename in os.listdir(videos_output_folder_path):
		if user_uuid in filename:
			output_videos.append(filename)

	# output_videos = os.listdir(videos_output_folder_path)

	# If no images and videos were uploaded to the dropzone, then both these lists would be empty
	# In this case, redirect to home page and display Error Message
	if len(output_images) == 0 and len(output_videos) == 0:
		return redirect(url_for('home', error="NO FILE UPLOADED"))
	
	# Render the results page
	return render_template('results.html', output_images=output_images, output_videos=output_videos)


# Delete all files in given directory path
def delete_directory_files(dir_path):
	for filename in os.listdir(dir_path):
		file_path = os.path.join(dir_path, filename)
		try:
			shutil.rmtree(file_path)
		except OSError:
			os.remove(file_path)


# This route is to send images to UI after resizing it properly (which cannot be done on the front-end side)
@app.route('/results/<file_type>/<file_name>')
def send_file(file_type, file_name):
	if file_type == "image":
		return send_from_directory(images_output_folder_path, file_name)
	if file_type == "video":
		return send_from_directory(videos_output_folder_path, file_name)


if __name__ == "__main__":
	app.run(debug=True)
