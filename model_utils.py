import numpy as np
import pandas as pd
from sklearn.metrics import classification_report, confusion_matrix, ConfusionMatrixDisplay, cohen_kappa_score, matthews_corrcoef, accuracy_score, f1_score
from sklearn.model_selection import RandomizedSearchCV
import matplotlib.pyplot as plt

def train_classifier(classifier, param_grid, X, y, scoring = "f1_macro", **search_args):
    """ Trains a classifier and optimizes its hyperparameters.

    Parameters
    ----------

    classifier: The classifier to be trained.
    param_grid: A dictionary containing the hyperparameters and their corresponding values to be input into RandomizedSearchCV.
    X, y: The features and labels of the training dataset.
    scoring: The evaluation metric to be used for selecting the best classifier. The default is f1_macro.
    **search_args: Additional keyword arguments to be passed to RandomizedSearchCV.

    Returns
    -------

    best_classifier: The classifier with the highest cross-validated performance
    
    """ 
    
    # Optimize the hyperparameters and extract the best model
    clf = RandomizedSearchCV(classifier, 
                             param_grid,
                             scoring = scoring,
                             **search_args)
    
    # Find the best hyperparameters using cross-validation and extract the best classifier
    clf.fit(X,y)
    
    return clf.best_estimator_


def plot_report(y_true, y_pred):
    """ Plots a classification report and confusion matrix.

    Parameters
    ----------

    y_true: True labels
    y_pred: Predictions
    class_labels: The class labels to be used in the confusion matrix

    """
    
    # Classification report
    print(classification_report(y_true, y_pred))

    # Cohen's kappa and Matthews correlation coefficient
    print("Cohen's kappa: {:.2f}".format(cohen_kappa_score(y_true, y_pred)))
    print("Matthews correlation coefficient: {:.2f}".format(matthews_corrcoef(y_true, y_pred)))
    
    # Confusion matrix
    disp = ConfusionMatrixDisplay.from_predictions(y_true, y_pred, xticks_rotation = 45)

def compare_train_test_performance(train_y, train_pred, test_y, test_pred):
    """ Plots a report that compares the training and test performance.

    Parameters
    ----------

    train_y: True training labels
    train_pred: Predictions on training data
    test_y: True test labels
    test_pred: Predictions on test data

    """

    data = [(train_y, train_pred),(test_y, test_pred)]
    metrics = [cohen_kappa_score, matthews_corrcoef, accuracy_score, lambda y,y_hat: f1_score(y,y_hat,average = 'macro')]
    metric_names = ["kappa", "matthews_corr_coef", "accuracy", "macro_f1"]
    results = [[metric(*dataset) for dataset in data] for metric in metrics] 

    f,ax = plt.subplots(2,2)
    f.tight_layout()
    ax = ax.flatten()

    for i,ax in enumerate(ax):
        ax.bar([0,1],results[i])
        ax.set_xticks([0,1])
        ax.set_xticklabels(["train","test"])
        ax.set_title(metric_names[i])

    
    

