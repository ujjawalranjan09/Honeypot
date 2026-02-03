from scam_detector import ScamDetector
import logging
import time

# Configure logging to see progress
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def main():
    detector = ScamDetector()
    
    start_time = time.time()
    print("Starting Ultra-Diverse Dataset Training...")
    
    # This will now load all 200k+ datasets as per my recent update to scam_detector.py
    accuracy = detector.train_model()
    
    end_time = time.time()
    duration = end_time - start_time
    
    if accuracy:
        print(f"✅ Training Complete!")
        print(f"📊 Accuracy: {accuracy:.2%}")
        print(f"⏱️ Duration: {duration/60:.2f} minutes")
    else:
        print(f"❌ Training Failed.")

if __name__ == "__main__":
    main()
