import subprocess, sys, json, time

proc = subprocess.Popen(
    [sys.executable, "-u", "coalition_mcp_server.py"],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE
)

# Send MCP initialize request
init_request = (json.dumps({
    "jsonrpc": "2.0",
    "id": 1,
    "method": "initialize",
    "params": {
        "protocolVersion": "2024-11-05",
        "capabilities": {},
        "clientInfo": {"name": "test", "version": "1.0"}
    }
}) + "\n").encode()

proc.stdin.write(init_request)
proc.stdin.flush()
proc.stdin.close()

try:
    stdout, stderr = proc.communicate(timeout=10)
except subprocess.TimeoutExpired:
    proc.kill()
    stdout, stderr = proc.communicate()

print("=== STDOUT ===")
print(repr(stdout))
print("=== STDERR ===")
print(repr(stderr))
print("=== RETURN CODE ===")
print(proc.returncode)
