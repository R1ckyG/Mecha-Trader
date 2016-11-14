#!/usr/bin/env python
from data import feature_extractor as fe
from sklearn.feature_extraction import DictVectorizer as dv
import numpy as np
from sklearn.grid_search import GridSearchCV as gs
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier, ExtraTreesClassifier
from sklearn.svm import SVC, NuSVC
from sklearn.neighbors import KNeighborsClassifier
from sklearn.mixture import DPGMM
from sklearn.metrics import classification_report, confusion_matrix, average_precision_score
import sklearn.preprocessing as pw
import sklearn.feature_selection as fs
from lib import talib
import sys, math, cPickle, copy, pdb

def prep_training_data(data, label='label', fields_to_remove=[]):
  clean_data = list()
  labels = list()
  
  for da in data:
    d = copy.copy(da)
    for field in fields_to_remove:
      if field in d: d.pop(field)
        
    if data_valid(d):
      labels.append(d.pop(label))
      clean_data.append(d)
  return clean_data, labels

def get_model(model_type, features, labels, grid_search=True, train_test_cutoff=.75):
  model, mtype = select_model(model_type)
  if grid_search:
    c = get_best_model_params(model, features, labels, model_type=mtype, train_test_cutoff=train_test_cutoff)
    return c
  return model
  
def run_model(model, features, labels, train_test_cutoff=.75):
  if isinstance(model, GradientBoostingClassifier):
    predictions = model.score(features)
    score = predictions
    probablities = model.predict_proba(features)
  else:
    score = model.score(features, labels)
    predictions = model.predict(features)
    probablities = model.predict_proba(features)
  return predictions, score, probablities

def evaluate_model(exp_name, model, labels, predictions, scores, probabilities):
  outfile = open('%s_exp_output.txt' % exp_name, 'w', buffering=0)
  
  msg = '-' * 35 + exp_name +'-' * 35 + '\n'
  msg = msg + 'Score: %r' % scores + '\n\n'
  
  cr = classification_report(labels.tolist(), predictions) 
  cm = confusion_matrix(labels, predictions)
  msg = msg + '%s' % cr + '\n\n\n'
  msg = msg + '%s' % cm
  
  print msg
  outfile.write(msg)
  with open('%s.pkl' % (exp_name), 'wb') as fid:
            cPickle.dump(model, fid)
  
  results = {}
  results['cm'] = cm
  results['cr'] = cr
  results['predictions'] = predictions
  results['labels'] = labels
  results['scores'] = scores
  results['probabilities'] = probabilities
  
  return results

def run_experiment(exp_name, model_type, data, label='label', fields_to_remove=[],\
    feature_extracor=prep_training_data, model_selector=get_model,\
    model_runner=run_model, evaluator=evaluate_model, grid_search=True, train_test_cutoff=.75):
  
  print "Preparing training data and model for expermient %s" % exp_name
  features, labels = prep_training_data(data, label, fields_to_remove)
  model = model_selector(model_type, features, labels, grid_search, train_test_cutoff=.75)
  
  print "Evaluating model for experiment %s" % exp_name
  test_features, test_labels = get_data(features, labels, train_test_cutoff)
  predictions, scores, probabilities = model_runner(model, test_features, test_labels, train_test_cutoff)
  results = evaluator(exp_name, model, test_labels, predictions, scores, probabilities)
  
  return model, results

#--------------------------- Data Prep ----------------------#

def data_valid(datum):
  for key in datum:
    if isinstance(datum[key], float) and math.isnan(datum[key]):
      return False
  return True

def get_clean_data(ticker):
  clean_data = list()
  data = fe.get_features(ticker)
  labels = list()
  for d in data:
    d.pop('date')
    d.pop('_id')
    d.pop('excess')
    if data_valid(d):
      clean_data.append(d)
      labels.append(d.pop('bxret'))
  return clean_data, labels

def get_data_for_multiple(tickers):
  clean_data = list()
  clean_labels = list()
  for ticker in tickers:
    data, labels = get_clean_data(ticker)
    clean_data.extend(data)
    clean_labels.extend(labels)
  return clean_data, clean_lables

def encode_str_features(data):
  str_features = dict()
  print len(data)
  for d in data:
    for i in range(len(d)):
     if type(d[i]) == str:
       if i in str_features and not d[i] in str_features[i]:
         str_features[i].append(d[i])
       elif not i in str_features:
         str_features[i] = list()
         str_features[i].append(d[i])
   
  results = list()
  for d in data:
    for i in range(len(d)):
      if i in str_features:
        d[i] = str_features[i].index(d[i])
    results.append(d)
  return results

