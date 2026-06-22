import sys
import json
import subprocess
import os
import re

def extract_json(text):
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r'(\{.*\}|\[.*\])', text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1))
            except json.JSONDecodeError:
                pass
        raise json.JSONDecodeError("No JSON found", text, 0)

def get_cli_path():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_dir, ".venv", "Scripts", "notebooklm.exe")

def run_cmd(args):
    cli = get_cli_path()
    if not os.path.exists(cli):
        print(json.dumps({"error": f"CLI not found at {cli}. Ensure uv setup is complete."}))
        sys.exit(1)
    
    cmd = [cli] + args + ["--json"]
    # Set encoding to utf-8 to prevent Windows UnicodeDecodeError
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    
    result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', env=env)
    
    if result.returncode != 0:
        # Pass the error JSON if possible, else wrap output
        output_str = result.stdout if result.stdout.strip() else result.stderr
        try:
            err_data = extract_json(output_str)
            print(json.dumps({"error": err_data, "exit_code": result.returncode}))
        except json.JSONDecodeError:
            print(json.dumps({"error": output_str.strip(), "exit_code": result.returncode}))
        sys.exit(result.returncode)
    
    try:
        # Validate output is json
        data = extract_json(result.stdout)
        print(json.dumps(data))
    except json.JSONDecodeError:
        print(json.dumps({"raw_output": result.stdout.strip()}))

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python notebook_bridge.py <action> [args...]")
        sys.exit(1)
        
    action = sys.argv[1]
    if action == "create":
        # python notebook_bridge.py create "Title"
        run_cmd(["create", sys.argv[2]])
    elif action == "list":
        run_cmd(["list"])
    elif action == "add-source":
        # python notebook_bridge.py add-source <nb_id> <url>
        run_cmd(["source", "add", sys.argv[3], "-n", sys.argv[2]])
    elif action == "research":
        # python notebook_bridge.py research <nb_id> <query> <mode>
        run_cmd(["source", "add-research", sys.argv[3], "--mode", sys.argv[4], "-n", sys.argv[2], "--no-wait"])
    elif action == "wait-research":
        # python notebook_bridge.py wait-research <nb_id>
        run_cmd(["research", "wait", "-n", sys.argv[2]])
    elif action == "list-source":
        # python notebook_bridge.py list-source <nb_id>
        run_cmd(["source", "list", "-n", sys.argv[2]])
    elif action == "delete-source":
        # python notebook_bridge.py delete-source <nb_id> <source_id>
        run_cmd(["source", "delete", sys.argv[3], "-n", sys.argv[2]])
    elif action == "ask":
        # python notebook_bridge.py ask <nb_id> <question>
        run_cmd(["ask", sys.argv[3], "-n", sys.argv[2]])
    elif action == "status":
        run_cmd(["status"])
    else:
        print(json.dumps({"error": f"Unknown action: {action}"}))
        sys.exit(1)
