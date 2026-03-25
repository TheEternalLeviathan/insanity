class FakeNewsEnsemble:
    def __init__(self, tfidf_model, bert_model):
        self.tfidf = tfidf_model
        self.bert = bert_model

    def predict(self, text: str) -> dict:
        tfidf_prob = self.tfidf.predict_proba(text)
        bert_prob = self.bert.predict_proba(text)

        return {
            "tfidf_prob": tfidf_prob,
            "bert_prob": bert_prob
        }
