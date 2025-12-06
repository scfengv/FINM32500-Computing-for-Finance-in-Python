import pandas as pd
import numpy as np
from src.train_model import train_classification_models

def test_training_shapes():
    X = np.random.randn(200, 5)
    y = np.random.randint(0, 2, 200)

    model_params = {'logistic_regression': {'max_iter': 200}, 'random_forest_classifier': {'n_estimators': 10}}
    models, metrics = train_classification_models(X, y, model_params)

    assert 'log_reg' in models
    assert 'rf_clf' in models