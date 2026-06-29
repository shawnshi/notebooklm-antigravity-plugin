import sys
import json
import subprocess
import os

def extract_json(text):
    try:
        return json.loads(text), text
    except json.JSONDecodeError:
        decoder = json.JSONDecoder()

        start_brace = text.find('{')
        start_bracket = text.find('[')

        candidates = []
        if start_brace != -1:
            candidates.append(start_brace)
        if start_bracket != -1:
            candidates.append(start_bracket)

        candidates.sort()

        for start_idx in candidates:
            try:
                obj, new_end = decoder.raw_decode(text, start_idx)
                return obj, text[start_idx:new_end]
            except json.JSONDecodeError:
                pass

        raise json.JSONDecodeError("No JSON found", text, 0)

def get_cli_path():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_dir, ".venv", "Scripts", "notebooklm.exe")

def run_cmd(args):
    cli = get_cli_path()
    if not os.path.exists(cli):
        print(json.dumps({"error": "CLI not found. Ensure uv setup is complete."}))
        sys.exit(1)
        
    cmd = [cli] + args + ["--json"]
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    
    result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', env=env)
    
    if result.returncode != 0:
        # The notebooklm CLI often prints JSON errors to stdout even on exit code 1
        output_str = result.stdout if result.stdout.strip() else result.stderr
        try:
            err_data, _ = extract_json(output_str)
            print(json.dumps({"error": err_data, "exit_code": result.returncode}))
        except json.JSONDecodeError:
            print(json.dumps({"error": "CLI execution failed with non-JSON output", "exit_code": result.returncode}))
        sys.exit(result.returncode)
    
    try:
        # Avoid redundant JSON serialization for successful responses
        # print(json.dumps(data)) is slow for large objects (e.g. 10MB reports)
        _, raw_json_str = extract_json(result.stdout)
        print(raw_json_str)
    except json.JSONDecodeError:
        print(json.dumps({"error": "CLI execution succeeded but returned non-JSON output"}))

if __name__ == "__main__":
    try:
        if len(sys.argv) < 2:
            print(json.dumps({"error": "Usage: python auth_bridge.py <action>"}))
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
    except IndexError:
        print(json.dumps({"error": "Missing required arguments"}))
        sys.exit(1)
    except KeyboardInterrupt:
        print(json.dumps({"error": "Execution interrupted by user"}))
        sys.exit(1)
    except Exception:
        print(json.dumps({"error": "An unexpected error occurred during execution"}))
        sys.exit(1)
