"""Run one research script through the installed official, sandboxed Resolve MCP."""
import json
from pathlib import Path
import queue
import subprocess
import sys
import threading
import time

script_path, output_path = map(Path, sys.argv[1:3])
messages = queue.Queue()
received = []
process = subprocess.Popen(
    [r"G:\Davinci Studio\ResolveMCP.exe"],
    stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    text=True, encoding="utf8", creationflags=subprocess.CREATE_NO_WINDOW,
)

def read_stdout():
    for line in process.stdout:
        messages.put(json.loads(line))

stderr = []
threading.Thread(target=read_stdout, daemon=True).start()
stderr_thread = threading.Thread(target=lambda: stderr.extend(process.stderr.readlines()), daemon=True)
stderr_thread.start()

def send(value):
    process.stdin.write(json.dumps(value) + "\n")
    process.stdin.flush()

def request(ident, method, params):
    send({"jsonrpc": "2.0", "id": ident, "method": method, "params": params})
    deadline = time.monotonic() + 65
    while time.monotonic() < deadline:
        try:
            message = messages.get(timeout=deadline - time.monotonic())
        except queue.Empty:
            raise TimeoutError(method) from None
        received.append(message)
        if message.get("id") != ident:
            continue
        if "error" in message or message.get("result", {}).get("isError"):
            raise RuntimeError("MCP call failed; inspect the private response file")
        for block in message.get("result", {}).get("content", []):
            if block.get("type") != "text":
                continue
            try:
                value = json.loads(block["text"])
            except ValueError:
                continue
            if isinstance(value, dict) and "error" in value:
                raise RuntimeError("Resolve script failed; inspect the private response file")
        return message
    raise TimeoutError(method)

try:
    request(1, "initialize", {"protocolVersion": "2024-11-05", "capabilities": {}, "clientInfo": {"name": "resolve-exposure-research", "version": "0.1"}})
    send({"jsonrpc": "2.0", "method": "notifications/initialized"})
    response = request(2, "tools/call", {"name": "run_script", "arguments": {"script": script_path.read_text(encoding="utf8"), "timeout": 60}})
    value = json.loads(response["result"]["content"][0]["text"])
    if not isinstance(value, dict) or not isinstance(value.get("result"), dict):
        raise RuntimeError("Resolve response lacks a result object; inspect the private response file")
    print(json.dumps({"script_succeeded": True, "result_keys": list(value["result"])}, ensure_ascii=False))
finally:
    process.stdin.close()
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.terminate()
        process.wait(timeout=5)
    stderr_thread.join(timeout=1)
    output_path.write_text(json.dumps(received, ensure_ascii=False, indent=2), encoding="utf8")
    output_path.with_suffix(".stderr.txt").write_text("".join(stderr), encoding="utf8")
