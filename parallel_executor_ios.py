import subprocess
import threading
import time
import os

# ================= CONFIGURATION =================
# Danh sách Bundle ID cho Simulator 1
APPS_IOS_DEVICE_1 = [
    "com.abc.ccna"
]

# Danh sách Bundle ID cho Simulator 2
APPS_IOS_DEVICE_2 = [
    "com.abc.cna"
]

# Thay thế bằng UDID thật của bạn (lấy từ lệnh: xcrun simctl list devices)
DEVICE_IOS_1 = "53A96484-342B-49DD-86B9-89BEBF4EA2DD"
DEVICE_IOS_2 = "28637C8C-EED7-4D48-ACC7-4B4A332F3E0D"

# Lấy đường dẫn tuyệt đối của file guardian iOS
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
GUARDIAN_IOS_PATH = os.path.join(SCRIPT_DIR, "maestro_guardian_ios.py")
# =================================================

def run_ios_apps(device_id, app_list):
    """Chạy lần lượt các app iOS trong danh sách trên một Simulator cụ thể."""
    if device_id == "53A96484-342B-49DD-86B9-89BEBF4EA2DD" or device_id == "28637C8C-EED7-4D48-ACC7-4B4A332F3E0D":
        print(f"\n[⚠️ WARNING] Bạn chưa thay UDID cho thiết bị {device_id}!")
        return

    for app_id in app_list:
        print(f"\n[IOS-MANAGER] >>> Bắt đầu test {app_id} trên {device_id}...")
        
        # Gọi guardian chuyên cho iOS
        cmd = f"python3 \"{GUARDIAN_IOS_PATH}\" {app_id} {device_id}"
        
        try:
            # Chạy và đợi cho đến khi hoàn thành app hiện tại
            subprocess.run(cmd, shell=True, check=True)
        except subprocess.CalledProcessError:
            print(f"[IOS-MANAGER] ❌ Lỗi khi chạy {app_id} trên {device_id}. Tiếp tục app tiếp theo...")
        
        print(f"[IOS-MANAGER] <<< Kết thúc test {app_id} trên {device_id}.")
        time.sleep(5) # Nghỉ 5s giữa các app để Simulator ổn định

if __name__ == "__main__":
    print("🚀 Khởi chạy hệ thống test song song trên 2 Simulator iOS...")
    print(f"📂 Guardian iOS path: {GUARDIAN_IOS_PATH}")
    print(f"📱 Simulator 1 ({DEVICE_IOS_1}): {len(APPS_IOS_DEVICE_1)} apps")
    print(f"📱 Simulator 2 ({DEVICE_IOS_2}): {len(APPS_IOS_DEVICE_2)} apps")

    # Tạo 2 luồng để chạy song song
    thread1 = threading.Thread(target=run_ios_apps, args=(DEVICE_IOS_1, APPS_IOS_DEVICE_1))
    thread2 = threading.Thread(target=run_ios_apps, args=(DEVICE_IOS_2, APPS_IOS_DEVICE_2))

    thread1.start()
    thread2.start()

    thread1.join()
    thread2.join()

    print("\n✅ TẤT CẢ SIMULATOR ĐÃ HOÀN THÀNH TEST LIST.")
