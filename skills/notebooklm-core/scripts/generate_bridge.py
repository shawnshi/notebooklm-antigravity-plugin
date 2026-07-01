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
    
    # We do NOT add --wait here, since this is for Agents and long tasks should return immediately.
    cmd = [cli] + args + ["--json"]
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    
    result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', env=env)
    
    if result.returncode != 0:
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
            print(json.dumps({"error": "Usage: python generate_bridge.py <action> [args...]"}))
            sys.exit(1)

        action = sys.argv[1]
        # format: python generate_bridge.py <type> <notebook_id> [instructions]
        nb_id = sys.argv[2]
        
        if action in ["audio", "video"]:
            instructions = sys.argv[3] if len(sys.argv) > 3 else ""
            run_cmd(["generate", action, instructions, "-n", nb_id])
        elif action in ["slide-deck", "quiz", "mind-map", "report", "flashcards", "infographic", "data-table", "cinematic-video"]:
            run_cmd(["generate", action, "-n", nb_id])
        elif action == "status":
            # Check status of all artifacts
            run_cmd(["artifact", "list", "-n", nb_id])
        elif action == "wait":
            # usage: python generate_bridge.py wait <notebook_id> <artifact_id>
            artifact_id = sys.argv[3]
            run_cmd(["artifact", "wait", artifact_id, "-n", nb_id])
        elif action == "download":
            # usage: python generate_bridge.py download <notebook_id> <artifact_id> <type> <output_path>
            artifact_id = sys.argv[3]
            art_type = sys.argv[4]
            out_path = sys.argv[5]

            # Security: Prevent Path Traversal
            # Resolve the output path absolutely and resolve symlinks
            abs_out = os.path.realpath(out_path)

            # The bridge scripts execute from the repo root in this setup, or we must ensure
            # they write strictly within current working directory's brain or scratch folders.
            cwd = os.getcwd()
            allowed_brain = os.path.realpath(os.path.join(cwd, "brain"))
            allowed_scratch = os.path.realpath(os.path.join(cwd, "scratch"))

            # Ensure the output path is strictly within the allowed directories
            is_valid_brain = os.path.commonpath([allowed_brain, abs_out]) == allowed_brain
            is_valid_scratch = os.path.commonpath([allowed_scratch, abs_out]) == allowed_scratch

            if not (is_valid_brain or is_valid_scratch):
                print(json.dumps({"error": "Invalid output path: Path must strictly resolve within the 'brain' or 'scratch' directories"}))
                sys.exit(1)

            run_cmd(["download", art_type, out_path, "-a", artifact_id, "-n", nb_id])
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
