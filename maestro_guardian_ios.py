import subprocess
import os
import requests
import json
import re
import glob
import shutil
import sys
import argparse
import time
from datetime import datetime

# ================= CONFIGURATION =================
# 1. Cấu hình Discord Webhook
WEBHOOK_URL = "https://discord.com/api/webhooks/1488793084434317332/CnGZdQrzLbLuSFd5eGpsZuOt8LlDD78AbHGND0hQ1r5vmI4qa9gQnBZ5IPeboZMx9ayt"
# =================================================

def get_safe_name(device_id):
    """Chuyển ID thiết bị thành tên thư mục hợp lệ (dành cho iOS UDID)."""
    return device_id.replace(":", "_").replace("-", "_").replace(".", "_")

def get_unique_port(device_id):
    """Tạo một cổng driver duy nhất dựa trên device_id cho iOS."""
    # Vì iOS UDID là chuỗi dài, chúng ta hash hoặc lấy các ký tự cuối
    try:
        # Lấy 4 ký tự cuối và chuyển thành số
        last_chars = "".join(filter(str.isdigit, device_id))[-4:]
        if last_chars:
            return 8000 + (int(last_chars) % 1000)
    except:
        pass
    return 8001

def prepare_dirs(device_id):
    """Chuẩn bị các thư mục riêng biệt cho từng thiết bị iOS."""
    safe_name = get_safe_name(device_id)
    output_dir = os.path.abspath(f"outputs_ios/{safe_name}")
    debug_dir = os.path.abspath(f"debug_ios/{safe_name}")
    
    for d in [output_dir, debug_dir]:
        if os.path.exists(d):
            shutil.rmtree(d)
        os.makedirs(d, exist_ok=True)
    return output_dir, debug_dir

def classify_error(output):
    """Phân loại lỗi dựa trên log output của iOS."""
    if "Wait for" in output and "timed out" in output:
        return "⏳ TIMEOUT ERROR", "Hệ thống/Ứng dụng phản hồi chậm (iOS)."
    elif "Assertion failed" in output or "Assertion error" in output:
        return "🐞 BUG DETECTED", "Điều kiện kiểm tra không khớp (Assertion)."
    elif "Element not found" in output or "Could not find" in output:
        return "🔍 UI/LOCATOR CHANGED", "Không tìm thấy phần tử UI trên iOS."
    elif "App not installed" in output or "bundle id" in output.lower():
        return "📦 APP NOT FOUND", "Bundle ID không tồn tại trên Simulator này."
    return "⚠️ UNKNOWN FAILURE", "Lỗi không xác định trên iOS."

def send_notification(message, image_path=None):
    """Gửi thông báo qua Discord Webhook."""
    if WEBHOOK_URL and "discord.com" in WEBHOOK_URL:
        try:
            requests.post(WEBHOOK_URL, json={"content": message}, timeout=10)
            if image_path and os.path.exists(image_path):
                with open(image_path, 'rb') as f:
                    requests.post(WEBHOOK_URL, files={'file': f}, timeout=10)
            print(f"✅ Đã gửi báo cáo iOS lên Discord.")
        except Exception as e:
            print(f"Lỗi Discord iOS: {e}")

def run_maestro_ios(app_id, device_id):
    output_dir, debug_dir = prepare_dirs(device_id)
    driver_port = get_unique_port(device_id)
    
    print(f"🍎 Maestro Guardian [iOS] - CÔ LẬP HOÀN TOÀN:")
    print(f"📱 Simulator UDID: {device_id}")
    print(f"🆔 Bundle ID: {app_id}")
    print(f"🔌 Driver Port: {driver_port}")
    
    # 1. Dọn dẹp Maestro cũ trên thiết bị iOS này
    print(f"🧹 Đang dừng Maestro driver cũ trên {device_id}...")
    subprocess.run(f"maestro --device {device_id} stop", shell=True, capture_output=True)
    time.sleep(2)

    # 2. Thiết lập biến môi trường (Không dùng ANDROID_SERIAL)
    env = os.environ.copy()
    
    # Lệnh Maestro sử dụng tham số --driver-host-port để cô lập driver hoàn toàn
    command = (
        f"maestro --driver-host-port {driver_port} --device {device_id} test "
        f"-e APP_ID={app_id} "
        f"-e DEVICE_ID={device_id} "
        f"--test-output-dir {output_dir} "
        f"--debug-output {debug_dir} "
        f"--flatten-debug-output "
        f"run_once.yaml"
    )
    
    process = subprocess.Popen(
        command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, env=env
    )

    full_output = []
    flow_results = []
    current_flow = None
    
    flow_pattern = re.compile(r"Running\s+(.*\.yaml)")

    while True:
        line = process.stdout.readline()
        if not line: break
        print(f"[iOS-{device_id[:8]}] {line}", end="")
        full_output.append(line)
        
        flow_match = flow_pattern.search(line)
        if flow_match:
            current_flow = flow_match.group(1).split("/")[-1]
            
        if "✅" in line and current_flow:
            if current_flow != "run_once.yaml" and current_flow != "appModul.yaml":
                flow_results.append(f"✅ `{current_flow}`: PASS")
            current_flow = None
        elif "❌" in line and current_flow:
            flow_results.append(f"❌ `{current_flow}`: FAILED")
            current_flow = None

        if "✅ runFlow appModul.yaml" in line:
            summary = "\n".join(flow_results)
            msg = (
                f"🍎 **APP TEST PASSED (iOS)**\n"
                f"🆔 **Bundle ID:** `{app_id}`\n"
                f"📱 **Simulator:** `{device_id}`\n"
                f"📊 **Results:**\n{summary}"
            )
            send_notification(msg)
            flow_results = []

    process.wait()
    output_str = "".join(full_output)

    if process.returncode != 0:
        print(f"\n❌ iOS {device_id} kết thúc với lỗi!")
        category, explanation = classify_error(output_str)
        
        screenshots = glob.glob(f"{debug_dir}/*.png")
        screenshots += glob.glob(f"{output_dir}/*.png")
        latest_screenshot = max(screenshots, key=os.path.getctime) if screenshots else None

        summary = "\n".join(flow_results) if flow_results else "Lỗi xảy ra ngay từ đầu trên iOS."
        message = (
            f"🍎 **APP TEST FAILED (iOS)**\n"
            f"🆔 **Bundle ID:** `{app_id}`\n"
            f"📱 **Simulator:** `{device_id}`\n\n"
            f"📊 **Status:**\n{summary}\n\n"
            f"🛑 **Category:** {category}\n"
            f"💡 **Detail:** {explanation}\n"
            f"📝 **Last Log:**\n```\n{''.join(full_output[-5:])}\n```"
        )
        send_notification(message, latest_screenshot)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Maestro Guardian iOS - Run automation for iOS.")
    parser.add_argument("app_id", help="The bundle ID of the app (e.g., com.abc.part)")
    parser.add_argument("device_id", help="The UDID of the iOS Simulator (e.g., 5B6B...)")
    
    args = parser.parse_args()
    run_maestro_ios(args.app_id, args.device_id)
