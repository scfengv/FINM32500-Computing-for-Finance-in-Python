import json
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split, StratifiedKFold, cross_val_score
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (accuracy_score, precision_score, recall_score, confusion_matrix)

def load_features_config(path: str):
    with open(path, 'r') as f:
        return json.load(f)

def load_model_params(path: str):
    with open(path, 'r') as f:
        return json.load(f)

def get_X_y(df: pd.DataFrame, cfg: dict):
    X = df[cfg['features']].values
    y = df[cfg['label']].values
    return X, y

def train_classification_models(X, y, model_params):
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, shuffle=False)

    cv = StratifiedKFold(n_splits=5, shuffle=False)

    models = {}
    metrics = {}

    lr = Pipeline([('scaler', StandardScaler()), ('clf', LogisticRegression(**model_params['LogisticRegression']))])
    lr_cv = cross_val_score(lr, X_train, y_train, cv=cv, scoring='accuracy')
    lr.fit(X_train, y_train)
    pred = lr.predict(X_test)

    models['log_reg'] = lr
    metrics['log_reg'] = {
        'cv_accuracy': lr_cv.mean(),
        'test_accuracy': accuracy_score(y_test, pred),
        'precision': precision_score(y_test, pred),
        'recall': recall_score(y_test, pred),
        'confusion_matrix': confusion_matrix(y_test, pred).tolist(),
    }

    rf = RandomForestClassifier(**model_params['RandomForestClassifier'])
    rf_cv = cross_val_score(rf, X_train, y_train, cv=cv, scoring='accuracy')
    rf.fit(X_train, y_train)
    pred2 = rf.predict(X_test)

    models['rf_clf'] = rf
    metrics['rf_clf'] = {
        'cv_accuracy': rf_cv.mean(),
        'test_accuracy': accuracy_score(y_test, pred2),
        'precision': precision_score(y_test, pred2),
        'recall': recall_score(y_test, pred2),
        'confusion_matrix': confusion_matrix(y_test, pred2).tolist(),
        'feature_importances': rf.feature_importances_.tolist(),
    }

    return models, metrics

def add_predictions_to_df(df, models, cfg):
    df = df.copy()
    X = df[cfg['features']].values

    for name, model in models.items():
        if hasattr(model, 'predict_proba'):
            df[f'proba_{name}'] = model.predict_proba(X)[:, 1]
        df[f'pred_{name}'] = model.predict(X)

    return df