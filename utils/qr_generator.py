import qrcode
import uuid
import base64
import io
from datetime import datetime, timedelta
from django.conf import settings
from django.urls import reverse
from django.utils import timezone


def generate_session_token():
    """Generate a unique token for a session"""
    return str(uuid.uuid4())


def generate_qr_code_data(session_id, token, expiry_time):
    """Generate the data to be encoded in the QR code"""
    data = {
        'session_id': session_id,
        'token': token,
        'expiry': expiry_time.isoformat(),
    }
    return data


def generate_qr_code_url(session_id, token):
    """Generate a URL for the QR code that can be scanned by students"""
    attendance_url = reverse('mark_attendance', args=[session_id, token])
    base_url = getattr(settings, 'BASE_URL', 'https://web-production-9a574.up.railway.app')
    
    # Ensure base_url has protocol (https://)
    if base_url and not base_url.startswith(('http://', 'https://')):
        base_url = f"https://{base_url}"
    
    return f"{base_url}{attendance_url}"


def generate_qr_code_image(url, size=10, border=1):
    """Generate a QR code image from a URL"""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=size,
        border=border,
    )
    qr.add_data(url)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Convert the image to a base64 string
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    img_str = base64.b64encode(buffer.getvalue()).decode()
    
    return f"data:image/png;base64,{img_str}"


def calculate_expiry_time(duration_seconds=10):
    """Calculate the expiry time for a QR code"""
    return timezone.now() + timedelta(seconds=duration_seconds)
