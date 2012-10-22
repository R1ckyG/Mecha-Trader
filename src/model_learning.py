#!/usr/bin/env python
import feature_extractor as fe
from sklearn.feature_extraction import DictVectorizer as dv
import numpy as np
from sklearn.grid_search import GridSearchCV as gs
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier, ExtraTreesClassifier
from sklearn.svm import SVC, NuSVC
import sys

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
    data, labels = get_clean_data(ticker)
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

def select_model(model_key):
  model = None
  if model_key == 'b':
    model = GradientBoostingClassifier()
  elif model_key == 'svc':
    model = SVC()
  elif model_key == 'nusvc':
    print 'selecting NuSVC'
    model = NuSVC()
  elif model_key == 'r':
    model = RandomForestClassifier()
  elif model_key == 'e':
    model = ExtraTreesClassifier()
  return model, model_key

def get_hyper_parameters(model_key):
  hyper_parameters = None
  if model_key == 'b':
    hyper_parameters = [{'learn_rate':[.1], 'n_estimators': [800],
                         'max_depth': [6], 'subsample':[1.0], 'max_features': [ 14]}]
  elif model_key == 'svc':
    hyper_parameters = [{'C':[.1, .5, 1], 'kernel':['rbf', 'poly', 'sigmoid'], 'degree':[3, 6, 9]
                         ,'gamma':[0, .01, .1], 'coef0':[0, .01, .1]}]
  elif model_key == 'nusvc':
    hyper_parameters = [{'nu':[.1, .5, 1], 'kernel':['rbf', 'poly', 'sigmoid'], 'degree':[3, 6, 9]
                         ,'gamma':[0, .01, .1], 'coef0':[0, .01, .1]}] 
  elif model_key == 'r':
    hyper_parameters = [{'n_estimators':[10, 100, 200], 'criterion':['gini', 'entropy']
                        ,'n_jobs':[2], 'max_features':['sqrt', 'log2']}]
  elif model_key == 'e':
    hyper_parameters = [{'n_estimators':[10, 100, 200], 'criterion':['gini', 'entropy']
                        ,'n_jobs':[2], 'max_features':['sqrt', 'log2']}]
  return hyper_parameters

def get_best_model_params(model, data, labels, model_type='b'):
  x_train, x_test, y_train, y_test = get_data_sets(data, labels)
  train = dv().fit_transform(x_train)
  test = np.array(y_train)
  hyper_parameters = get_hyper_parameters(model_type)
  clf = gs(model, hyper_parameters)  
  clf.fit(train.todense(), test)
  
  print "Best parameters set found on development set:"
  print
  print clf.best_estimator_
  
  train = dv().fit_transform(x_test)
  test = np.array(y_test)
  #print clf.score(train.todense(), test)
  return clf

if __name__ == '__main__':
  d = l = None
  if len(sys.argv) == 2:
    print 'Ticker file: %s' % sys.argv[1]
    f = open(sys.argv[1])
    out_file = open('output.txt', 'w', buffering=0)
    for line in f:
      ticker = line.strip()
      print '*' * 50, ticker
      d, l = get_clean_data(ticker)
      try:
        c = get_best_model_params(GradientBoostingClassifier(), d, l)
        features, test = get_data(d, l)
        score = c.score(features, test)
        out_file.write("%s, %f\n" % (ticker, score))
        print '*' * 50, 'Score for %s: %f' % (ticker, score)
      except Exception, e:
        print e
        pass
    f.close()
    out_file.close()
  elif len(sys.argv) >= 3:
    print 'Ticker file: %s' % sys.argv
    f = open(sys.argv[1])
    out_file = open('output.txt', 'w')
    ticker_list = []
    for line in f:
      ticker = line.strip()
      print '*' * 50, ticker
      d, l = get_clean_data(ticker)
      try:
        model, mtype = select_model(sys.argv[2])
        c = get_best_model_params(model, d, l, model_type=mtype)
        features, test = get_data(d, l)
        score = c.score(features, test)
        out_file.write("%s, %f\n" % (ticker, score))
        print '*' * 50, 'Score for %s: %f' % (ticker, score)
      except Exception, e:
        print e 
        pass
    f.close()
    out_file.close()
  else:
    d, l = get_clean_data('GOOG')
    c = get_best_model_params(GradientBoostingClassifier(), d, l)
    features, test = get_data(d, l)
    print c.score(features, test)
