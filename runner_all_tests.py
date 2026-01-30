import os
import subprocess
import glob
import re
import json
import time
from datetime import datetime

# Configuration
TEST_FILES_PATTERN = "multi_turn_test_v*.py"
API_URL = "http://localhost:8000"
API_KEY = "YOUR_SECRET_API_KEY"
METRICS_FILE = "session_metrics.jsonl"
REPORT_FILE = "marathon_full_report.md"

def get_test_files():
    files = glob.glob(TEST_FILES_PATTERN)
    # Sort numerically by version extracted from filename
    files.sort(key=lambda x: int(re.search(r'v(\d+)', x).group(1)))
    return files

def get_latest_metrics(count=20):
    if not os.path.exists(METRICS_FILE):
        return []
    with open(METRICS_FILE, 'r') as f:
        lines = f.readlines()
        if not lines:
            return []
        return [json.loads(line) for line in lines[-count:]]

def evaluate_quality(text):
    """Simple rule-based quality evaluation similar to V1/V2"""
    if not text or text == "[No response]": return 0
    score = 5
    text_lower = text.lower()
    if len(text) > 50: score += 1
    if any(q in text for q in ['?', 'kya', 'kaun', 'kaise', 'kyun']): score += 1
    if any(word in text_lower for word in ['ji', 'haan', 'theek', 'ok', 'acha']): score += 1
    if any(word in text_lower for word in ['worried', 'scared', 'problem', 'help']): score += 1
    if 'I am an AI' in text or 'language model' in text_lower: score -= 4
    return max(0, min(10, score))

def extract_intel(text):
    """Basic intel extraction for the summary report"""
    intel = {"upi": [], "links": [], "phones": [], "accounts": []}
    
    # UPI
    upis = re.findall(r'[a-zA-Z0-9._-]+@(ybl|paytm|okaxis|oksbi|okicici|upi)', text.lower())
    if upis: intel["upi"] = upis
    
    # Links
    links = re.findall(r'https?://[^\s]+', text.lower())
    if links: intel["links"] = links
    
    # Phones
    phones = re.findall(r'\b[6-9]\d{9}\b', text)
    if phones: intel["phones"] = phones
    
    return intel

def run_test_and_format(file_path, version):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    # Matching the user's preferred format: test_results_v1_20260130_191419.txt
    results_filename = f"test_results_v{version}_{timestamp}.txt"
    
    print(f"\n{'='*40}")
    print(f"STARTING VERSION {version}: {file_path}")
    print(f"LOGGING TO: {results_filename}")
    print(f"{'='*40}\n")
    
    full_output = []
    report_lines = [
        f"ITERATION {version}: ENHANCED HONEY-POT TEST REPORT",
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "Total Scenarios: [Extracted from run]",
        "Focus: Multi-turn interaction test",
        "\n"
    ]
    
    current_scenario = None
    scenario_logs = []
    quality_scores = []
    intel_total = {"upi": [], "links": [], "phones": [], "accounts": []}
    
    try:
        process = subprocess.Popen(
            ['python', '-u', file_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            universal_newlines=True
        )
        
        for line in process.stdout:
            print(line, end='', flush=True)
            full_output.append(line)
            
            # Detect Scenario Start
            if "SCENARIO:" in line or "RUNNING:" in line:
                current_scenario = line.split(":")[-1].strip().replace("=", "").strip()
                scenario_logs.append(f"\n{'='*80}\n SCENARIO: {current_scenario} \n{'='*80}\n")
            
            # Detect Turns
            if "Scammer:" in line or "SCAMMER:" in line:
                scenario_logs.append(line.strip())
            if "Bot:" in line or "BOT [" in line:
                bot_text = line.split("]:")[-1].strip() if "]:" in line else line.split(":")[-1].strip()
                score = evaluate_quality(bot_text)
                quality_scores.append(score)
                scenario_logs.append(f"Bot [Q:{score}/10]: {bot_text}\n")
                
                # Extract intel for summary
                last_scammer_msg = scenario_logs[-2] if len(scenario_logs) >= 2 else ""
                found = extract_intel(last_scammer_msg)
                for k in intel_total: intel_total[k].extend(found[k])

        process.wait(timeout=600)
    except Exception as e:
        scenario_logs.append(f"\n[EXCEPTION: {e}]")

    # Construct final report
    report_lines.extend(scenario_logs)
    
    avg_q = sum(quality_scores)/len(quality_scores) if quality_scores else 0
    report_lines.append("\n--- INTELLIGENCE SUMMARY ---")
    report_lines.append(f"UPI IDs: {list(set(intel_total['upi']))}")
    report_lines.append(f"Phishing Links: {list(set(intel_total['links']))}")
    report_lines.append(f"Phone Numbers: {list(set(intel_total['phones']))}")
    report_lines.append(f"Average Response Quality: {avg_q:.1f}/10")
    report_lines.append("-" * 28)
    
    with open(results_filename, 'w', encoding='utf-8') as f:
        f.write("\n".join(report_lines))
        
    return "\n".join(report_lines), results_filename

def main():
    test_files = get_test_files()
    
    # Initialize master report
    with open(REPORT_FILE, 'w', encoding='utf-8') as f:
        f.write(f"# Marathon Report - {datetime.now().isoformat()}\n\n")

    for test_file in test_files:
        version = re.search(r'v(\d+)', test_file).group(1)
        
        formatted_report, filename = run_test_and_format(test_file, version)
        
        # Append to master report
        with open(REPORT_FILE, 'a', encoding='utf-8') as f:
            f.write(f"## Version {version}: `{test_file}`\n")
            f.write(f"Full log: [{filename}](file:///{os.path.abspath(filename)})\n\n")
            f.write("```text\n")
            f.write(formatted_report)
            f.write("\n```\n\n---\n")
            
    print(f"\nMarathon complete. Final report saved to {REPORT_FILE}")

if __name__ == "__main__":
    main()