def get_data_sets(data, labels, train_test_cutoff=.75):
  data_length = len(data)
  partition_index = int(data_length * train_test_cutoff)
  l = list()
  for d in data:
    f = list()
    for k in d:
      f.append(d[k])
    l.append(f)
    
  cat_features = [i for i in range(len(l[0])) if type(l[0][i]) == str]
  print cat_features
  train = encode_str_features(l)
  train = pw.OneHotEncoder(categorical_features=cat_features).fit_transform(l).toarray()
  train = pw.normalize(train, 'l2', 0)
  train = fs.SelectPercentile(fs.f_classif, percentile=5).fit_transform(train, labels)
  print 'Length of training set: %d\nLength of test set: %d' \
      % (partition_index, data_length - partition_index)
  return np.array(train[:partition_index]), np.array(train[partition_index:]), np.array(labels[:partition_index]), np.array(labels[partition_index:])
  
def get_data(data, labels, train_test_cutoff=.75):
  x_train, features, y_train, test = get_data_sets(data, labels, train_test_cutoff)
  return features, test

#--------------------------- Model Prep ----------------------#

def select_model(model_key):
  model = None
  if model_key == 'b':
    model = GradientBoostingClassifier()
  elif model_key == 'svc':
    model = SVC(probability=True, gamma='auto')
  elif model_key == 'nusvc':
    print 'selecting NuSVC'
    model = NuSVC(probability=True)
  elif model_key == 'r':
    model = RandomForestClassifier(class_weight={'buy':1, 'stay':.75})
  elif model_key == 'e':
    model = ExtraTreesClassifier()
  elif model_key == 'nn':
    model = KNeighborsClassifier()
  elif model_key == 'gmm':
    model = DPGMM()
  return model, model_key

def get_hyper_parameters(model_key):
  hyper_parameters = None
  if model_key == 'b':
    hyper_parameters = [{'learn_rate':[.1], 'loss':['deviance', 'exponential'], 'n_estimators': [10,20, 50, 100],
                         'max_depth': [25], 'subsample':[.25]}]
  elif model_key == 'svc':
    hyper_parameters = [{'C':[1,1e3, 5e3, 1e4, 5e4, 1e5], 'kernel':['rbf',  'sigmoid', 'poly'], 'degree':[3, 6, 9]
                         ,'gamma':[ .01, .1], 'coef0':[0.0, .01 ,.02]}]
  elif model_key == 'nusvc':
    hyper_parameters = [{'nu':[.1, .4, .6, .7,], 'kernel':['rbf', 'sigmoid', 'poly'], 'degree':[9]
                         , 'coef0':[0.0, .01, .5, 1, 5]}] 
  elif model_key == 'r':
    hyper_parameters = [{'n_estimators':[10, 50], 'criterion':['gini', 'entropy']
                        ,'max_leaf_nodes':[40, 100, 200]}]
  elif model_key == 'e':
    hyper_parameters = [{'n_estimators':[10, 100, 200], 'criterion':['gini', 'entropy']}]
  elif model_key == 'nn':
    hyper_parameters = [{'n_neighbors': [5, 15, 35, 61], 'algorithm': ['ball_tree', 'kd_tree', 'brute'],
                         'p':[1, 2, 3], 'weights':['distance', 'uniform'] }]
  elif model_key == 'gmm':
    hyper_parameters = [{'covariance_type':['spherical', 'diag']}]
  return hyper_parameters

def get_best_model_params(model, data, labels, model_type='b', train_test_cutoff=.75):
  train, x_test, test, y_test = get_data_sets(data, labels, train_test_cutoff)
  hyper_parameters = get_hyper_parameters(model_type)
  clf = gs(model, hyper_parameters)
  
  if model_type == 'gmm':
    clf = model
    clf.fit(train)
  else:  
    clf.fit(train, test)
  
  print "Best parameters set found on development set:"
  print
  if not model_type == 'gmm': print clf.best_estimator_
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
    out_file = open('%s_output.txt' % sys.argv[2], 'w', buffering=0)
    detailed_file = open('%s_detailed_output.txt' % sys.argv[2], 'w', buffering=0)
    ticker_list = []
    for line in f:
      ticker = line.strip()
      print '*' * 50, ticker
      d, l = get_clean_data(ticker)
      try:
        model, mtype = select_model(sys.argv[2])
        c = get_best_model_params(model, d, l, model_type=mtype)
        features, test = get_data(d, l)
        if mtype == 'gmm':
          predictions = c.score(features)
          score = predictions
        else:
          score = c.score(features, test)
          predictions = c.predict(features)
        if not mtype == 'gmm':out_file.write("%r, %f\n" % (ticker, score))
        detailed_file.write('*' * 25 + ticker+'*' * 25 +'\n')
        detailed_file.write(classification_report(test, predictions) + '\n')
        detailed_file.write('%r\n' %confusion_matrix(test, predictions))
        if not mtype == 'gmm':print '*' * 50, 'Score for %r: %f' % (ticker, score)
        print classification_report( test, predictions)
        print confusion_matrix(test, predictions)
        
        with open('%s_%s.pkl' % (mtype, ticker), 'wb') as fid:
            cPickle.dump(c, fid)
      except Exception, e:
        print e 
        pass
    f.close()
    out_file.close()
    detailed_file.close()
  else:
    d, l = get_clean_data('GOOG')
    c = get_best_model_params(GradientBoostingClassifier(), d, l)
    features, test = get_data(d, l)
    print c.score(features, test)
