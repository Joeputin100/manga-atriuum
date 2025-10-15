import base64
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
import random

def generate_placeholder_image(text: str, source: str, width: int = 200, height: int = 300) -> str:
    """Generate a base64 encoded placeholder image"""
    # Create image with random background color
    bg_color = (random.randint(100, 200), random.randint(100, 200), random.randint(100, 200))
    img = Image.new('RGB', (width, height), color=bg_color)
    draw = ImageDraw.Draw(img)
    
    # Use default font
    font = ImageFont.load_default()
    
    # Draw source label
    draw.text((10, 10), source, fill=(255, 255, 255), font=font)
    
    # Draw text
    lines = text.split()
    y = height // 2 - len(lines) * 10
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        text_width = bbox[2] - bbox[0]
        x = (width - text_width) // 2
        draw.text((x, y), line, fill=(255, 255, 255), font=font)
        y += 20
    
    # Convert to base64
    buffer = BytesIO()
    img.save(buffer, format='JPEG')
    img_str = base64.b64encode(buffer.getvalue()).decode()
    return f"data:image/jpeg;base64,{img_str}"

# Generate some test images
print("Generating test images...")

images = {
    'deepseek_one_piece': generate_placeholder_image("One Piece\nDeepSeek", "DeepSeek API"),
    'google_bleach': generate_placeholder_image("Bleach\nGoogle Books", "Google Books"),
    'deepseek_naruto': generate_placeholder_image("Naruto\nDeepSeek", "DeepSeek API"),
    'google_death_note': generate_placeholder_image("Death Note\nGoogle Books", "Google Books"),
}

print("Images generated successfully!")
for key, data_url in images.items():
    print(f"{key}: {data_url[:50]}...")
