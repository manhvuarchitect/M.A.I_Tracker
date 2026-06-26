import os
import shutil
import subprocess
import sys

# 3 file cốt lõi cần bảo mật
FILES_TO_PROTECT = [
    "custom_components/mai_tracker/coordinator.py",
    "custom_components/mai_tracker/utils/caffeine_calc.py",
    "custom_components/mai_tracker/utils/alcohol_calc.py",
]

BACKUP_DIR = ".private_backup"

def print_banner():
    print("=" * 60)
    print("        M.A.I TRACKER - SECURE DEPLOY TOOL v1.0")
    print("=" * 60)

def backup_files():
    if os.path.exists(BACKUP_DIR):
        shutil.rmtree(BACKUP_DIR)
    os.makedirs(BACKUP_DIR, exist_ok=True)
    
    print("[1/5] Đang sao lưu mã nguồn sạch vào thư mục ẩn...")
    for rel_path in FILES_TO_PROTECT:
        if not os.path.exists(rel_path):
            print(f"❌ Lỗi: Không tìm thấy file {rel_path}")
            sys.exit(1)
        
        # Tạo đường dẫn thư mục đích nếu chưa có
        dest_path = os.path.join(BACKUP_DIR, os.path.basename(rel_path))
        shutil.copy2(rel_path, dest_path)
        print(f"  -> Đã sao lưu: {rel_path} -> {dest_path}")
    print("✅ Đã sao lưu hoàn tất và an toàn.")

def restore_files():
    print("[5/5] Đang khôi phục lại mã nguồn sạch để phát triển tiếp...")
    for rel_path in FILES_TO_PROTECT:
        backup_file = os.path.join(BACKUP_DIR, os.path.basename(rel_path))
        if os.path.exists(backup_file):
            shutil.copy2(backup_file, rel_path)
            print(f"  -> Đã khôi phục: {rel_path}")
        else:
            print(f"⚠️ Cảnh báo: Không tìm thấy file sao lưu cho {rel_path}")
    
    # Dọn dẹp thư mục tạm
    if os.path.exists(BACKUP_DIR):
        shutil.rmtree(BACKUP_DIR)
    print("✅ Đã khôi phục và dọn dẹp thư mục tạm.")

def run_git_commands(commit_msg, tag_version=None):
    print("[3/5] Đang thêm và commit các file đã mã hóa...")
    try:
        # Git add
        subprocess.run(["git", "add", "."], check=True)
        
        # Git commit
        subprocess.run(["git", "commit", "-m", commit_msg], check=True)
        print("✅ Đã commit thành công.")
        
        # Git tag (nếu có)
        if tag_version:
            print(f"[4/5] Đang tạo tag phiên bản: {tag_version}...")
            # Xóa tag cũ nếu trùng tên cục bộ
            subprocess.run(["git", "tag", "-d", tag_version], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            subprocess.run(["git", "tag", tag_version], check=True)
            print(f"✅ Đã tạo tag {tag_version}.")
            
            print("🛫 Đang push mã nguồn đã mã hóa và tag lên GitHub...")
            subprocess.run(["git", "push", "origin", "main", "--tags"], check=True)
        else:
            print("🛫 Đang push mã nguồn đã mã hóa lên GitHub...")
            subprocess.run(["git", "push", "origin", "main"], check=True)
            
        print("✅ Đẩy lên GitHub thành công!")
    except subprocess.CalledProcessError as e:
        print(f"❌ Lỗi thực thi Git: {e}")
        print("⚠️ Tiến trình đẩy Git thất bại nhưng file nguồn gốc vẫn sẽ được khôi phục.")
        raise e

def main():
    print_banner()
    
    # Bước 1: Sao lưu các file gốc
    backup_files()
    
    # Thao tác bọc trong try-finally để luôn khôi phục lại file gốc ngay cả khi có lỗi xảy ra giữa chừng
    try:
        print("\n" + "="*50)
        print("👉 BƯỚC 2: TIẾN HÀNH MÃ HÓA CODE")
        print("  1. Hãy tiến hành mã hóa 3 file sau bằng công cụ băm code của bạn:")
        for f in FILES_TO_PROTECT:
            print(f"     - {f}")
        print("  2. Sau khi đã chạy mã hóa xong thành công trên 3 file trên:")
        print("     Hãy quay lại đây và nhấn phím ENTER để tiếp tục...")
        print("="*50)
        input()
        
        # Hỏi commit message
        commit_msg = input("\n📝 Nhập thông điệp commit (Commit Message) [Mặc định: 'deploy: push secure obfuscated code']: ").strip()
        if not commit_msg:
            commit_msg = "deploy: push secure obfuscated code"
            
        # Hỏi tag version
        tag_version = input("🏷️ Nhập tag phiên bản cần tạo (ví dụ: v2.2.11) [Để trống nếu không tạo tag]: ").strip()
        if not tag_version:
            tag_version = None
            
        # Chạy Git push
        run_git_commands(commit_msg, tag_version)
        
    except KeyboardInterrupt:
        print("\n\n⚠️ Tiến trình bị hủy bởi người dùng.")
    finally:
        # Bước cuối: Luôn khôi phục lại mã nguồn sạch để phát triển tiếp
        restore_files()
        print("\n" + "="*60)
        print("🎉 QUY TRÌNH HOÀN TẤT. BẠN CÓ THỂ TIẾP TỤC CODE FILE GỐC!")
        print("="*60)

if __name__ == "__main__":
    main()
