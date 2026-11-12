"""
OVC Web Assets Cloudinary Uploader
Uploads all images from common-assets, logo, and ovc-image to Cloudinary
using Python Standard Library only (urllib, hashlib, json, mimetypes, concurrent.futures).

Features:
- Preserves exact relative public_id (without extension) for seamless drop-in CDN replacement.
- Sets asset_folder matching folder structure for clean visual Media Library UI.
- Signs requests with HMAC SHA-1 per Cloudinary Upload API specification.
- Supports single-file smoke testing (--smoke-test).
- High-concurrency parallel upload (ThreadPoolExecutor) with exponential backoff retries.
"""

import os
import sys
import time
import json
import uuid
import hashlib
import mimetypes
import urllib.request
import urllib.error
from concurrent.futures import ThreadPoolExecutor, as_completed

ASSETS_DIR = os.path.dirname(os.path.abspath(__file__))
ENV_FILE = os.path.join(ASSETS_DIR, ".env")
TARGET_FOLDERS = ["common-assets", "logo", "ovc-image"]
IMAGE_EXTENSIONS = {".webp", ".jpg", ".jpeg", ".png", ".svg"}

def load_env(env_path: str) -> dict:
    if not os.path.exists(env_path):
        raise FileNotFoundError(f".env file not found at: {env_path}")
    env_vars = {}
    with open(env_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                env_vars[k.strip()] = v.strip().strip("'\"")
    required = ["CLOUDINARY_CLOUD_NAME", "CLOUDINARY_API_KEY", "CLOUDINARY_API_SECRET"]
    for req in required:
        if req not in env_vars or not env_vars[req]:
            raise ValueError(f"Missing required configuration: {req} in {env_path}")
    return env_vars

def generate_signature(params: dict, api_secret: str) -> str:
    # Sort keys alphabetically and construct key=value&key2=value2... + secret
    sorted_keys = sorted(params.keys())
    to_sign = "&".join(f"{k}={params[k]}" for k in sorted_keys) + api_secret
    return hashlib.sha1(to_sign.encode("utf-8")).hexdigest()

def encode_multipart_formdata(fields: dict, file_field: str, file_path: str):
    boundary = f"----CloudinaryBoundary{uuid.uuid4().hex}"
    body = bytearray()

    for key, value in fields.items():
        body.extend(f"--{boundary}\r\n".encode("utf-8"))
        body.extend(f'Content-Disposition: form-data; name="{key}"\r\n\r\n'.encode("utf-8"))
        body.extend(f"{value}\r\n".encode("utf-8"))

    filename = os.path.basename(file_path)
    content_type = mimetypes.guess_type(file_path)[0] or "application/octet-stream"
    body.extend(f"--{boundary}\r\n".encode("utf-8"))
    body.extend(f'Content-Disposition: form-data; name="{file_field}"; filename="{filename}"\r\n'.encode("utf-8"))
    body.extend(f"Content-Type: {content_type}\r\n\r\n".encode("utf-8"))
    with open(file_path, "rb") as f:
        body.extend(f.read())
    body.extend(f"\r\n--{boundary}--\r\n".encode("utf-8"))

    content_type_header = f"multipart/form-data; boundary={boundary}"
    return bytes(body), content_type_header

def upload_single_file(file_path: str, rel_path: str, config: dict, max_retries: int = 3) -> tuple:
    rel_path_norm = rel_path.replace("\\", "/")
    # public_id: without extension
    public_id = os.path.splitext(rel_path_norm)[0]
    # asset_folder: parent directory
    asset_folder = os.path.dirname(rel_path_norm)
    if not asset_folder:
        asset_folder = ""

    cloud_name = config["CLOUDINARY_CLOUD_NAME"]
    api_key = config["CLOUDINARY_API_KEY"]
    api_secret = config["CLOUDINARY_API_SECRET"]
    upload_url = f"https://api.cloudinary.com/v1_1/{cloud_name}/image/upload"

    for attempt in range(1, max_retries + 1):
        timestamp = str(int(time.time()))
        signed_params = {
            "asset_folder": asset_folder,
            "invalidate": "true",
            "overwrite": "true",
            "public_id": public_id,
            "timestamp": timestamp,
        }
        signature = generate_signature(signed_params, api_secret)

        fields = {
            "api_key": api_key,
            "timestamp": timestamp,
            "public_id": public_id,
            "asset_folder": asset_folder,
            "overwrite": "true",
            "invalidate": "true",
            "signature": signature,
        }

        try:
            body_bytes, content_type = encode_multipart_formdata(fields, "file", file_path)
            req = urllib.request.Request(upload_url, data=body_bytes, method="POST")
            req.add_header("Content-Type", content_type)
            req.add_header("Content-Length", str(len(body_bytes)))
            req.add_header("User-Agent", "OVC-Cloudinary-Uploader/1.0")

            with urllib.request.urlopen(req, timeout=45) as resp:
                resp_data = resp.read().decode("utf-8")
                resp_json = json.loads(resp_data)
                return True, rel_path_norm, resp_json

        except urllib.error.HTTPError as e:
            err_body = e.read().decode("utf-8", errors="ignore")
            # If 4xx client error (e.g. invalid signature), don't retry endlessly
            if 400 <= e.code < 500 and e.code != 429:
                return False, rel_path_norm, f"HTTP {e.code}: {err_body}"
            if attempt == max_retries:
                return False, rel_path_norm, f"HTTP {e.code} after {max_retries} attempts: {err_body}"
            time.sleep(1.5 * attempt)

        except Exception as e:
            if attempt == max_retries:
                return False, rel_path_norm, f"Exception after {max_retries} attempts: {str(e)}"
            time.sleep(1.5 * attempt)

    return False, rel_path_norm, "Unknown upload failure"

def verify_live_url(url: str, timeout: int = 15) -> tuple:
    req = urllib.request.Request(url, method="GET")
    req.add_header("User-Agent", "OVC-Url-Verifier/1.0")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status == 200, resp.status, resp.headers.get("Content-Type", "")
    except urllib.error.HTTPError as e:
        return False, e.code, str(e)
    except Exception as e:
        return False, 0, str(e)

def run_smoke_test(config: dict):
    print("=" * 60)
    print("RUNNING SMOKE TEST: Uploading single file (logo/ovc.webp)...")
    print("=" * 60)
    
    sample_file = os.path.join(ASSETS_DIR, "logo", "ovc.webp")
    if not os.path.exists(sample_file):
        print(f"Error: {sample_file} does not exist!")
        sys.exit(1)

    rel_path = "logo/ovc.webp"
    ok, rel, result = upload_single_file(sample_file, rel_path, config)
    if not ok:
        print(f"Smoke test upload FAILED: {result}")
        sys.exit(1)

    print("Smoke test upload SUCCESS!")
    print(f"  Public ID : {result.get('public_id')}")
    print(f"  Secure URL: {result.get('secure_url')}")
    print(f"  Format    : {result.get('format')}")
    print(f"  Bytes     : {result.get('bytes')}")

    # Verify transformed delivery URL
    cloud_name = config["CLOUDINARY_CLOUD_NAME"]
    test_delivery_url = f"https://res.cloudinary.com/{cloud_name}/image/upload/f_auto,q_auto/logo/ovc.webp"
    print(f"\nVerifying live delivery URL: {test_delivery_url}")
    is_live, status, ctype = verify_live_url(test_delivery_url)
    if is_live:
        print(f"VERIFICATION SUCCESS: HTTP {status} (Content-Type: {ctype})")
    else:
        print(f"VERIFICATION FAILED: Status {status} - {ctype}")
        sys.exit(1)
    print("=" * 60)

def run_full_upload(config: dict, max_workers: int = 8):
    print("=" * 60)
    print("COLLECTING TARGET IMAGES...")
    targets = []
    for folder in TARGET_FOLDERS:
        folder_path = os.path.join(ASSETS_DIR, folder)
        if not os.path.exists(folder_path):
            continue
        for root, dirs, files in os.walk(folder_path):
            if ".git" in dirs:
                dirs.remove(".git")
            for f in files:
                ext = os.path.splitext(f)[1].lower()
                if ext in IMAGE_EXTENSIONS:
                    abs_path = os.path.join(root, f)
                    rel_path = os.path.relpath(abs_path, ASSETS_DIR)
                    targets.append((abs_path, rel_path))

    total = len(targets)
    print(f"Found {total} images across target folders ({', '.join(TARGET_FOLDERS)}).")
    print(f"Starting parallel upload with ThreadPoolExecutor (max_workers={max_workers})...")
    print("=" * 60)

    start_time = time.time()
    uploaded_count = 0
    failed_count = 0
    failures = []

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_file = {
            executor.submit(upload_single_file, abs_p, rel_p, config): rel_p
            for abs_p, rel_p in targets
        }

        for idx, future in enumerate(as_completed(future_to_file), 1):
            rel_p = future_to_file[future]
            try:
                ok, _, res = future.result()
                if ok:
                    uploaded_count += 1
                else:
                    failed_count += 1
                    failures.append((rel_p, res))
            except Exception as e:
                failed_count += 1
                failures.append((rel_p, str(e)))

            if idx % 50 == 0 or idx == total:
                print(f"Progress: [{idx}/{total}] completed ({uploaded_count} uploaded, {failed_count} failed)...")

    elapsed = time.time() - start_time
    print("=" * 60)
    print("UPLOAD SUMMARY")
    print("=" * 60)
    print(f"Total images processed: {total}")
    print(f"Successfully uploaded : {uploaded_count}")
    print(f"Failed uploads        : {failed_count}")
    print(f"Total time elapsed    : {elapsed:.2f} seconds (avg {elapsed/total:.2f}s per image)")
    print(f"CLOUDINARY_CLOUD_NAME : {config['CLOUDINARY_CLOUD_NAME']}")

    if failures:
        print(f"\nFailed files ({len(failures)}):")
        for f_path, err in failures[:10]:
            print(f"  {f_path}: {err}")
    else:
        print("\nAll files uploaded successfully with 0 errors!")

    # Verify sample live URLs
    cloud_name = config["CLOUDINARY_CLOUD_NAME"]
    samples = [
        "logo/ovc.webp",
        "ovc-image/about-us/hero/1.webp",
        "ovc-image/activities/xuan-tinh-nguyen/den-tham-mai-am/3(1).jpg"
    ]
    print("\nVerifying sample live delivery URLs:")
    for sample in samples:
        url = f"https://res.cloudinary.com/{cloud_name}/image/upload/f_auto,q_auto/{sample}"
        ok, status, ctype = verify_live_url(url)
        status_text = f"HTTP {status} OK" if ok else f"FAILED (HTTP {status})"
        print(f"  [{status_text}] {url}")
    print("=" * 60)

if __name__ == "__main__":
    config = load_env(ENV_FILE)
    if "--smoke-test" in sys.argv:
        run_smoke_test(config)
    elif "--all" in sys.argv:
        run_full_upload(config, max_workers=8)
    else:
        print("Usage: python upload_to_cloudinary.py [--smoke-test | --all]")
