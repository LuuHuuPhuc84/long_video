import os
import sys
import json
import time
import shutil
import io
import urllib.request
import urllib.error
import subprocess
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8', line_buffering=True)

BASE_DIR = Path(__file__).resolve().parent.parent
REMOTION_DIR = BASE_DIR / "remotion-video"
PUBLIC_DIR = REMOTION_DIR / "public"
OUTPUT_DIR = BASE_DIR / "output"
TOKEN_FILE = BASE_DIR / "pipeline" / "gdrive_token.json"

REPO_OWNER = "LuuHuuPhuc84"
REPO_NAME = "long_video"
API_BASE = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}"

def run_git(cmd_list, check=True):
    res = subprocess.run(["git"] + cmd_list, cwd=str(BASE_DIR), capture_output=True, text=True, encoding="utf-8")
    if check and res.returncode != 0:
        print(f"❌ Git error: {res.stderr.strip()}")
        raise RuntimeError(res.stderr.strip())
    return res.stdout.strip()

def get_json_api(url):
    headers = {
        "User-Agent": "Antigravity-Render-Client",
        "Accept": "application/vnd.github.v3+json"
    }
    gh_token = os.environ.get("GITHUB_TOKEN")
    if gh_token:
        headers["Authorization"] = f"Bearer {gh_token}"
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception:
        return None

def download_video_from_drive(video_id, target_path):
    """Tải video trực tiếp từ Google Drive về máy local nếu có token."""
    if not TOKEN_FILE.exists():
        return False
    try:
        from google.oauth2.credentials import Credentials
        from google.auth.transport.requests import Request
        from googleapiclient.discovery import build
        from googleapiclient.http import MediaIoBaseDownload

        with open(TOKEN_FILE, "r", encoding="utf-8") as f:
            token_data = json.load(f)

        creds = Credentials(
            None,
            refresh_token=token_data.get("refresh_token"),
            token_uri="https://oauth2.googleapis.com/token",
            client_id=token_data.get("client_id"),
            client_secret=token_data.get("client_secret"),
            scopes=['https://www.googleapis.com/auth/drive']
        )
        creds.refresh(Request())
        service = build('drive', 'v3', credentials=creds)

        # Tìm folder video_id
        q_folder = f"name='{video_id}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
        res_folder = service.files().list(q=q_folder, fields="files(id, name)").execute()
        folders = res_folder.get("files", [])
        if not folders:
            return False

        folder_id = folders[0]["id"]

        # Tìm file mp4 trong folder, ưu tiên bản tạo mới nhất
        q_file = f"'{folder_id}' in parents and name contains '.mp4' and trashed=false"
        res_files = service.files().list(
            q=q_file,
            fields="files(id, name, size, createdTime)",
            orderBy="createdTime desc"
        ).execute()
        files = res_files.get("files", [])
        if not files:
            return False

        # Luôn lấy file render mới nhất
        file_info = files[0]
        file_id = file_info["id"]
        size_mb = round(int(file_info.get("size", 0)) / (1024*1024), 2)

        print(f"⬇️ Đang tải video mới nhất từ Google Drive về máy ({file_info['name']} - {size_mb} MB)...")
        request = service.files().get_media(fileId=file_id)
        target_path.parent.mkdir(parents=True, exist_ok=True)
        with open(target_path, "wb") as f:
            downloader = MediaIoBaseDownload(f, request, chunksize=1024*1024*5)
            done = False
            while not done:
                status, done = downloader.next_chunk()
                if status:
                    print(f"   Tiến độ tải về: {int(status.progress() * 100)}%")

        print(f"✅ ĐÃ ĐỒNG BỘ VIDEO VỀ MÁY LOCAL: {target_path}")

        # Dọn dẹp các bản trùng lặp cũ trên Drive (nếu có file cũ sinh đuôi (1))
        if len(files) > 1:
            for old_f in files[1:]:
                try:
                    service.files().delete(fileId=old_f["id"]).execute()
                    print(f"   🧹 Đã dọn dẹp bản cũ trùng lặp trên Drive: {old_f['name']}")
                except:
                    pass
            # Đổi tên file mới nhất về chuẩn không có đuôi (1)
            if "(1)" in file_info["name"]:
                try:
                    clean_name = f"video_{video_id}.mp4"
                    service.files().update(fileId=file_id, body={"name": clean_name}).execute()
                    print(f"   🏷️ Đã đổi tên chuẩn trên Drive: {clean_name}")
                except:
                    pass
        return True
    except Exception as e:
        print(f"ℹ️ Không thể tự động tải từ Drive (sẽ dùng bản trực tiếp trên Cloud): {e}")
        return False

