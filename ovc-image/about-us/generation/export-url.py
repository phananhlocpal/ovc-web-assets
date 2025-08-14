import os

folder_path = "ovc-image/about-us/generation/gen0-2021"
members = []

for filename in os.listdir(folder_path):
    if os.path.isfile(os.path.join(folder_path, filename)):
        name_without_ext = os.path.splitext(filename)[0]
        parts = name_without_ext.split('-')
        position = parts[-1]
        
        member = {
            "name": name_without_ext,
            "position": position,
            "image": f"https://cdn.jsdelivr.net/gh/phananhlocpal/ovc-web-assets@master/ovc-image/about-us/generation/gen0-2021/{filename}"
        }
        members.append(member)

# Tạo JSON-like text với key không có ""
lines = []
for m in members:
    line = f'{{name:{m["name"]},position:{m["position"]},image:{m["image"]}}}'
    lines.append(line)

text = "{\nmembers:[\n" + ",\n".join(lines) + "\n]\n}"

with open("members.json", "w", encoding="utf-8") as f:
    f.write(text)

print("Đã xuất xong members.json kiểu key không có nháy")
