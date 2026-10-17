import os
import sys
import json
from pathlib import Path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

sys.stdout.reconfigure(encoding='utf-8')

def get_drive_credentials():
    # 1. Ưu tiên OAuth Credentials của tài khoản cá nhân (Dùng dung lượng cá nhân, không bị hạn mức 0 của Service Account)
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
        print("🔑 Sử dụng Google Service Account Key (Google Workspace Shared Drive)...")
        service_account_info = json.loads(sa_json)
        return service_account.Credentials.from_service_account_info(
            service_account_info, scopes=['https://www.googleapis.com/auth/drive']
        )

    print("❌ Không tìm thấy thông tin xác thực Google Drive (cần GDRIVE_CLIENT_ID/GDRIVE_CLIENT_SECRET/GDRIVE_REFRESH_TOKEN hoặc GDRIVE_SA_KEY).")
    sys.exit(1)

def upload_video_to_gdrive(file_path, folder_id):
    path = Path(file_path)
    if not path.exists():
        print(f"❌ Không tìm thấy file: {file_path}")
        sys.exit(1)

    creds = get_drive_credentials()

    try:
        drive_service = build('drive', 'v3', credentials=creds)

        file_metadata = {
            'name': path.name,
            'parents': [folder_id]
        }

        media = MediaFileUpload(
            str(path),
            mimetype='video/mp4',
            resumable=True
        )

        print(f"☁️ Đang tải {path.name} ({round(path.stat().st_size / 1024 / 1024, 2)} MB) lên Google Drive (Folder ID: {folder_id})...")
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
                print(f"   Đang tải: {int(status.progress() * 100)}%")

        print(f"✅ TẢI LÊN GOOGLE DRIVE THÀNH CÔNG!")
        print(f"📁 File ID: {response.get('id')}")
        print(f"🔗 Xem trên Drive: {response.get('webViewLink')}")
    except Exception as e:
        print(f"❌ Lỗi khi tải file lên Google Drive: {e}")
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python upload_to_gdrive.py <file_path> <folder_id>")
        sys.exit(1)
    upload_video_to_gdrive(sys.argv[1], sys.argv[2])
