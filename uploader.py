"""
Uploads the generated MP4 to Cloudinary and returns a public URL.
Deletes the local file after a successful upload.
"""
import os
import subprocess
import json


def upload_video(file_path: str) -> str:
    """
    Upload MP4 to Cloudinary. Returns the secure public URL.
    Deletes the local file on success.
    """
    cloud_name = os.environ.get('CLOUDINARY_CLOUD_NAME', '')
    api_key    = os.environ.get('CLOUDINARY_API_KEY', '')
    api_secret = os.environ.get('CLOUDINARY_API_SECRET', '')

    if not all([cloud_name, api_key, api_secret]):
        raise ValueError("CLOUDINARY_CLOUD_NAME, CLOUDINARY_API_KEY and "
                         "CLOUDINARY_API_SECRET must be set")

    upload_url = f"https://api.cloudinary.com/v1_1/{cloud_name}/video/upload"

    print(f"Uploading {os.path.basename(file_path)} to Cloudinary …")

    result = subprocess.run(
        ['curl', '-s',
         '-X', 'POST', upload_url,
         '-u', f'{api_key}:{api_secret}',
         '-F', f'file=@{file_path}',
         '-F', 'resource_type=video',
         '-F', 'folder=gold-rates',
         '-F', 'overwrite=false'],
        capture_output=True, text=True, timeout=120,
    )

    try:
        body = json.loads(result.stdout)
    except Exception:
        raise RuntimeError(f"Cloudinary non-JSON response: {result.stdout[:200]}")

    if 'secure_url' not in body:
        raise RuntimeError(f"Cloudinary upload failed: {body.get('error', body)}")

    url = body['secure_url']
    print(f"Uploaded → {url}")

    # Delete local file — no need to keep it once it's in the cloud
    os.remove(file_path)
    print(f"Local file deleted: {os.path.basename(file_path)}")

    return url
