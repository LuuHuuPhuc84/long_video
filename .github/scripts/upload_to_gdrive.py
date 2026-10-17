import os
import sys
import json
from pathlib import Path
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

sys.stdout.reconfigure(encoding='utf-8')

def upload_video_to_gdrive(file_path, folder_id):
    path = Path(file_path)
    if not path.exists():
        print(f"❌ Không tìm thấy file: {file_path}")
        sys.exit(1)

    sa_json = os.environ.get("GDRIVE_SA_KEY")
    if not sa_json:
        print("❌ Biến môi trường GDRIVE_SA_KEY chưa được cấu hình.")
        sys.exit(1)

    try:
        service_account_info = json.loads(sa_json)
    except Exception as e:
        print(f"❌ Lỗi giải mã JSON từ GDRIVE_SA_KEY: {e}")
        sys.exit(1)

    scopes = ['https://www.googleapis.com/auth/drive']
    creds = service_account.Credentials.from_service_account_info(
        service_account_info, scopes=scopes
    )

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

        print(f"☁️ Đang tải {path.name} ({round(path.stat().st_size / 1024 / 1024, 2)} MB) lên Google Drive...")
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
        print("💡 Gợi ý: Hãy kiểm tra xem Service Account đã được Share quyền 'Editor' vào thư mục Google Drive chưa, và Google Drive API đã được Enable trong Google Cloud chưa.")
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python upload_to_gdrive.py <file_path> <folder_id>")
        sys.exit(1)
    upload_video_to_gdrive(sys.argv[1], sys.argv[2])
