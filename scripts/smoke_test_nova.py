import os
import sys

# Ensure layer is importable
sys.path.insert(0, os.path.abspath("backend/layer/python"))
from common.nova import converse


def main():
    print("[*] Testing Amazon Nova Lite connectivity via Bedrock Converse...")
    messages = [{"role": "user", "content": [{"text": "Hello, respond with 'OK'."}]}]
    try:
        resp = converse(messages=messages, system="You are an automated smoke test.", max_tokens=10)
        output_text = resp.get("output", {}).get("message", {}).get("content", [{}])[0].get("text", "")
        model_id = os.environ.get("NOVA_MODEL_ID", "amazon.nova-lite-v1:0")
        print(f"[+] Successfully connected to Bedrock!")
        print(f"    Model ID: {model_id}")
        print(f"    Response: {output_text.strip()}")
    except Exception as e:
        print(f"[!] Smoke test failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
