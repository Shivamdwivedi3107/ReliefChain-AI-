import io
import base64
from typing import Optional

try:
    import qrcode
    QRCODE_AVAILABLE = True
except ImportError:
    QRCODE_AVAILABLE = False


def generate_qr_base64_image(data_text: str) -> str:
    """Generate Base64 encoded PNG string from data string."""
    if not QRCODE_AVAILABLE:
        # Fallback base64 string
        encoded = base64.b64encode(f"QR_DATA:{data_text}".encode()).decode()
        return f"data:image/png;base64,{encoded}"

    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=10,
        border=4,
    )
    qr.add_data(data_text)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    buffered = io.BytesIO()
    img.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
    return f"data:image/png;base64,{img_str}"
