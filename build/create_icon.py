"""Create application icon for Warehouse-GUI.

This script generates a simple icon file for the application.
Run this script to generate the icon.ico file.
"""

from PIL import Image, ImageDraw, ImageFont
import os


def create_icon():
    """Create application icon."""
    # Image sizes for Windows icon
    sizes = [(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)]

    images = []

    for size in sizes:
        # Create a new image with a transparent background
        img = Image.new('RGBA', size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        # Draw a rounded rectangle (box/warehouse shape)
        padding = size[0] // 10
        box = (
            padding,
            padding,
            size[0] - padding,
            size[1] - padding
        )

        # Draw gradient background (blue to dark blue)
        gradient_steps = 20
        for i in range(gradient_steps):
            progress = i / gradient_steps
            color_intensity = int(100 + 100 * progress)
            color = (0, color_intensity, 200, 255)

            # Calculate rectangle coordinates
            x0 = padding
            y0 = padding + int((size[1] - 2 * padding) * progress)
            x1 = size[0] - padding
            y1 = y0 + int((size[1] - 2 * padding) / gradient_steps) + 1

            # Ensure y1 >= y0
            if y1 < y0:
                y1 = y0 + 1

            draw.rectangle(
                (x0, y0, x1, min(y1, size[1] - padding)),
                fill=color,
                outline=color
            )

        # Draw box shape (warehouse)
        box_padding = size[0] // 6
        draw.rectangle(
            (box_padding, box_padding + size[0]//8, size[0] - box_padding, size[1] - box_padding),
            fill=(255, 255, 255, 200),
            outline=(255, 255, 255, 255),
            width=2
        )

        # Draw "W" text for Warehouse
        try:
            font_size = size[0] // 3
            font = ImageFont.truetype("arial.ttf", font_size)
        except:
            # Fallback to default font if arial not available
            font = ImageFont.load_default()

        text = "W"
        text_bbox = draw.textbbox((0, 0), text, font=font)
        text_width = text_bbox[2] - text_bbox[0]
        text_height = text_bbox[3] - text_bbox[1]

        text_position = (
            (size[0] - text_width) // 2,
            (size[1] - text_height) // 2
        )

        draw.text(text_position, text, fill=(255, 255, 255, 255), font=font)

        images.append(img)

    # Save as ICO file
    icon_path = os.path.join(os.path.dirname(__file__), 'icon.ico')
    images[0].save(
        icon_path,
        format='ICO',
        sizes=[(size[0], size[1]) for size in sizes]
    )

    print(f"Icon created: {icon_path}")
    return icon_path


if __name__ == '__main__':
    create_icon()
