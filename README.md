# Emotion-Recognizer-420
Its a bit slow but I've got the web-app hosted here: https://emotion-recognizer-420.herokuapp.com/
<br> Definitely not copying what @esoteriikos did :P

# What It Does?
Provide a set of images or videos as input and get output image or video annotated with the predicted emotions.

Emotion Labels supported: Anger, Sad, Happy, Neutral, Disgust, Fear, Surprise but some of these labels are quite unlikely to appear because of the large discrepancies in number of training images, this is something that can definitely be improved upon.

# Dataset
Download the dataset from <a href="https://www.kaggle.com/c/challenges-in-representation-learning-facial-expression-recognition-challenge/data">here</a>

# Background & Requirements
Model was trained using Tensorflow and the dataset mentioned above and the Web-App was made using Flask.
All requirements are present in the requirements.txt file (there's probably some unnecessary libraries in there as well, literally just did pip freeze on the virtual environment for this project and this is what I got) and note that certain libraries like Tensorflow were downgraded to older versions so as to reduce the slug size for Heroku Deployment.
