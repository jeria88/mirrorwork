import subprocess
import json
import os
import sys

def call_mcp(tool_name, arguments):
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
        
        while True:
            line = proc.stdout.readline()
            if not line:
                break
            try:
                resp = json.loads(line)
                if resp.get("id") == req_id:
                    return resp
                else:
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
    send_request("initialize", init_params, 1)
    
    proc.stdin.write(json.dumps({
        "jsonrpc": "2.0",
        "method": "notifications/initialized"
    }) + "\n")
    proc.stdin.flush()

    # 2. Call tool
    call_params = {
        "name": tool_name,
        "arguments": arguments
    }
    call_resp = send_request("tools/call", call_params, 2)
    proc.terminate()
    return call_resp

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python3 call_magic_mcp.py <tool_name> <arguments_json_string>", file=sys.stderr)
        sys.exit(1)
        
    tool_name = sys.argv[1]
    try:
        arguments = json.loads(sys.argv[2])
    except Exception as e:
        print(f"Error parsing JSON arguments: {e}", file=sys.stderr)
        sys.exit(1)
        
    response = call_mcp(tool_name, arguments)
    print(json.dumps(response, indent=2, ensure_ascii=False))
