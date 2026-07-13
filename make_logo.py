from PIL import Image

def make_transparent(input_path, output_path):
    img = Image.open(input_path).convert("RGBA")
    data = img.getdata()
    
    new_data = []
    for item in data:
        # If the pixel is pure white or very close to white, make it transparent
        # item is (R, G, B, A)
        if item[0] > 240 and item[1] > 240 and item[2] > 240:
            new_data.append((255, 255, 255, 0))
        else:
            new_data.append(item)
            
    img.putdata(new_data)
    img.save(output_path, "PNG")

input_image = r"C:\Users\andre\.gemini\antigravity-ide\brain\b94cfe38-e31b-440f-a253-5f685e8f175c\mutuner_logo_minimalist_1783980855069.png"
output_image = "e:/myTuner/static/img/logo.png"

import os
os.makedirs(os.path.dirname(output_image), exist_ok=True)

make_transparent(input_image, output_image)

# Create favicon (smaller version)
img = Image.open(output_image)
img.thumbnail((32, 32))
img.save("e:/myTuner/static/img/favicon.ico", format="ICO")
print("Logo created and saved to static/img/")
