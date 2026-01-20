import os
import sys
import platform

import qrcode
from loguru import logger
import hydra
from omegaconf import DictConfig
from PIL import Image, ImageDraw, ImageFont

def get_font(size):
    """Helper to find a valid system font."""
    paths = []
    if platform.system() == "Windows":
        paths = ["C:\\Windows\\Fonts\\arial.ttf", "C:\\Windows\\Fonts\\segoeui.ttf"]
    elif platform.system() == "Darwin":
        paths = ["/Library/Fonts/Arial.ttf", "/System/Library/Fonts/Helvetica.ttc"]
    else:
        paths = ["/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"]
    
    for path in paths:
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            continue
    return ImageFont.load_default()

@hydra.main(version_base=None, config_path="conf", config_name="config")
def generate_batch(cfg: DictConfig):
    # Load settings from config
    font_size = cfg.settings.font_size
    padding = cfg.settings.padding
    box_size = cfg.settings.box_size
    output_dir = hydra.utils.get_original_cwd() + "/" + cfg.settings.output_dir
    
    os.makedirs(output_dir, exist_ok=True)
    font = get_font(font_size)
    
    logger.remove()

    logger.add(
        sys.stdout,
    colorize=True,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | "
    "{module}:{function}:{line} - {message}",
        level="INFO"
    )

    logger.info(f"Starting batch generation for {len(cfg.locations)} locations...")

    for data in cfg.locations:
        # 1. Generate QR Code
        qr = qrcode.QRCode(box_size=box_size, border=4)
        qr.add_data(data)
        qr.make(fit=True)
        qr_img = qr.make_image(fill_color="black", back_color="white").convert("RGBA")
        qr_w, qr_h = qr_img.size

        # 2. Measure Text
        bbox = font.getbbox(data)
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]

        # 3. Calculate Canvas
        canvas_width = max(qr_w, text_w) + (padding * 2)
        canvas_height = qr_h + text_h + (padding * 3)

        # 4. Create and Assemble
        canvas = Image.new("RGBA", (canvas_width, canvas_height), "white")
        qr_x = (canvas_width - qr_w) // 2
        canvas.paste(qr_img, (qr_x, padding))

        draw = ImageDraw.Draw(canvas)
        text_x = (canvas_width - text_w) // 2
        text_y = qr_h + (padding * 2) - bbox[1]
        draw.text((text_x, text_y), data, fill="black", font=font)

        # 5. Save
        # Sanitize filename (replace slashes/dots if they exist in location names)
        safe_filename = data.replace("/", "-").replace("\\", "-")
        final_path = os.path.join(output_dir, f"{safe_filename}.png")
        canvas.convert("RGB").save(final_path)
        
        logger.info(f"  [✔] Generated: {final_path}")


if __name__ == "__main__":
    generate_batch()