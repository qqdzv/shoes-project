import logging
from pathlib import Path

from django.conf import settings
from PIL import Image

logger = logging.getLogger(__name__)


def resize_product_image(photo_path: str | None) -> None:
    if not photo_path or not Path(photo_path).exists():
        return

    max_w = getattr(settings, "PRODUCT_IMAGE_MAX_WIDTH", 300)
    max_h = getattr(settings, "PRODUCT_IMAGE_MAX_HEIGHT", 200)

    try:
        with Image.open(photo_path) as img:
            if img.width > max_w or img.height > max_h:
                img.thumbnail((max_w, max_h), Image.Resampling.LANCZOS)
                img.save(photo_path)
    except Exception:
        logger.exception("Ошибка при обработке фото: %s", photo_path)
