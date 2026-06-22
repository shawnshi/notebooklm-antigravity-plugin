import sys
import time
import json
import subprocess
import os

def get_python_exe():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_dir, ".venv", "Scripts", "python.exe")

def get_status(nb_id):
    py_exe = get_python_exe()
    bridge_script = os.path.join(os.path.dirname(os.path.abspath(__file__)), "generate_bridge.py")
    
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    
    result = subprocess.run([py_exe, bridge_script, "status", nb_id], capture_output=True, text=True, encoding='utf-8', env=env)
    
    if result.returncode != 0:
        return None
        
    try:
        # Search for valid JSON in case of pollution
        import re
        match = re.search(r'(\{.*\}|\[.*\])', result.stdout.strip(), re.DOTALL)
        if match:
            return json.loads(match.group(1))
    except Exception:
        pass
        
    return None

def main():
    if len(sys.argv) < 3:
        print(json.dumps({"error": "Usage: python daemon_watchdog.py <nb_id> <task_id>"}))
        sys.exit(1)
        
    nb_id = sys.argv[1]
    task_id = sys.argv[2]
    
    print(f"Watchdog started for Notebook: {nb_id}, Task: {task_id}. Polling every 15 seconds...")
    sys.stdout.flush()
    
    max_retries = 120 # 30 minutes max
    
    for i in range(max_retries):
        data = get_status(nb_id)
        if data and "artifacts" in data:
            artifacts = data["artifacts"]
            
            # Find the specific task
            task = next((a for a in artifacts if a.get("id") == task_id), None)
            if task:
                status = task.get("status")
                if status in ("completed", "failed", "error"):
                    print(f"[WAKEUP] Task {task_id} finished with status: {status} for notebook {nb_id}.")
                    sys.stdout.flush()
                    sys.exit(0)
            else:
                # Task not found yet, maybe still initializing on the backend. Keep polling.
                pass
                
        time.sleep(15)
        
    print(f"[WAKEUP] Watchdog timed out after 30 minutes for notebook {nb_id}.")
    sys.exit(1)

if __name__ == "__main__":
    main()
