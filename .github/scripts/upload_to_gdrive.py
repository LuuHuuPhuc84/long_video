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
    # 1. Ưu tiên OAuth Credentials của tài khoản cá nhân
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

    # 2. Dự phòng: Service Account Key
    sa_json = os.environ.get("GDRIVE_SA_KEY")
    if sa_json:
        print("🔑 Sử dụng Google Service Account Key...")
        service_account_info = json.loads(sa_json)
        return service_account.Credentials.from_service_account_info(
            service_account_info, scopes=['https://www.googleapis.com/auth/drive']
        )

    print("❌ Không tìm thấy thông tin xác thực Google Drive.")
    sys.exit(1)

def create_drive_folder(drive_service, folder_name, parent_id):
    """Tạo subfolder trên Drive, trả về folder_id mới."""
    # Kiểm tra folder đã tồn tại chưa
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
    print(f"📁 Đã tạo subfolder: {folder_name} (ID: {folder_id})")
    return folder_id

def upload_file_to_folder(drive_service, file_path, folder_id, mimetype='video/mp4'):
    """Upload một file vào folder, trả về file info."""
    path = Path(file_path)
    file_metadata = {
        'name': path.name,
        'parents': [folder_id]
    }
    media = MediaFileUpload(str(path), mimetype=mimetype, resumable=True)
    size_mb = round(path.stat().st_size / 1024 / 1024, 2)
    print(f"☁️  Đang tải {path.name} ({size_mb} MB) lên Drive...")

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
    """Upload dict dưới dạng JSON file vào folder."""
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
    print(f"📄 Đã upload {filename} lên Drive (ID: {result.get('id')})")
    return result

def upload_video_to_gdrive(file_path, parent_folder_id):
    path = Path(file_path)
    if not path.exists():
        print(f"❌ Không tìm thấy file: {file_path}")
        sys.exit(1)

    # Lấy video_id từ tên thư mục cha (output/{video_id}/)
    video_id = path.parent.name
    info_file = path.parent / "info.json"

    creds = get_drive_credentials()

    try:
        drive_service = build('drive', 'v3', credentials=creds)

        # 1. Tạo subfolder {video_id} trên Drive
        print(f"\n📂 Tạo/kiểm tra subfolder '{video_id}' trên Drive...")
        subfolder_id = create_drive_folder(drive_service, video_id, parent_folder_id)

        # 2. Upload video MP4
        video_response = upload_file_to_folder(drive_service, file_path, subfolder_id, 'video/mp4')
        print(f"✅ VIDEO ĐÃ LÊN DRIVE!")
        print(f"   🔗 {video_response.get('webViewLink')}")

        # 3. Upload info.json nếu có
        if info_file.exists():
            with open(info_file, 'r', encoding='utf-8') as f:
                info_data = json.load(f)
            # Thêm link Drive vào info
            info_data['gdrive_video_id'] = video_response.get('id')
            info_data['gdrive_video_url'] = video_response.get('webViewLink')
            info_data['gdrive_folder_id'] = subfolder_id
            upload_json_to_folder(drive_service, info_data, "info.json", subfolder_id)
        else:
            print(f"⚠️  Không tìm thấy info.json tại {info_file}, bỏ qua.")

        print(f"\n✅ HOÀN TẤT! Tất cả file của '{video_id}' đã lên Drive.")

    except Exception as e:
        print(f"❌ Lỗi khi tải lên Google Drive: {e}")
        import traceback; traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python upload_to_gdrive.py <file_path> <parent_folder_id>")
        sys.exit(1)
    upload_video_to_gdrive(sys.argv[1], sys.argv[2])
