import os
import sys
import json
import shutil
import time
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

BASE_DIR = Path(__file__).resolve().parent.parent
PIPELINE_DIR = BASE_DIR / "pipeline"
OUTPUT_DIR = BASE_DIR / "output"
GDRIVE_LONG_DIR = Path(r"G:\Drive của tôi\Video_Render\Long_Video")

def publish_long_video_from_drive(video_id="essay_ep02"):
    """
    Tự động quét thư mục output trong gói pkg_{video_id} trên Google Drive (Long Video).
    Nếu tìm thấy file video thành phẩm:
    1. Copy video & thumbnail về thư mục con output/{video_id}/ trên máy A.
    2. Đọc file post_info.json (tiêu đề, mô tả, tags).
    3. Tự động đăng và hẹn giờ lên YouTube qua pipeline/upload_youtube.py!
    """
    pkg_dir = GDRIVE_LONG_DIR / f"pkg_{video_id}"
    if not pkg_dir.exists():
        print(f"❌ Không tìm thấy gói: {pkg_dir}")
        return False

    out_folder = pkg_dir / "output"
    if not out_folder.exists():
        print(f"❌ Không tìm thấy thư mục output trong gói: {out_folder}")
        return False

    # Tìm file mp4 trong thư mục output, ưu tiên bản render mới nhất
    mp4_files = list(out_folder.glob("*.mp4"))
    if not mp4_files:
        mp4_files = list(pkg_dir.glob("video_*.mp4"))

    if not mp4_files:
        print(f"⚠️ Chưa có file video thành phẩm (.mp4) nào trong thư mục:\n   {out_folder}")
        print("👉 Vui lòng kéo thả file video render từ Máy B vào thư mục output này!")
        return False

    # Sắp xếp theo thời gian tạo/sửa đổi mới nhất
    mp4_files.sort(key=lambda f: f.stat().st_mtime, reverse=True)
    video_file = mp4_files[0]
    print(f"✓ Đã tìm thấy video mới nhất: {video_file.name} ({video_file.stat().st_size / (1024*1024):.1f} MB)")

    # Chuẩn hóa tên file về chuẩn không có đuôi (1)
    clean_video_name = f"video_{video_id}.mp4"
    target_folder = OUTPUT_DIR / video_id
    target_folder.mkdir(parents=True, exist_ok=True)
    local_video_path = target_folder / clean_video_name
    shutil.copy2(video_file, local_video_path)
    print(f"✓ Đã copy về máy A tại: {local_video_path}")

    # Dọn dẹp bản render cũ thừa trên Drive nếu có
    if len(mp4_files) > 1:
        for old_f in mp4_files[1:]:
            try:
                old_f.unlink()
                print(f"   🧹 Đã dọn dẹp bản cũ trùng lặp trên Drive: {old_f.name}")
            except Exception:
                pass

    # Đọc post_info.json
    post_info_file = pkg_dir / "post_info.json"
    post_data = {}
    if post_info_file.exists():
        with open(post_info_file, "r", encoding="utf-8") as f:
            post_data = json.load(f)

    # Copy thumbnail nếu có
    thumb_candidates = list(pkg_dir.glob("thumbnail_*.jpg")) + list(out_folder.glob("thumbnail_*.jpg"))
    local_thumb_path = None
    if thumb_candidates:
        local_thumb_path = target_folder / thumb_candidates[0].name
        shutil.copy2(thumb_candidates[0], local_thumb_path)
        print(f"✓ Đã copy thumbnail tại: {local_thumb_path}")

    yt_title = post_data.get("title", f"Video {video_id}")
    yt_desc = post_data.get("description", "")
    yt_tags = post_data.get("tags", ["Nửa Chén Trà", "Long Video", "triết lý sống"])
    schedule_time = post_data.get("schedule", None)

    # Tạo/cập nhật info.json trong thư mục con
    info_file_path = target_folder / "info.json"
    info_data = {
        "id": video_id,
        "title": yt_title,
        "description": yt_desc,
        "tags": yt_tags,
        "schedule": schedule_time,
        "final_video_file": local_video_path.name,
        "thumbnail_file": local_thumb_path.name if local_thumb_path else None,
        "file_size_mb": round(local_video_path.stat().st_size / (1024 * 1024), 2),
        "updated_at": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    with open(info_file_path, "w", encoding="utf-8") as f:
        json.dump(info_data, f, ensure_ascii=False, indent=2)
    print(f"📄 Đã cập nhật file thông tin: {info_file_path}")

    print(f"\n========================================================")
    print(f"🚀 BẮT ĐẦU XUẤT BẢN LONG VIDEO: {video_file.name}")
    print(f"📌 Tiêu đề: {yt_title}")
    if schedule_time:
        print(f"⏰ Hẹn giờ: {schedule_time}")
    print(f"========================================================")

    # Đăng lên YouTube
    try:
        sys.path.insert(0, str(BASE_DIR))
        from pipeline.upload_youtube import upload_video
        upload_video(
            video_path=str(local_video_path),
            title=yt_title,
            description=yt_desc,
            tags=yt_tags,
            schedule=schedule_time,
            thumbnail_path=str(local_thumb_path) if local_thumb_path else None
        )
    except Exception as e:
        print(f"❌ Lỗi khi upload YouTube: {e}")

if __name__ == "__main__":
    vid_id = sys.argv[1] if len(sys.argv) > 1 else "essay_ep02"
    publish_long_video_from_drive(vid_id)
