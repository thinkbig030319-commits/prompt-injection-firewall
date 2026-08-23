"""
Layer 2: ML classifier for prompt injection detection.
Run: python app/train.py
Produces: models/classifier.joblib
"""
import pandas as pd
import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report


def main():
    df = pd.read_csv("data/dataset.csv")

    X_train, X_test, y_train, y_test = train_test_split(
        df["text"], df["label"], test_size=0.25, random_state=42, stratify=df["label"]
    )

    pipeline = Pipeline([
        ("tfidf", TfidfVectorizer(ngram_range=(1, 2), min_df=1, sublinear_tf=True)),
        ("clf", LogisticRegression(max_iter=1000, class_weight="balanced")),
    ])

    pipeline.fit(X_train, y_train)

    preds = pipeline.predict(X_test)
    print("=== Evaluation on held-out test set ===")
    print(classification_report(y_test, preds, target_names=["benign", "injection"]))

    pipeline.fit(df["text"], df["label"])

    joblib.dump(pipeline, "models/classifier.joblib")
    print("Saved trained model to models/classifier.joblib")


if __name__ == "__main__":
    main()
