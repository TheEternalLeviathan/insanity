import joblib
import numpy as np


class TfidfModel:
    def __init__(self, vectorizer_path: str, model_path: str):
        self.vectorizer = joblib.load(vectorizer_path)
        self.model = joblib.load(model_path)

    def predict_proba(self, text: str) -> float:
        X = self.vectorizer.transform([text])
        # assuming class 1 = fake
        prob = self.model.predict_proba(X)[0][1]
        return float(prob)
