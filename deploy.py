"""
Deployment script for Vercel - lightweight version
Removes heavy dependencies and large files for deployment
"""
import os
import shutil
import subprocess

def prepare_deployment():
    """Clean up files for Vercel deployment"""
    
    # Remove large datasets
    large_files = [
        'massive_200k_ultra_diverse_dataset.csv',
        'massive_200k_ultra_diverse_dataset_clean.csv', 
        'massive_200k_ultra_diverse_dataset_complete.csv',
        'massive_20k_scam_dataset.csv',
        'additional_data.csv'
    ]
    
    for file in large_files:
        if os.path.exists(file):
            os.remove(file)
            print(f"Removed: {file}")
    
    # Remove test files
    test_patterns = [
        'test_*.py',
        'api_test_results*.txt',
        'evaluation_results*.txt',
        'final_test_results*.txt',
        'benchmark_*.py',
        'runner_*.py',
        'quick_*.py',
        'advanced_*.py',
        'diverse_*.py',
        'indian_*.py',
        'multi_turn_*.py',
        'final_validation_*.py',
        'generate_*.py',
        'retrain_*.py',
        'run_*.py'
    ]
    
    for pattern in test_patterns:
        for file in os.listdir('.'):
            if file.startswith(pattern.split('*')[0]) and file.endswith(pattern.split('*')[1]):
                if os.path.exists(file):
                    os.remove(file)
                    print(f"Removed: {file}")
    
    # Create lightweight requirements.txt
    lightweight_reqs = """
# Lightweight requirements for Vercel
fastapi>=0.115.0
uvicorn[standard]>=0.30.0
gunicorn>=22.0.0
pydantic>=2.9.0
python-dotenv==1.0.0
httpx>=0.27.0
aiofiles>=23.2.0
google-generativeai==0.8.3
"""
    
    with open('requirements.txt', 'w') as f:
        f.write(lightweight_reqs)
    
    print("Created lightweight requirements.txt")

if __name__ == "__main__":
    prepare_deployment()