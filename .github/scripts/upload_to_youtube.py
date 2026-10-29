import os
import sys
import json
from pathlib import Path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

sys.stdout.reconfigure(encoding='utf-8')

SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube"
]

def get_youtube_service():
    client_id = os.environ.get("YOUTUBE_CLIENT_ID")
    client_secret = os.environ.get("YOUTUBE_CLIENT_SECRET")
    refresh_token = os.environ.get("YOUTUBE_REFRESH_TOKEN")

    if not (client_id and client_secret and refresh_token):
        print("❌ Lỗi: Thiếu YOUTUBE Secrets (YOUTUBE_CLIENT_ID, YOUTUBE_CLIENT_SECRET, YOUTUBE_REFRESH_TOKEN).")
        return None

    try:
        creds = Credentials(
            None,
            refresh_token=refresh_token,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=client_id,
            client_secret=client_secret,
            scopes=SCOPES
        )
        creds.refresh(Request())
        return build("youtube", "v3", credentials=creds)
    except Exception as e:
        print(f"❌ Lỗi xác thực YouTube API: {e}")
        return None

def upload_video_to_youtube(video_path, video_id):
    youtube = get_youtube_service()
    if not youtube:
        return None

    vpath = Path(video_path)
    if not vpath.exists():
        print(f"❌ Không tìm thấy file video tại: {vpath}")
        return None

    # Tìm thông tin metadata (ưu tiên info.json, sau đó là video_data_*.json)
    info_file = None
    possible_infos = [
        Path("output") / video_id / "info.json",
        Path("output") / video_id / "input" / "info.json",
        vpath.parent / "info.json",
        vpath.parent / "input" / "info.json",
        Path("remotion-video/public") / "info.json",
        Path("remotion-video/public") / f"info_{video_id}.json",
        Path("remotion-video/public") / f"video_data_{video_id}.json",
        Path("pipeline") / f"script_{video_id}.json"
    ]
    for p in possible_infos:
        if p.exists():
            info_file = p
            break

    title = f"Video Essay | {video_id}"
    description = "Nhìn sâu để sống nhẹ — Nửa Chén Trà"
    tags = ["Nửa Chén Trà", "nhìn sâu để sống nhẹ", "video essay", "chữa lành"]

    privacy_status = "private"
    schedule_str = None

    if info_file and info_file.exists():
        try:
            with open(info_file, "r", encoding="utf-8-sig") as f:
                d = json.load(f)
            if d.get("skip_youtube") or d.get("no_youtube"):
                print("ℹ️ Bỏ qua upload YouTube theo cấu hình info.json (skip_youtube=True).")
                return "SKIPPED_BY_CONFIG"
            title = d.get("title") or title
            description = d.get("description") or description
            tags = d.get("tags") or tags
            schedule_str = d.get("schedule") or d.get("schedule_time")
            if isinstance(d.get("status"), dict):
                privacy_status = d["status"].get("privacyStatus", "private")
            elif d.get("privacyStatus"):
                privacy_status = d["privacyStatus"]
        except Exception:
            schedule_str = None

    status_dict = {
        "privacyStatus": privacy_status,
        "selfDeclaredMadeForKids": False,
        "containsSyntheticMedia": True
    }

    publish_log = f"{privacy_status.upper()} ({'Công khai ngay' if privacy_status == 'public' else 'Bản nháp / Draft'})"
    if schedule_str and privacy_status != "public":
        try:
            import datetime
            s = str(schedule_str).strip()
            now = datetime.datetime.now()
            if " " in s:
                schedule_dt = datetime.datetime.strptime(s, "%Y-%m-%d %H:%M")
            else:
                time_part = datetime.datetime.strptime(s, "%H:%M").time()
                schedule_dt = datetime.datetime.combine(now.date(), time_part)
                if schedule_dt <= now:
                    schedule_dt += datetime.timedelta(days=1)
            tz_vn = datetime.timezone(datetime.timedelta(hours=7))
            schedule_dt = schedule_dt.replace(tzinfo=tz_vn)
            utc_dt = schedule_dt.astimezone(datetime.timezone.utc)
            iso_utc = utc_dt.strftime("%Y-%m-%dT%H:%M:%SZ")
            status_dict["publishAt"] = iso_utc
            publish_log = f"SCHEDULED (Hẹn giờ phát sóng lúc {schedule_str} VN -> {iso_utc})"
        except Exception as e:
            print(f"⚠️ Lỗi định dạng schedule '{schedule_str}': {e}. Giữ chế độ private.")

    body = {
        "snippet": {
            "title": title[:100],
            "description": description[:5000],
            "tags": tags,
            "categoryId": "22",  # People & Blogs
            "defaultLanguage": "vi",
            "defaultAudioLanguage": "vi"
        },
        "status": status_dict
    }

    print(f"\n========================================================")
    print(f"🚀 BẮT ĐẦU TẢI VIDEO LÊN YOUTUBE TỪ GITHUB ACTIONS:")
    print(f"📌 Tiêu đề: {title}")
    print(f"📢 Chế độ: {publish_log}")
    print(f"📁 Dung lượng: {round(vpath.stat().st_size / (1024*1024), 2)} MB")
    print(f"========================================================")

    # Upload video resumable
    media = MediaFileUpload(str(vpath), chunksize=10*1024*1024, resumable=True)
    req = youtube.videos().insert(part="snippet,status", body=body, media_body=media)

    response = None
    while response is None:
        status, response = req.next_chunk()
        if status:
            print(f"   -> Đang tải: {int(status.progress() * 100)}%")

    yt_id = response.get("id")
    yt_url = f"https://youtu.be/{yt_id}"
    studio_url = f"https://studio.youtube.com/video/{yt_id}/edit"

    print(f"\n🎉 TẢI LÊN YOUTUBE THÀNH CÔNG!")
    print(f"🆔 YouTube Video ID: {yt_id}")
    print(f"🔗 Link xem: {yt_url}")
    print(f"🛠️ Link chỉnh sửa Studio: {studio_url}")

    # Tìm và upload Thumbnail nếu có
    thumb_file = None
    possible_thumbs = [
        vpath.parent / f"thumbnail_{video_id}_A.jpg",
        vpath.parent / f"thumbnail_{video_id}.jpg",
        vpath.parent / "thumbnail.jpg",
        Path("output") / video_id / f"thumbnail_{video_id}.jpg",
        Path("output") / video_id / "thumbnail.jpg",
        Path("remotion-video/public") / f"thumbnail_{video_id}.jpg"
    ]
    for pt in possible_thumbs:
        if pt.exists():
            thumb_file = pt
            break

    if thumb_file and thumb_file.exists():
        print(f"🖼 Đang tải ảnh Thumbnail: {thumb_file.name}...")
        try:
            youtube.thumbnails().set(
                videoId=yt_id,
                media_body=MediaFileUpload(str(thumb_file))
            ).execute()
            print("✓ Tải Thumbnail thành công!")
        except Exception as e:
            print(f"⚠️ Không thể tải Thumbnail: {e}")

    return {
        "youtube_id": yt_id,
        "youtube_url": yt_url,
        "studio_url": studio_url
    }

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python upload_to_youtube.py <video_path> <video_id>")
        sys.exit(1)
    vpath = sys.argv[1]
    vid = sys.argv[2]
    upload_video_to_youtube(vpath, vid)
