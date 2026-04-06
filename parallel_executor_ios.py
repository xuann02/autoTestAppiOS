import subprocess
import threading
import time
import os

# ================= CONFIGURATION =================
# BƯỚC 1: ĐIỀN UDID THẬT CỦA BẠN VÀO ĐÂY
DEVICE_IOS_1 = "28637C8C-EED7-4D48-ACC7-4B4A332F3E0D"
DEVICE_IOS_2 = "28225DE3-858A-49E3-8739-518B19980592"

APPS_IOS_DEVICE_1 = ["com.abc.ccna"]
APPS_IOS_DEVICE_2 = ["com.abc.cna"]

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
GUARDIAN_IOS_PATH = os.path.join(SCRIPT_DIR, "maestro_guardian_ios.py")

def run_ios_apps(device_id, app_list, delay=0):
    """Chạy app với cơ chế delay start để tránh xung đột driver."""
    if delay > 0:
        print(f"[MANAGER] ⏳ Chờ {delay}s cho thiết bị {device_id} khởi động sau...")
        time.sleep(delay)

    for app_id in app_list:
        print(f"\n[IOS-MANAGER] >>> Test {app_id} trên {device_id}...")
        cmd = f"python3 \"{GUARDIAN_IOS_PATH}\" {app_id} {device_id}"
        subprocess.run(cmd, shell=True)
        time.sleep(5)

if __name__ == "__main__":
    print("🚀 Khởi chạy hệ thống iOS Parallel (Đã fix xung đột Port)...")

    # Thread 1: Chạy ngay lập tức
    t1 = threading.Thread(target=run_ios_apps, args=(DEVICE_IOS_1, APPS_IOS_DEVICE_1, 0))
    
    # Thread 2: Chờ 15 giây mới bắt đầu (Cực kỳ quan trọng cho iOS)
    t2 = threading.Thread(target=run_ios_apps, args=(DEVICE_IOS_2, APPS_IOS_DEVICE_2, 15))

    t1.start()
    t2.start()

    t1.join()
    t2.join()

    print("\n✅ TẤT CẢ SIMULATOR ĐÃ HOÀN THÀNH.")