def render_long_video_via_github(video_id, auto_cleanup=True):
    print("========================================================")
    print(f"🎬 BẮT ĐẦU RENDER LONG VIDEO TRÊN GITHUB ACTIONS: {video_id}")
    print("☁️ Quy chuẩn: Render Cloud -> Đẩy Google Drive (Folder riêng + info.json)")
    print("✨ Bảo mật: Không lưu MP4/Release trên GitHub, tự động dọn sạch Git")
    print("========================================================")

    # 1. Kiểm tra file Metadata
    meta_path = PUBLIC_DIR / f"video_data_{video_id}.json"
    if not meta_path.exists():
        meta_path = PUBLIC_DIR / f"{video_id}.json"
    if not meta_path.exists():
        print(f"❌ Không tìm thấy file metadata: {meta_path}")
        return False

    with open(meta_path, "r", encoding="utf-8") as f:
        meta_data = json.load(f)

    # 2. Thu thập danh sách file cần thiết của riêng video này
    files_to_push = [meta_path]
    audio_file = meta_data.get("audioFile", "")
    if audio_file:
        audio_path = PUBLIC_DIR / audio_file
        if audio_path.exists():
            files_to_push.append(audio_path)
        else:
            print(f"⚠️ Cảnh báo: Không thấy audio {audio_path}")

    # Thu thập B-roll / Images từ scenes
    scenes = meta_data.get("scenes", [])
    for sc in scenes:
        bg = sc.get("image") or sc.get("backgroundVideo") or sc.get("video")
        if bg:
            bg_path = PUBLIC_DIR / bg
            if bg_path.exists() and bg_path not in files_to_push:
                files_to_push.append(bg_path)

    # Đính kèm info.json nếu đã có sẵn ở local
    local_info = OUTPUT_DIR / video_id / "info.json"
    if local_info.exists() and local_info not in files_to_push:
        files_to_push.append(local_info)

    # Đính kèm Thumbnail chuyên biệt nếu có ở local
    local_thumb = OUTPUT_DIR / video_id / f"thumbnail_{video_id}.jpg"
    if not local_thumb.exists():
        for tf in (OUTPUT_DIR / video_id).glob("thumbnail*.*"):
            local_thumb = tf
            break
    if local_thumb and local_thumb.exists() and local_thumb not in files_to_push:
        files_to_push.append(local_thumb)

    print(f"📦 Các file nguyên liệu cần đưa lên ({len(files_to_push)} files):")
    for fp in files_to_push:
        print(f"   - {fp.name} ({round(fp.stat().st_size / (1024*1024), 2)} MB)")

    # 3. Đóng gói và push thẳng lên branch render trên GitHub (Zero-switch)
    branch_name = f"render-{video_id}"
    print(f"\n📦 Đang đóng gói nguyên liệu và chuẩn bị đẩy lên nhánh: {branch_name}...")
    rel_paths = [str(fp.relative_to(BASE_DIR)).replace("\\", "/") for fp in files_to_push]
    run_git(["add", "-f"] + rel_paths)
    run_git(["commit", "-m", f"render: upload assets for {video_id}"])

    head_sha = run_git(["rev-parse", "HEAD"])
    print(f"🚀 Đang đẩy nguyên liệu lên GitHub (Commit: {head_sha[:7]})...")
    run_git(["push", "-f", "origin", f"HEAD:refs/heads/{branch_name}"])
    print(f"✓ Đã đẩy nhánh {branch_name} lên GitHub thành công!")

    # 4. Trả lại trạng thái commit ban đầu cho Local (giữ nguyên 100% file nguyên liệu trên máy)
    run_git(["reset", "HEAD~1"])
    print(f"🔒 Local đã được giữ nguyên vẹn trên 'main', không bị mất file.")

    # 5. Theo dõi tiến trình GitHub Actions
    print(f"\n⏳ Đang đợi GitHub Actions nhận lệnh và bắt đầu render...")
    print(f"🔗 Xem trực tiếp tại: https://github.com/{REPO_OWNER}/{REPO_NAME}/actions")

    start_time = time.time()
    last_status = ""
    completed = False
    success = False

    while not completed:
        time.sleep(15)
        elapsed = int(time.time() - start_time)

        runs_data = get_json_api(f"{API_BASE}/actions/runs?branch={branch_name}")
        if runs_data and runs_data.get("workflow_runs"):
            latest_run = runs_data["workflow_runs"][0]
            status = latest_run.get("status")
            conclusion = latest_run.get("conclusion")

            if status != last_status:
                print(f"   [{elapsed}s] Trạng thái: {status} (Đang render & tải lên Drive)...")
                last_status = status

            if status == "completed":
                completed = True
                success = (conclusion == "success")
                break

        if elapsed > 2400:  # 40 phút timeout cho long video
            print("❌ Quá thời gian chờ (40 phút).")
            return False

    if success:
        print(f"\n🎉 RENDER & ĐẨY LÊN GOOGLE DRIVE THÀNH CÔNG! (Thời gian: {elapsed}s)")
    else:
        print(f"\n❌ GitHub Actions hoàn tất nhưng kết quả thất bại! Hãy kiểm tra log tại GitHub Actions.")

    # 6. Đồng bộ video từ Google Drive về máy Local (nếu có thể)
    out_video_file = OUTPUT_DIR / str(video_id) / f"video_{video_id}.mp4"
    if success:
        download_video_from_drive(video_id, out_video_file)

    # 7. Dọn dẹp trên Git (Xóa sạch branch tạm trên GitHub)
    if auto_cleanup:
        print(f"\n🧹 Đang xóa sạch nhánh tạm '{branch_name}' trên GitHub...")
        try:
            run_git(["push", "origin", "--delete", branch_name], check=False)
            run_git(["branch", "-D", branch_name], check=False)
            print(f"✨ ĐÃ XÓA SẠCH DẤU VẾT TRÊN GITHUB! Repo trở lại trạng thái khung rỗng sạch sẽ.")
            print(f"🛡️ Không có file MP4 hay Release nào được lưu trữ trên GitHub.")
        except Exception as e:
            print(f"⚠️ Dọn dẹp branch gặp lỗi nhẹ: {e}")

    print("\n========================================================")
    print(f"🏁 HOÀN TẤT TOÀN BỘ QUY TRÌNH CHO: {video_id}")
    print("========================================================")
    return success

if __name__ == "__main__":
    vid = sys.argv[1] if len(sys.argv) > 1 else "essay_ep01"
    render_long_video_via_github(vid)
