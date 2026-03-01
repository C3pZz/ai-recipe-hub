#!/usr/bin/env python3
"""Generate OG image for AI Recipe Hub"""
from PIL import Image, ImageDraw, ImageFont
import os

def create_og_image(output_path, width=1200, height=630):
    # Create gradient background
    img = Image.new('RGB', (width, height), color='#0a0e1a')
    draw = ImageDraw.Draw(img)

    # Background gradient effect (simple)
    for y in range(height):
        alpha = int(255 * (1 - y / height) * 0.3)
        draw.line([(0, y), (width, y)], fill=(99, 102, 241, alpha))

    # Draw decorative elements
    # Top accent line
    draw.rectangle([0, 0, width, 4], fill='#6366f1')

    # Circle decorations
    draw.ellipse([900, -100, 1300, 300], outline='#6366f1', width=2)
    draw.ellipse([800, 400, 1100, 700], outline='#06b6d4', width=1)

    # Main text
    try:
        # Try to use a system font
        title_font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 72)
        subtitle_font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 32)
        small_font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 24)
    except:
        title_font = ImageFont.load_default()
        subtitle_font = ImageFont.load_default()
        small_font = ImageFont.load_default()

    # Title
    draw.text((80, 180), "AI Recipe Hub", font=title_font, fill='#f1f5f9')

    # Subtitle
    draw.text((80, 290), "AIツール比較・レビュー専門メディア", font=subtitle_font, fill='#94a3b8')

    # Description
    draw.text((80, 360), "文章生成・画像生成・コーディング・業務効率化", font=small_font, fill='#64748b')
    draw.text((80, 395), "あらゆるカテゴリのAIツールを徹底比較", font=small_font, fill='#64748b')

    # Badge
    draw.rounded_rectangle([80, 450, 340, 500], radius=25, fill='#6366f1')
    draw.text((110, 462), "毎日更新中", font=small_font, fill='white')

    # URL
    draw.text((80, 560), "airecipehub.com", font=small_font, fill='#6366f1')

    # Save
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    img.save(output_path, 'PNG', optimize=True)
    print(f"OG image saved to: {output_path}")

if __name__ == '__main__':
    create_og_image('/home/ubuntu/projects/ai-recipe-hub/static/images/og-image.png')
