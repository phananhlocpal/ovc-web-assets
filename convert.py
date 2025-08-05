from PIL import Image
import os

input_folder = "src/assets/ovc-image/about-us/why-choose-raw"          
output_folder = "src/assets/ovc-image/about-us/why-choose"

os.makedirs(output_folder, exist_ok=True)

for filename in os.listdir(input_folder):
    if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.JPG')):
        img_path = os.path.join(input_folder, filename)
        img = Image.open(img_path)

        # Nếu là ảnh có palette (P) và có transparency → convert chuẩn sang RGBA
        if img.mode == "P":
            img = img.convert("RGBA")
        elif img.mode in ("LA", "RGBA"):
            img = img.convert("RGBA")
        else:
            img = img.convert("RGB")

        base_name = os.path.splitext(filename)[0] + ".webp"
        output_path = os.path.join(output_folder, base_name)
        
        img.save(output_path, "webp", quality=80, lossless=True)  # lossless giữ trong suốt tốt hơn
        print(f"Converted: {filename} -> {base_name}")

print("Completed converting image to webp!")
