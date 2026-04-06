import subprocess
import os
import requests
import re
import glob
import shutil
import argparse
import time

# ================= CONFIGURATION =================
WEBHOOK_URL = "https://discord.com/api/webhooks/1488793084434317332/CnGZdQrzLbLuSFd5eGpsZuOt8LlDD78AbHGND0hQ1r5vmI4qa9gQnBZ5IPeboZMx9ayt"

def get_unique_port(device_id):
    """Tạo port riêng biệt cho từng Simulator (VD: 8001, 8002...)"""
    try:
        last_chars = "".join(filter(str.isdigit, device_id))[-3:]
        return 8000 + (int(last_chars) % 500) if last_chars else 8001
    except:
        return 8001

def prepare_dirs(device_id):
    safe_name = device_id.replace("-", "_")
    output_dir = os.path.abspath(f"outputs_ios/{safe_name}")
    debug_dir = os.path.abspath(f"debug_ios/{safe_name}")
    for d in [output_dir, debug_dir]:
        if os.path.exists(d):
            shutil.rmtree(d)
        os.makedirs(d, exist_ok=True)
    return output_dir, debug_dir

def run_maestro_ios(app_id, device_id):
    output_dir, debug_dir = prepare_dirs(device_id)
    driver_port = get_unique_port(device_id)

    print(f"🍎 [iOS-{device_id[:8]}] Khởi chạy với Port: {driver_port}")

    # Dọn dẹp driver cũ
    subprocess.run(f"maestro --device {device_id} stop", shell=True, capture_output=True)
    time.sleep(2)

    # THIẾT LẬP PORT QUA BIẾN MÔI TRƯỜNG
    env = os.environ.copy()
    env["MAESTRO_DRIVER_PORT"] = str(driver_port)

    command = (
        f"maestro --device {device_id} test "
        f"-e APP_ID={app_id} "
        f"-e DEVICE_ID={device_id} "
        f"--test-output-dir {output_dir} "
        f"--debug-output {debug_dir} "
        f"--flatten-debug-output "
        f"run_once.yaml"
    )

    process = subprocess.Popen(
        command,
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        env=env
    )

    while True:
        line = process.stdout.readline()
        if not line:
            break
        print(f"[iOS-{device_id[:8]}] {line}", end="")

    process.wait()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("app_id")
    parser.add_argument("device_id")
    args = parser.parse_args()

    run_maestro_ios(args.app_id, args.device_id)
