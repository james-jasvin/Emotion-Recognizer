import tensorflow as tf
from tensorflow.keras.layers import Conv2D, MaxPooling2D, AveragePooling2D, Flatten, Dense, Dropout, BatchNormalization
from tensorflow.keras.regularizers import l1, l2, l1_l2


# Creating and training the model for images of dimensions 48 * 48 with 3 channels
def model1():
    m1 = tf.keras.models.Sequential([
        tf.keras.layers.Conv2D(16, (3, 3), activation='relu', input_shape=(256,256,3)),
        tf.keras.layers.MaxPooling2D(2,2),
        tf.keras.layers.Conv2D(32, (3, 3), activation='relu'),
        tf.keras.layers.MaxPooling2D(2, 2),
        tf.keras.layers.Conv2D(64, (3, 3), activation='relu'),
        tf.keras.layers.MaxPooling2D(2, 2),
        # tf.keras.layers.Conv2D(128, (3, 3), activation='relu'),
        tf.keras.layers.MaxPooling2D(2, 2),
        tf.keras.layers.Flatten(),
        tf.keras.layers.Dense(512,activation='relu'),
        tf.keras.layers.Dense(6, activation='softmax')

    ])
    # print(m1.summary())

    return m1


# ck-data
def model_h5():
    model = tf.keras.models.Sequential([
        tf.keras.layers.Conv2D(32, (3,3), activation='relu', input_shape=(48, 48, 3)),
        tf.keras.layers.MaxPooling2D(2, 2),
        tf.keras.layers.Conv2D(64, (3,3), activation='relu'),
        # tf.keras.layers.MaxPooling2D(2,2),
        tf.keras.layers.Conv2D(128, (3,3), activation='relu'),
        tf.keras.layers.MaxPooling2D(2,2),
        tf.keras.layers.Conv2D(256, (3,3), activation='relu'),
        tf.keras.layers.MaxPooling2D(2,2),
        # tf.keras.layers.Conv2D(256, (3, 3), activation='relu'),
        # tf.keras.layers.AveragePooling2D(2, 2),
        tf.keras.layers.Dropout(0.5),
        tf.keras.layers.Flatten(),
        tf.keras.layers.Dense(512, activation='relu'),
        tf.keras.layers.Dense(7, activation='softmax')
    ])
    return model

def model_h6():
    model = tf.keras.models.Sequential([
        tf.keras.layers.Conv2D(32, (3, 3), activation='relu', input_shape=(48, 48, 3)),
        tf.keras.layers.MaxPooling2D(2, 2),
        tf.keras.layers.Conv2D(64, (3, 3), activation='relu'),
        tf.keras.layers.Dropout(0.5),
        # tf.keras.layers.MaxPooling2D(2,2),
        tf.keras.layers.Conv2D(128, (3, 3), activation='relu'),
        tf.keras.layers.MaxPooling2D(2, 2),
        tf.keras.layers.Conv2D(256, (3, 3), activation='relu'),
        # tf.keras.layers.MaxPooling2D(2,2),
        tf.keras.layers.Conv2D(256, (3, 3), activation='relu'),
        # tf.keras.layers.AveragePooling2D(2, 2),
        tf.keras.layers.Dropout(0.5),
        tf.keras.layers.Flatten(),
        tf.keras.layers.Dense(2048, activation='relu'),
        tf.keras.layers.Dense(512, activation='relu'),
        tf.keras.layers.Dense(6, activation='softmax')
    ])
    return model


def model_h8():
    model = tf.keras.models.Sequential([
        tf.keras.layers.Conv2D(32, (3,3), activation='relu', input_shape=(48, 48, 3)),
        tf.keras.layers.MaxPooling2D(2, 2),
        tf.keras.layers.Conv2D(64, (3,3), activation='relu'),
        tf.keras.layers.Dropout(0.5),
        tf.keras.layers.MaxPooling2D(2,2),
        tf.keras.layers.Conv2D(128, (3,3), activation='relu', padding='same'),
        tf.keras.layers.MaxPooling2D(2,2),
        tf.keras.layers.Conv2D(256, (3,3), activation='relu'),
        # tf.keras.layers.MaxPooling2D(2,2),
        tf.keras.layers.Conv2D(512, (3, 3), activation='relu'),
        # tf.keras.layers.AveragePooling2D(2, 2),
        tf.keras.layers.Dropout(0.5),
        tf.keras.layers.Flatten(),
        tf.keras.layers.Dense(1024, activation='relu'),
        tf.keras.layers.Dense(512, activation='relu'),
        tf.keras.layers.Dense(6, activation='softmax')
    ])
    return model


def model_h9():
    model = tf.keras.models.Sequential([
        tf.keras.layers.Conv2D(32, (3, 3), activation='relu', input_shape=(48, 48, 3)),
        tf.keras.layers.MaxPooling2D(2, 2),
        tf.keras.layers.Conv2D(64, (3, 3), activation='relu'),
        tf.keras.layers.Dropout(0.5),
        tf.keras.layers.MaxPooling2D(2, 2),
        tf.keras.layers.Conv2D(128, (3, 3), activation='relu', padding='same'),
        tf.keras.layers.MaxPooling2D(2, 2),
        tf.keras.layers.Conv2D(256, (3, 3), activation='relu'),
        # tf.keras.layers.MaxPooling2D(2,2),
        # tf.keras.layers.Conv2D(512, (3, 3), activation='relu'),
        # tf.keras.layers.AveragePooling2D(2, 2),
        tf.keras.layers.Dropout(0.5),
        tf.keras.layers.Flatten(),
        tf.keras.layers.Dense(1024, activation='relu'),
        tf.keras.layers.Dense(512, activation='relu'),
        tf.keras.layers.Dense(6, activation='softmax')
    ])
    return model

def cnn_model_2():
    classes = 7
    input_shape = (48, 48, 1)
    m1 = tf.keras.models.Sequential([
        Conv2D(8, (3, 3), activation='relu', input_shape=input_shape),
        BatchNormalization(),
        # 46 46 8

        Conv2D(16, (3, 3), activation='relu', padding='same'),
        # 46 46 16
        Dropout(0.25),
        Conv2D(16, (3, 3), activation='relu'),
        # 44 44 32
        BatchNormalization(),

        Conv2D(32, (3, 3), activation='relu', padding='same'),
        # 44 44 64
        Dropout(0.25),
        Conv2D(32, (5, 5), activation='relu'),
        # 40 40 32
        MaxPooling2D(2, 2),
        # 20 20 32
        BatchNormalization(),

        Conv2D(32, (3, 3), activation='relu', padding='same'),
        # 20 20 64
        Dropout(0.3),
        Conv2D(64, (3, 3), activation='relu'),
        # 18 18 64
        BatchNormalization(),

        Conv2D(128, (3, 3), activation='relu', padding='same'),
        # 18 18 128
        Dropout(0.25),
        Conv2D(128, (3, 3), activation='relu'),
        # 16 16 128
        MaxPooling2D(2, 2),
        # 8 8 128
        BatchNormalization(),

        Conv2D(256, (3, 3), activation='relu', padding='same'),
        # 8 8 256
        Dropout(0.35),
        Conv2D(256, (3, 3), activation='relu'),
        # 6 6 256
        AveragePooling2D(2, 2),
        # 3 3 256
        BatchNormalization(),

        Flatten(),
        Dense(1024, activation='relu'),
        Dense(512, activation='relu'),
        Dense(128, activation='relu'),
        Dense(classes, activation='softmax')

    ])
    # print(m1.summary())
    return m1