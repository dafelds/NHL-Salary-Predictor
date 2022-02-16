import pandas as pd
import numpy as np
import keras.metrics
import data_processing_functions
import os

from tensorflow.keras import models
from tensorflow.keras import layers

from sklearn.model_selection import train_test_split

dirname = os.path.dirname(__file__)
filename = os.path.join(dirname, '../../data/full_nhl_player_yearly_stats.csv')

raw = pd.read_csv(filename, index_col=0)
df = data_processing_functions.preprocessing_pipeline(raw)

input_category_numbers = [4] + list(range(15, len(df.columns)))
input_category_numbers

X = df.iloc[:, input_category_numbers].to_numpy()
y = df.iloc[:, 8:15].to_numpy()
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=99)

network = models.Sequential()
network.add(layers.Dense(225, activation='relu', input_shape=(15,)))
network.add(layers.Dense(225, activation='relu'))
network.add(layers.Dense(7, activation='relu'))
network.compile(optimizer='adam',
                loss='mse',
                metrics=[keras.metrics.RootMeanSquaredError()])

network.fit(X_train, y_train, batch_size = 50, epochs = 100)

test_loss, test_acc = network.evaluate(X_test, y_test)
print('test_acc:', test_acc, 'test_loss', test_loss)