import os

folder_path = "ovc-image/about-us/generation/gen4-2024-2025"
members = []

for filename in os.listdir(folder_path):
    if os.path.isfile(os.path.join(folder_path, filename)):
        name_without_ext = os.path.splitext(filename)[0]
        parts = name_without_ext.split('-')
        position = parts[-1]
        
        member = {
            "name": name_without_ext,
            "position": position,
            "image": f"https://cdn.jsdelivr.net/gh/phananhlocpal/ovc-web-assets@master/{folder_path}/{filename}"
        }
        members.append(member)

lines = []
for m in members:
    line = f'{{name: \'{m["name"]}\', position: \'{m["position"]}\', image: \'{m["image"]}\'}}'
    lines.append(line)

text = "{\nmembers:[\n" + ",\n".join(lines) + "\n]\n}"

with open("members.json", "w", encoding="utf-8") as f:
    f.write(text)

