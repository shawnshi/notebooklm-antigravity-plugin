import sys
import json
import subprocess
import os
import re

def extract_json(text):
    text_strip = text.strip()
    try:
        return json.loads(text_strip)
    except json.JSONDecodeError:
        start_brace = text_strip.find('{')
        end_brace = text_strip.rfind('}')

        start_bracket = text_strip.find('[')
        end_bracket = text_strip.rfind(']')

        candidates = []
        if start_brace != -1 and end_brace != -1 and end_brace > start_brace:
            candidates.append((start_brace, end_brace))
        if start_bracket != -1 and end_bracket != -1 and end_bracket > start_bracket:
            candidates.append((start_bracket, end_bracket))

        candidates.sort(key=lambda x: x[0])

        for start_idx, end_idx in candidates:
            try:
                return json.loads(text_strip[start_idx:end_idx+1])
            except json.JSONDecodeError:
                continue

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
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    
    result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', env=env)
    
    if result.returncode != 0:
        # The notebooklm CLI often prints JSON errors to stdout even on exit code 1
        output_str = result.stdout if result.stdout.strip() else result.stderr
        try:
            err_data = extract_json(output_str)
            print(json.dumps({"error": err_data, "exit_code": result.returncode}))
        except json.JSONDecodeError:
            print(json.dumps({"error": output_str.strip(), "exit_code": result.returncode}))
        sys.exit(result.returncode)
    
    try:
        data = extract_json(result.stdout)
        print(json.dumps(data))
    except json.JSONDecodeError:
        print(json.dumps({"raw_output": result.stdout.strip()}))

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python auth_bridge.py <action>")
        sys.exit(1)
        
    action = sys.argv[1]
    if action == "check":
        run_cmd(["auth", "check", "--test"])
    elif action == "login":
        # Check if we should try headless cookie steal first
        # python auth_bridge.py login [browser_name]
        if len(sys.argv) > 2:
            browser = sys.argv[2]
            run_cmd(["login", "--browser-cookies", browser])
        else:
            run_cmd(["login"])
    else:
        print(json.dumps({"error": f"Unknown action: {action}"}))
        sys.exit(1)
