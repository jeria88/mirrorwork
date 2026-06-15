import subprocess
import json
import os
import sys

def run_mcp_command():
    # Start the MCP server process
    env = os.environ.copy()
    env["API_KEY"] = "ebd8c47fb34b7bffb72effd02a9bb05b41719dc1adbfc3d74d4266153d234960"
    
    proc = subprocess.Popen(
        ["npx", "-y", "@21st-dev/magic@latest"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
        env=env
    )
    
    def send_request(method, params=None, req_id=1):
        req = {
            "jsonrpc": "2.0",
            "id": req_id,
            "method": method
        }
        if params is not None:
            req["params"] = params
        
        proc.stdin.write(json.dumps(req) + "\n")
        proc.stdin.flush()
        
        # Read lines from stdout until we get a valid JSON response matching the id
        while True:
            line = proc.stdout.readline()
            if not line:
                break
            try:
                resp = json.loads(line)
                # Ignore notifications or logging messages
                if resp.get("id") == req_id:
                    return resp
                else:
                    # Print logs for visibility
                    if "method" in resp and resp["method"] == "window/logMessage":
                        print(f"[Log] {resp['params']['message']}", file=sys.stderr)
            except Exception:
                pass
        return None

    # 1. Initialize
    init_params = {
        "protocolVersion": "2024-11-05",
        "capabilities": {},
        "clientInfo": {"name": "Antigravity", "version": "1.0.0"}
    }
    init_resp = send_request("initialize", init_params, 1)
    
    # Send initialized notification
    proc.stdin.write(json.dumps({
        "jsonrpc": "2.0",
        "method": "notifications/initialized"
    }) + "\n")
    proc.stdin.flush()

    # 2. List tools
    tools_resp = send_request("tools/list", None, 2)
    print(json.dumps(tools_resp, indent=2, ensure_ascii=False))

    # Terminate the process cleanly
    proc.terminate()

if __name__ == "__main__":
    run_mcp_command()
