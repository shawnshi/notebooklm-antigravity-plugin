import sys
import json
import subprocess
import os

def extract_json(text):
    try:
        return json.loads(text), text
    except json.JSONDecodeError:
        start_brace = text.find('{')
        end_brace = text.rfind('}')

        start_bracket = text.find('[')
        end_bracket = text.rfind(']')

        candidates = []
        if start_brace != -1 and end_brace != -1 and end_brace > start_brace:
            candidates.append((start_brace, end_brace))
        if start_bracket != -1 and end_bracket != -1 and end_bracket > start_bracket:
            candidates.append((start_bracket, end_bracket))

        candidates.sort(key=lambda x: x[0])

        for start_idx, end_idx in candidates:
            try:
                candidate_str = text[start_idx:end_idx+1]
                return json.loads(candidate_str), candidate_str
            except json.JSONDecodeError:
                continue

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
    # Set encoding to utf-8 to prevent Windows UnicodeDecodeError
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    
    result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', env=env)
    
    if result.returncode != 0:
        # Pass the error JSON if possible, else wrap output
        output_str = result.stdout if result.stdout.strip() else result.stderr
        try:
            err_data, _ = extract_json(output_str)
            print(json.dumps({"error": err_data, "exit_code": result.returncode}))
        except json.JSONDecodeError:
            print(json.dumps({"error": "CLI execution failed with non-JSON output", "exit_code": result.returncode}))
        sys.exit(result.returncode)
    
    try:
        # Validate output is json
        # Avoid redundant JSON serialization for successful responses
        # print(json.dumps(data)) is slow for large objects (e.g. 10MB reports)
        _, raw_json_str = extract_json(result.stdout)
        print(raw_json_str)
    except json.JSONDecodeError:
        print(json.dumps({"error": "CLI execution succeeded but returned non-JSON output"}))

if __name__ == "__main__":
    try:
        if len(sys.argv) < 2:
            print(json.dumps({"error": "Usage: python notebook_bridge.py <action> [args...]"}))
            sys.exit(1)

        action = sys.argv[1]
        if action == "create":
            # python notebook_bridge.py create "Title"
            run_cmd(["create", sys.argv[2]])
        elif action == "list":
            run_cmd(["list"])
        elif action == "add-source":
            # python notebook_bridge.py add-source <nb_id> <url>
            url = sys.argv[3]

            # Security: Prevent SSRF and Local File Inclusion
            if not url.startswith(("http://", "https://")):
                print(json.dumps({"error": "Invalid URL: Must start with http:// or https://"}))
                sys.exit(1)

            import urllib.parse
            import socket
            import ipaddress

            try:
                parsed_url = urllib.parse.urlparse(url)
                hostname = parsed_url.hostname or ""

                # If hostname is localhost, block immediately
                if hostname.lower() in ("localhost", "localhost.localdomain"):
                    print(json.dumps({"error": "Invalid URL: Local and internal IPs are not allowed"}))
                    sys.exit(1)

                # Try parsing as IP directly, stripping brackets for IPv6 literals
                clean_hostname = hostname.strip("[]")
                try:
                    ip_obj = ipaddress.ip_address(clean_hostname)
                except ValueError:
                    # Resolve the hostname to an IP and check against private/loopback ranges
                    ip = socket.gethostbyname(hostname)
                    ip_obj = ipaddress.ip_address(ip)

                if ip_obj.is_private or ip_obj.is_loopback or ip_obj.is_link_local:
                    print(json.dumps({"error": "Invalid URL: Local and internal IPs are not allowed"}))
                    sys.exit(1)
            except (socket.gaierror, ValueError, Exception):
                # We do not block on resolution failure here, as the CLI will handle standard fetch errors.
                pass

            run_cmd(["source", "add", url, "-n", sys.argv[2]])
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
    except IndexError:
        print(json.dumps({"error": "Missing required arguments"}))
        sys.exit(1)
    except KeyboardInterrupt:
        print(json.dumps({"error": "Execution interrupted by user"}))
        sys.exit(1)
    except Exception:
        print(json.dumps({"error": "An unexpected error occurred during execution"}))
        sys.exit(1)
