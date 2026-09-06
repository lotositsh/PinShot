# image_processor.py
import io
import traceback


class ImageProcessor:
    def __init__(self, config):
        self.config = config

    def process_screenshot(self, screenshot):
        """Encode the screenshot per the configured format and return
        (image_bytes, size, file_size_kb)."""
        try:
            fmt = self.config.image_format

            if fmt == "JPEG":
                screenshot = screenshot.convert("RGB")

            buffer = io.BytesIO()
            if fmt == "WEBP":
                screenshot.save(buffer, format="WEBP", quality=self.config.quality)
            elif fmt == "PNG":
                screenshot.save(buffer, format="PNG")
            elif fmt == "JPEG":
                screenshot.save(buffer, format="JPEG", quality=self.config.quality)
            else:
                raise ValueError(f"Unsupported image format: {fmt}")

            image_bytes = buffer.getvalue()
            file_size_kb = len(image_bytes) // 1024

            return image_bytes, screenshot.size, file_size_kb

        except Exception as e:
            print(f"Error in process_screenshot: {e}")
            traceback.print_exc()
            raise
