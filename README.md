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
All requirements are present in the requirements.txt file and note that certain libraries like Tensorflow were downgraded to older versions so as to reduce the slug size for Heroku Deployment.

Update: The older version on Heroku used to crash with the timeout error if large enough videos were uploaded for processing. So to overcome this error, Redis Task Queue was integrated with the app which now handles all the background tasks, to learn more about this implementation you can check out <a href="https://james-jasvin.medium.com/fix-the-30-second-timeout-error-on-heroku-25755ffbca95?source=friends_link&sk=203e21eaafbd5d05c731234b0d9d7077">this article</a> I wrote on how to integrate Redis Task Queues into your Flask web-app.
