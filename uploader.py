import base64
import requests

IMGBB_URL = "https://api.imgbb.com/1/upload"


class ImageUploader:
    def __init__(self, config):
        self.config = config
        # Reuse one session so repeated uploads share a connection pool
        # instead of opening a fresh TCP/TLS handshake every time.
        self._session = requests.Session()

    def upload_to_imgbb(self, image_bytes, name=None):
        try:
            payload = {
                "key": self.config.apis[self.config.current_api],
                "image": base64.b64encode(image_bytes),
                "expiration": self.config.expiration,
            }
            # No "name" field at all for the default style - imgbb picks its own
            if name:
                payload["name"] = name

            response = self._session.post(IMGBB_URL, data=payload, timeout=30)
            if response.status_code != 200:
                print(f"Upload error: {response.status_code} - {response.text}")
                return None

            data = response.json()["data"]
            return "https://ibb.co/" + data["id"]

        except Exception as e:
            print(f"Upload exception: {e}")
            return None
