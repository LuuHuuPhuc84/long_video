import os
import sys
import json
import io
from pathlib import Path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseUpload

sys.stdout.reconfigure(encoding='utf-8')

def get_drive_credentials():
    # 1. Ưu tiên OAuth Credentials của tài khoản cá nhân (dung lượng cá nhân, không bị hạn mức 0)
    client_id = os.environ.get("GDRIVE_CLIENT_ID")
    client_secret = os.environ.get("GDRIVE_CLIENT_SECRET")
    refresh_token = os.environ.get("GDRIVE_REFRESH_TOKEN")

    if client_id and client_secret and refresh_token:
        print("🔑 Sử dụng Google OAuth 2.0 Credentials (Tài khoản Google cá nhân)...")
        creds = Credentials(
            None,
            refresh_token=refresh_token,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=client_id,
            client_secret=client_secret,
            scopes=['https://www.googleapis.com/auth/drive']
        )
        creds.refresh(Request())
        return creds

    # 2. Dự phòng: Service Account Key (Dành cho Google Workspace Shared Drive)
    sa_json = os.environ.get("GDRIVE_SA_KEY")
    if sa_json:
        print("🔑 Sử dụng Google Service Account Key...")
        service_account_info = json.loads(sa_json)
        return service_account.Credentials.from_service_account_info(
            service_account_info, scopes=['https://www.googleapis.com/auth/drive']
        )

    print("❌ Không tìm thấy thông tin xác thực Google Drive (cần GDRIVE_CLIENT_ID/GDRIVE_CLIENT_SECRET/GDRIVE_REFRESH_TOKEN hoặc GDRIVE_SA_KEY).")
    sys.exit(1)

def create_drive_folder(drive_service, folder_name, parent_id):
    """Tạo hoặc lấy subfolder trên Google Drive theo tên."""
    query = f"name='{folder_name}' and '{parent_id}' in parents and mimeType='application/vnd.google-apps.folder' and trashed=false"
    results = drive_service.files().list(q=query, fields="files(id, name)", supportsAllDrives=True).execute()
    existing = results.get('files', [])
    if existing:
        folder_id = existing[0]['id']
        print(f"📁 Subfolder đã tồn tại: {folder_name} (ID: {folder_id})")
        return folder_id

    folder_metadata = {
        'name': folder_name,
        'mimeType': 'application/vnd.google-apps.folder',
        'parents': [parent_id]
    }
    folder = drive_service.files().create(body=folder_metadata, fields='id', supportsAllDrives=True).execute()
    folder_id = folder.get('id')
    print(f"📁 Đã tạo subfolder mới: {folder_name} (ID: {folder_id})")
    return folder_id

def upload_file_to_folder(drive_service, file_path, folder_id, mimetype='video/mp4'):
    """Upload file nhị phân vào thư mục trên Drive."""
    path = Path(file_path)
    file_metadata = {
        'name': path.name,
        'parents': [folder_id]
    }
    media = MediaFileUpload(str(path), mimetype=mimetype, resumable=True)
    size_mb = round(path.stat().st_size / 1024 / 1024, 2)
    print(f"☁️ Đang tải {path.name} ({size_mb} MB) vào Google Drive...")

    request = drive_service.files().create(
        body=file_metadata,
        media_body=media,
        fields='id, webViewLink',
        supportsAllDrives=True
    )
    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            print(f"   Tiến độ: {int(status.progress() * 100)}%")
    return response

def upload_json_to_folder(drive_service, json_data, filename, folder_id):
    """Upload dữ liệu JSON vào thư mục trên Drive."""
    json_bytes = json.dumps(json_data, ensure_ascii=False, indent=2).encode('utf-8')
    file_metadata = {
        'name': filename,
        'parents': [folder_id]
    }
    media = MediaIoBaseUpload(io.BytesIO(json_bytes), mimetype='application/json', resumable=False)
    result = drive_service.files().create(
        body=file_metadata,
        media_body=media,
        fields='id, webViewLink',
        supportsAllDrives=True
    ).execute()
    print(f"📄 Đã tải file mô tả {filename} lên Drive (ID: {result.get('id')})")
    return result

