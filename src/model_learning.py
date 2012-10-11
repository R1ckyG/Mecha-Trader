#!/usr/bin/env python
import feature_extractor as fe
from sklearn.feature_extraction import DictVectorizer as dv
import numpy as np
from sklearn.grid_search import GridSearchCV as gs
from sklearn.ensemble import GradientBoostingClassifier as gc

def get_clean_data(ticker):
  clean_data = list()
  data = fe.get_features(ticker)
  labels = list()
  for d in data:
    d.pop('date')
    d.pop('_id')
    labels.append(d.pop('bxret'))
    clean_data.append(d)
  return clean_data[31:], labels[31:]

def get_data_for_multiple(tickers):
  clean_data = list()
  clean_labels = list()
  for ticker in tickers:
    data, labels = fe.get_clean_data(ticker)
    clean_data.extend(data)
    clean_labels.extend(labels)
  return clean_data, clean_lables

def get_data_sets(data, labels):
  data_length = len(data)
  partition_index = int(data_length *.75)
  print 'Length of training set: %d\nLength of test set: %d' \
      % (partition_index, data_length - partition_index)
  return data[:partition_index], data[partition_index:], labels[:partition_index], labels[partition_index:]


def get_data(data, labels):
  x_train, x_test, y_train, y_test = get_data_sets(data, labels)
  train = dv().fit_transform(x_test)
  test = np.array(y_test)
  
  return train.todense(), test

def get_best_model_params(model, data, labels):
  x_train, x_test, y_train, y_test = get_data_sets(data, labels)
  train = dv().fit_transform(x_train)
  test = np.array(y_train)
  hyper_parameters = [{'learn_rate':[.1], 'n_estimators': [800],
                       'max_depth': [6], 'subsample':[1.0], 'max_features': [ 14]}]
  clf = gs(model, hyper_parameters)  
  clf.fit(train.todense(), test)
  
  print "Best parameters set found on development set:"
  print
  print clf.best_estimator_
  
  #for params, mean_score, scores in clf.grid_scores_:
  #  print "%0.3f (+/-%0.03f) for %r" % (mean_score, scores.std() / 2, params)
    
  train = dv().fit_transform(x_test)
  test = np.array(y_test)
  #print clf.score(train.todense(), test)
  return clf

if __name__ == '__main__':
  d = l = None
  if len(sys.argv) > 2:
    d, l = get_clean_dats(sys.argv[1])
  else:
    d, l = get_clean_data('YHOO')
    c = get_best_model_params(gc(), d, l)
    features, test = get_data(d, l)
    print c.score(features, test)
