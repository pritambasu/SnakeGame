from keras.models import Sequential
from keras.layers import *
from keras.optimizers import *
import numpy as np

class DQNetwork:
	
	def __init__(self, actions, input_shape, alpha = 0.1, gamma = 0.99, dropout_prob = 0.1, load_path = '', logger=None):
		self.model = Sequential()
		self.actions = actions # Size of the network output
		self.gamma = gamma
		self.alpha = alpha
		self.dropout_prob = dropout_prob

		# Define neural network
		self.model.add(BatchNormalization(axis=1, input_shape=input_shape))
		self.model.add(Convolution2D(32, 2, 2, border_mode='valid', subsample=(2, 2)))
		self.model.add(Activation('relu'))

		self.model.add(BatchNormalization(axis=1))
		self.model.add(Convolution2D(64, 2, 2, border_mode='valid', subsample=(2, 2),  dim_ordering="th"))
		self.model.add(Activation('relu'))

		self.model.add(BatchNormalization(axis=1))
		self.model.add(Convolution2D(64, 3, 3, border_mode='valid', subsample=(2, 2)))
		self.model.add(Activation('relu'))

		self.model.add(BatchNormalization(axis=1))
		self.model.add(Convolution2D(64, 2, 2, border_mode='valid', subsample=(2, 2)))
		self.model.add(Activation('relu'))

		self.model.add(Flatten())

		self.model.add(BatchNormalization(mode=1))
		self.model.add(Dropout(self.dropout_prob))
		self.model.add(Dense(1024))
		self.model.add(Activation('relu'))

		self.model.add(BatchNormalization(mode=1))
		self.model.add(Dropout(self.dropout_prob))
		self.model.add(Dense(512))
		self.model.add(Activation('relu'))

		self.model.add(BatchNormalization(mode=1))
		self.model.add(Dropout(self.dropout_prob))
		self.model.add(Dense(256))
		self.model.add(Activation('relu'))

		self.model.add(Dense(self.actions))

		self.optimizer = Adam()
		self.logger = logger

		# Load the netwrok from saved model
		if load_path != '':
			self.load(load_path)

		self.model.compile(loss = 'mean_squared_error', optimizer = self.optimizer, metrics = ['accuracy'])

	def train(self, batch):
		# Generate the xs and targets for the given batch, train the model on them 
		x_train = []
		t_train = []

		# Generate training set and targets
		for datapoint in batch:
			x_train.append(datapoint['source'])

			# Get the current Q-values for the next state and select the best
			next_state_pred = list(self.predict(datapoint['dest']).squeeze())
			next_a_Q_value = np.max(next_state_pred)

			# Set the target so that error will be 0 on all actions except the one taken
			t = list(self.predict(datapoint['source'])[0])			
			t[datapoint['action']] = (datapoint['reward'] + self.gamma * next_a_Q_value) if not datapoint['final'] else datapoint['reward']
			
			t_train.append(t)

		print next_state_pred # Print a prediction so to have an idea of the Q-values magnitude
		x_train = np.asarray(x_train).squeeze()
		t_train = np.asarray(t_train).squeeze()
		history = self.model.fit(x_train, t_train, batch_size=32, nb_epoch=1)
		self.logger.to_csv('loss_history.csv', history.history['loss'])

	def predict(self, state):
		# Feed state into the model, return predicted Q-values
		return self.model.predict(state, batch_size=1)

	def save(self, filename = None):
		# Save the model and its weights to disk
		print 'Saving...'
		self.model.save_weights(self.logger.path + ('model.h5' if filename is None else filename))

	def load(self, path):
		# Load the model and its weights from path
		print 'Loading...'
		self.model.load_weights(path)
