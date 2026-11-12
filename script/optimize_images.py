"""
OVC Web Assets Optimization Script
Performs lossless/high-quality image optimization and resizing:
- Preserves exact filenames and extensions.
- Transposes orientation based on EXIF before resizing.
- Avatar/generation photos: max 800px.
- Hero/banner/common backgrounds: max 1920px.
- All other photos: max 1400px.
- Files > 250KB or exceeding max dimensions are optimized.
- Overwrites in-place only if new file size is strictly smaller.
"""

import os
import io
import time
from concurrent.futures import ThreadPoolExecutor
from PIL import Image, ImageOps

ASSETS_DIR = os.path.dirname(os.path.abspath(__file__))
IMAGE_EXTENSIONS = {".webp", ".jpg", ".jpeg", ".png"}

def get_max_dimension(rel_path: str) -> int:
    rel_path_lower = rel_path.replace("\\", "/").lower()
    fname = os.path.basename(rel_path_lower)
    if "about-us/generation/" in rel_path_lower:
        return 800
    if (
        rel_path_lower.startswith("common-assets/")
        or "/hero/" in rel_path_lower
        or fname.startswith("bia.")
        or fname.startswith("bia-")
        or "banner" in fname
    ):
        return 1920
    return 1400

def process_image(file_info):
    abs_path, rel_path = file_info
    ext = os.path.splitext(abs_path)[1]
    ext_lower = ext.lower()
    orig_size = os.path.getsize(abs_path)
    max_dim = get_max_dimension(rel_path)

    try:
        with Image.open(abs_path) as img:
            img.seek(0)
            orig_w, orig_h = img.size
            dim_exceeded = max(orig_w, orig_h) > max_dim
            size_exceeded = orig_size > 250 * 1024

            if not (size_exceeded or dim_exceeded):
                return (rel_path, orig_size, orig_size, False, None)

            # Apply orientation transposition
            img = ImageOps.exif_transpose(img)
            img.thumbnail((max_dim, max_dim), Image.Resampling.LANCZOS)

            buf = io.BytesIO()
            if ext_lower == ".webp":
                save_img = img
                if save_img.mode not in ("RGB", "RGBA"):
                    save_img = save_img.convert("RGBA" if "A" in save_img.mode else "RGB")
                save_img.save(buf, format="WEBP", quality=82, method=6)
            elif ext_lower in (".jpg", ".jpeg"):
                save_img = img
                if save_img.mode != "RGB":
                    save_img = save_img.convert("RGB")
                save_img.save(buf, format="JPEG", quality=82, optimize=True, progressive=True)
            elif ext_lower == ".png":
                save_img = img
                save_img.save(buf, format="PNG", optimize=True)
                if buf.tell() > 500 * 1024:
                    q_buf = io.BytesIO()
                    if save_img.mode == "RGBA":
                        q_img = save_img.quantize(colors=256, method=Image.Quantize.FASTOCTREE)
                    else:
                        q_img = save_img.convert("RGB").quantize(colors=256)
                    q_img.save(q_buf, format="PNG", optimize=True)
                    if q_buf.tell() < buf.tell():
                        buf = q_buf

            new_bytes = buf.getvalue()
            new_size = len(new_bytes)

            if new_size < orig_size:
                with open(abs_path, "wb") as f_out:
                    f_out.write(new_bytes)
                return (rel_path, orig_size, new_size, True, None)
            else:
                return (rel_path, orig_size, orig_size, False, None)

    except Exception as e:
        return (rel_path, orig_size, orig_size, False, str(e))

def main():
    start_time = time.time()
    targets = []

    for root, dirs, files in os.walk(ASSETS_DIR):
        if ".git" in dirs:
            dirs.remove(".git")
        for f in files:
            ext = os.path.splitext(f)[1].lower()
            if ext in IMAGE_EXTENSIONS:
                abs_path = os.path.join(root, f)
                rel_path = os.path.relpath(abs_path, ASSETS_DIR)
                targets.append((abs_path, rel_path))

    total_images = len(targets)
    print(f"Scanning {total_images} images with ThreadPoolExecutor...")

    optimized_count = 0
    total_orig = 0
    total_final = 0
    errors = []
    largest_file = ("", 0)

    # Use 8 worker threads for balanced parallel I/O and CPU
    with ThreadPoolExecutor(max_workers=8) as executor:
        results = list(executor.map(process_image, targets))

    for rel_path, orig_sz, final_sz, overwritten, err in results:
        total_orig += orig_sz
        total_final += final_sz
        if overwritten:
            optimized_count += 1
        if err:
            errors.append((rel_path, err))
        if final_sz > largest_file[1]:
            largest_file = (rel_path, final_sz)

    elapsed = time.time() - start_time
    print(f"\n--- OPTIMIZATION SUMMARY ---")
    print(f"Execution time: {elapsed:.2f}s")
    print(f"Total images checked: {total_images}")
    print(f"Files optimized & overwritten: {optimized_count}")
    print(f"Total size before: {total_orig / (1024*1024):.2f} MB ({total_orig} bytes)")
    print(f"Total size after:  {total_final / (1024*1024):.2f} MB ({total_final} bytes)")
    saved = total_orig - total_final
    pct = (saved / total_orig * 100) if total_orig > 0 else 0
    print(f"Space saved: {saved / (1024*1024):.2f} MB ({pct:.1f}% reduction)")
    print(f"Largest remaining file: {largest_file[0]} ({largest_file[1] / 1024:.1f} KB / {largest_file[1] / (1024*1024):.2f} MB)")
    if errors:
        print(f"Encountered {len(errors)} errors:")
        for r, e in errors:
            print(f"  {r}: {e}")
    else:
        print("All images processed with zero errors!")

if __name__ == "__main__":
    main()
