"""
Full model training on all available datasets.
Combines all massive datasets + additional data for comprehensive training.
"""
import pandas as pd
import joblib
import os
import time
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.model_selection import train_test_split
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Create models directory
os.makedirs("models", exist_ok=True)

# List all datasets to load
datasets = [
    "massive_200k_ultra_diverse_dataset.csv",
    "massive_200k_ultra_diverse_dataset_clean.csv",
    "massive_200k_ultra_diverse_dataset_complete.csv",
    "massive_20k_scam_dataset.csv",
    "massive_5k_scam_dataset.csv",
    "additional_data.csv",
]

start_time = time.time()

try:
    logger.info("="*60)
    logger.info("COMPREHENSIVE MODEL TRAINING ON ALL DATASETS")
    logger.info("="*60)
    
    # Load all datasets
    dfs = []
    total_loaded = 0
    
    for fname in datasets:
        if not os.path.exists(fname):
            logger.warning(f"⚠️ Dataset not found: {fname}")
            continue
        
        try:
            logger.info(f"\n📂 Loading {fname}...")
            df = pd.read_csv(fname)
            
            # Auto-detect message and label columns
            text_col = None
            label_col = None
            
            for col in df.columns:
                if col.lower() in ['message_text', 'text', 'message', 'content']:
                    text_col = col
                if col.lower() in ['label', 'is_scam', 'class', 'target']:
                    label_col = col
            
            # Fallback to column positions if names not found
            if text_col is None or label_col is None:
                if len(df.columns) >= 2:
                    text_col = df.columns[1]
                    label_col = df.columns[2]
            
            df_subset = df[[text_col, label_col]].copy()
            df_subset.columns = ['message_text', 'label']
            
            logger.info(f"   ✓ Loaded {len(df_subset)} samples")
            dfs.append(df_subset)
            total_loaded += len(df_subset)
            
        except Exception as e:
            logger.error(f"   ✗ Error loading {fname}: {e}")
            continue
    
    if not dfs:
        logger.error("❌ No datasets loaded!")
        exit(1)
    
    # Combine all datasets
    logger.info(f"\n🔗 Combining all datasets...")
    df_all = pd.concat(dfs, ignore_index=True)
    
    # Remove duplicates
    initial_count = len(df_all)
    df_all.drop_duplicates(subset=['message_text'], inplace=True)
    logger.info(f"   Total before dedup: {initial_count}")
    logger.info(f"   Total after dedup:  {len(df_all)}")
    logger.info(f"   Duplicates removed: {initial_count - len(df_all)}")
    
    # Prepare features and labels
    X = df_all['message_text'].astype(str).fillna('')
    y = (df_all['label'].astype(str).str.lower() == 'scam').astype(int)
    
    logger.info(f"\n📊 Dataset Statistics:")
    logger.info(f"   Total samples: {len(X)}")
    logger.info(f"   Scam messages: {(y == 1).sum()}")
    logger.info(f"   Legitimate messages: {(y == 0).sum()}")
    logger.info(f"   Class ratio: {(y == 1).sum() / len(y):.1%} scams")
    
    # Split data
    logger.info(f"\n📋 Splitting data (80/20)...")
    X_train, X_test, y_train, y_test = train_test_split(
        X, y,
        test_size=0.2,
        random_state=42,
        stratify=y
    )
    logger.info(f"   Training set: {len(X_train)} samples")
    logger.info(f"   Test set: {len(X_test)} samples")
    
    # Vectorize
    logger.info(f"\n🔤 Vectorizing text features...")
    vectorizer = TfidfVectorizer(
        max_features=8000,
        ngram_range=(1, 2),
        min_df=2,
        max_df=0.95,
        lowercase=True,
        stop_words='english'
    )
    
    X_train_vec = vectorizer.fit_transform(X_train)
    X_test_vec = vectorizer.transform(X_test)
    logger.info(f"   Vectorizer vocabulary size: {len(vectorizer.vocabulary_)}")
    logger.info(f"   Features extracted: {X_train_vec.shape[1]}")
    
    # Train model
    logger.info(f"\n🤖 Training Gradient Boosting Classifier...")
    logger.info(f"   Estimators: 100")
    logger.info(f"   Max depth: 6")
    logger.info(f"   Learning rate: 0.1")
    
    model = GradientBoostingClassifier(
        n_estimators=100,
        max_depth=6,
        learning_rate=0.1,
        random_state=42,
        verbose=1
    )
    
    model.fit(X_train_vec, y_train)
    
    # Evaluate
    logger.info(f"\n✅ Model Training Complete!")
    
    train_accuracy = model.score(X_train_vec, y_train)
    test_accuracy = model.score(X_test_vec, y_test)
    
    logger.info(f"\n📈 Model Performance:")
    logger.info(f"   Training Accuracy: {train_accuracy:.2%}")
    logger.info(f"   Test Accuracy: {test_accuracy:.2%}")
    
    # Save model
    logger.info(f"\n💾 Saving model artifacts...")
    joblib.dump(model, "models/scam_detector.joblib")
    joblib.dump(vectorizer, "models/tfidf_vectorizer.joblib")
    
    model_size = os.path.getsize("models/scam_detector.joblib") / (1024 * 1024)
    vectorizer_size = os.path.getsize("models/tfidf_vectorizer.joblib") / (1024 * 1024)
    total_size = model_size + vectorizer_size
    
    logger.info(f"   Model file: {model_size:.2f} MB")
    logger.info(f"   Vectorizer file: {vectorizer_size:.2f} MB")
    logger.info(f"   Total size: {total_size:.2f} MB")
    
    # Summary
    elapsed_time = time.time() - start_time
    logger.info(f"\n{'='*60}")
    logger.info(f"✅ TRAINING SUCCESSFUL!")
    logger.info(f"{'='*60}")
    logger.info(f"Total training time: {elapsed_time/60:.1f} minutes")
    logger.info(f"Datasets combined: {len(dfs)}")
    logger.info(f"Total samples trained: {len(X)}")
    logger.info(f"Test accuracy: {test_accuracy:.2%}")
    logger.info(f"Model ready for deployment! 🚀")
    
except KeyboardInterrupt:
    logger.warning("\n⚠️ Training interrupted by user")
    exit(1)
except Exception as e:
    logger.error(f"\n❌ Training failed: {e}")
    import traceback
    traceback.print_exc()
    exit(1)
