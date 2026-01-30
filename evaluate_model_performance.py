
import pandas as pd
from scam_detector import detector
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
import joblib
import os
import time

def evaluate():
    print("Loading 20k Dataset...")
    try:
        df = pd.read_csv("massive_20k_scam_dataset.csv")
    except FileNotFoundError:
        print("Error: massive_20k_scam_dataset.csv not found.")
        return

    print(f"Dataset Loaded: {len(df)} rows")
    print(f"Scam vs Legit Distribution:\n{df['label'].value_counts()}")

    X = df['message_text'].fillna('')
    y = (df['label'] == 'scam').astype(int)

    # Split
    print("\nSplitting Data (80% Train, 20% Test)...")
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

    # Train
    print("Training Model (This may take a moment)...")
    start_time = time.time()
    
    # We can use the detector's internal logic or redo it here to be explicit
    # Let's use the detector's train_model to ensure identical configuration, 
    # but that function returns scalar accuracy. 
    # To get detailed metrics, let's replicate the training steps here using config params.
    
    # Config params from known values or detector defaults
    # Replicating logic for transparency in report
    vectorizer = TfidfVectorizer(max_features=5000, ngram_range=(1,3))
    X_train_vec = vectorizer.fit_transform(X_train)
    X_test_vec = vectorizer.transform(X_test)

    clf = GradientBoostingClassifier(n_estimators=100, learning_rate=0.1, max_depth=5, random_state=42)
    clf.fit(X_train_vec, y_train)
    
    train_time = time.time() - start_time
    print(f"Training completed in {train_time:.2f} seconds")

    # Predict
    print("\nEvaluating on Test Set (4000 samples)...")
    y_pred = clf.predict(X_test_vec)

    # Metrics
    acc = accuracy_score(y_test, y_pred)
    report = classification_report(y_test, y_pred, target_names=['Legitimate', 'Scam'])
    conf_mat = confusion_matrix(y_test, y_pred)

    print("\n" + "="*40)
    print(f"FINAL ACCURACY SCORE: {acc:.2%}")
    print("="*40)
    print("\nDetailed Classification Report:")
    print(report)
    print("\nConfusion Matrix:")
    print(f"True Negatives (Legit->Legit): {conf_mat[0][0]}")
    print(f"False Positives (Legit->Scam): {conf_mat[0][1]}")
    print(f"False Negatives (Scam->Legit): {conf_mat[1][0]}")
    print(f"True Positives (Scam->Scam): {conf_mat[1][1]}")

    # Also save this model to the system paths so the API uses this high-accuracy one
    print("\nSaving robust model to disk...")
    if not os.path.exists("models"):
        os.makedirs("models")
    joblib.dump(clf, "models/scam_detector.joblib")
    joblib.dump(vectorizer, "models/tfidf_vectorizer.joblib")
    print("Model saved successfully.")

if __name__ == "__main__":
    evaluate()