def upload_video_to_gdrive(file_path, parent_folder_id):
    path = Path(file_path)
    if not path.exists():
        print(f"❌ Không tìm thấy file: {file_path}")
        sys.exit(1)

    video_id = path.parent.name
    creds = get_drive_credentials()

    try:
        drive_service = build('drive', 'v3', credentials=creds)

        # 1. Tạo thư mục riêng cho video trên Google Drive
        print(f"\n========================================================")
        print(f"📂 TẠO THƯ MỤC DRIVE CHO VIDEO: {video_id}")
        print(f"========================================================")
        subfolder_id = create_drive_folder(drive_service, video_id, parent_folder_id)

        # 2. Upload video MP4 vào thư mục riêng
        video_response = upload_file_to_folder(drive_service, file_path, subfolder_id, 'video/mp4')
        print(f"✅ VIDEO ĐÃ LÊN GOOGLE DRIVE THÀNH CÔNG!")
        print(f"   📁 File ID: {video_response.get('id')}")
        print(f"   🔗 Link xem video: {video_response.get('webViewLink')}")

        # 3. Tìm hoặc tự sinh file info.json chứa tiêu đề, mô tả, hashtag
        info_data = None
        possible_info_files = [
            path.parent / "info.json",
            Path("output") / video_id / "info.json",
            Path("remotion-video") / "output" / video_id / "info.json"
        ]
        for inf in possible_info_files:
            if inf.exists():
                try:
                    with open(inf, 'r', encoding='utf-8') as f:
                        info_data = json.load(f)
                    print(f"✓ Đã nạp thông tin từ: {inf}")
                    break
                except Exception as e:
                    print(f"⚠️ Đọc file {inf} thất bại: {e}")

        if not info_data:
            # Tự động trích xuất từ metadata video_data
            possible_meta_files = [
                Path("remotion-video") / "public" / f"video_data_{video_id}.json",
                Path("remotion-video") / "public" / f"{video_id}.json",
                Path("public") / f"video_data_{video_id}.json",
                Path("public") / f"{video_id}.json",
            ]
            for mf in possible_meta_files:
                if mf.exists():
                    try:
                        with open(mf, 'r', encoding='utf-8') as f:
                            meta = json.load(f)
                        print(f"✓ Đã sinh info.json từ metadata: {mf}")
                        scenes = meta.get("scenes", [])
                        desc_parts = [sc.get("text", "") for sc in scenes if sc.get("text")]
                        description = " ".join(desc_parts[:3])
                        tags = ["Nửa Chén Trà", "Nhìn sâu để sống nhẹ"]
                        if meta.get("book"):
                            tags.append(meta.get("book"))
                        if meta.get("author"):
                            tags.append(meta.get("author"))

                        info_data = {
                            "id": video_id,
                            "title": meta.get("title", f"Video {video_id}"),
                            "subtitle": meta.get("subtitle", ""),
                            "book": meta.get("book", ""),
                            "author": meta.get("author", ""),
                            "chapter": meta.get("chapter", ""),
                            "description": description,
                            "tags": tags,
                            "final_video_file": path.name
                        }
                        break
                    except Exception as e:
                        print(f"⚠️ Trích xuất metadata {mf} thất bại: {e}")

        # 4. Tìm và Upload file Thumbnail (cho Long Video & Video có thumbnail)
        possible_thumb_files = [
            path.parent / f"thumbnail_{video_id}.jpg",
            path.parent / f"thumbnail_{video_id}.png",
            Path("output") / video_id / f"thumbnail_{video_id}.jpg",
            Path("output") / video_id / f"thumbnail_{video_id}.png",
            Path("remotion-video") / "output" / video_id / f"thumbnail_{video_id}.jpg",
        ]
        for folder_check in [path.parent, Path("output") / video_id, Path("remotion-video") / "output" / video_id]:
            if folder_check.exists():
                for tf in folder_check.glob("thumbnail*.*"):
                    if tf not in possible_thumb_files:
                        possible_thumb_files.append(tf)

        uploaded_thumbs = []
        for tf in possible_thumb_files:
            if tf.exists() and tf not in uploaded_thumbs:
                mtype = 'image/png' if tf.suffix.lower() == '.png' else 'image/jpeg'
                thumb_resp = upload_file_to_folder(drive_service, tf, subfolder_id, mtype)
                print(f"🖼️ ĐÃ TẢI THUMBNAIL LÊN DRIVE: {tf.name}")
                uploaded_thumbs.append(tf)
                if info_data:
                    info_data['thumbnail_file'] = tf.name
                    info_data['thumbnail_gdrive_url'] = thumb_resp.get('webViewLink')

        if info_data:
            info_data['gdrive_video_id'] = video_response.get('id')
            info_data['gdrive_video_url'] = video_response.get('webViewLink')
            info_data['gdrive_folder_id'] = subfolder_id
            info_data['file_size_mb'] = round(path.stat().st_size / 1024 / 1024, 2)
            upload_json_to_folder(drive_service, info_data, "info.json", subfolder_id)
        else:
            print("⚠️ Không tìm thấy metadata để tạo info.json.")

        # 5. Tự động đóng gói & Upload thư mục input/ lên Google Drive
        input_folder_id = create_drive_folder(drive_service, "input", subfolder_id)
        input_files_to_upload = []

        possible_input_dirs = [
            path.parent / "input",
            Path("output") / video_id / "input",
            Path("remotion-video") / "output" / video_id / "input"
        ]
        found_local_input = False
        for p_in in possible_input_dirs:
            if p_in.exists() and p_in.is_dir():
                for f_in in p_in.iterdir():
                    if f_in.is_file():
                        input_files_to_upload.append(f_in)
                found_local_input = True
                break

        if not found_local_input:
            for mf in [Path("remotion-video") / "public" / f"video_data_{video_id}.json", Path("remotion-video") / "public" / f"{video_id}.json"]:
                if mf.exists():
                    input_files_to_upload.append(mf)
                    break
            for vf in [Path("remotion-video") / "public" / f"voiceover_{video_id}.wav", Path("remotion-video") / "public" / f"voiceover_{video_id}.mp3"]:
                if vf.exists():
                    input_files_to_upload.append(vf)
                    break
            for sf in [Path("pipeline") / f"script_{video_id}.json", Path(f"script_{video_id}.json")]:
                if sf.exists():
                    input_files_to_upload.append(sf)
                    break

        for src_file in input_files_to_upload:
            ext = src_file.suffix.lower()
            if ext == ".json": mtype = "application/json"
            elif ext == ".wav": mtype = "audio/wav"
            elif ext == ".mp3": mtype = "audio/mpeg"
            elif ext == ".md": mtype = "text/markdown"
            else: mtype = "application/octet-stream"
            upload_file_to_folder(drive_service, src_file, input_folder_id, mtype)
            print(f"📦 Đã tải nguyên liệu input lên Drive: {src_file.name}")

        print(f"\n========================================================")
        print(f"🎉 TẤT CẢ FILE CỦA '{video_id}' ĐÃ ĐƯỢC LƯU TRỌN VẸN TRÊN DRIVE!")
        print(f"📁 Thư mục Drive: https://drive.google.com/drive/folders/{subfolder_id}")
        print(f"========================================================")

    except Exception as e:
        print(f"❌ Lỗi khi tải lên Google Drive: {e}")
        import traceback; traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python upload_to_gdrive.py <file_path> <parent_folder_id>")
        sys.exit(1)
    upload_video_to_gdrive(sys.argv[1], sys.argv[2])
