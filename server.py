"""Small dependency-free web server for the Paddy Mitra dashboard."""
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import json
import os
import secrets
import hashlib
import threading
import socket
import time
import urllib.parse
import urllib.request
from datetime import date
from urllib.parse import urlparse

ROOT = Path(__file__).parent
LOGIN_USER = os.environ.get("PADDY_USER", "ravi")
LOGIN_PASSWORD = os.environ.get("PADDY_PASSWORD", "paddy123")
DATA_DIR = Path(os.environ.get("PADDY_DATA_DIR", str(ROOT)))
DATA_DIR.mkdir(parents=True, exist_ok=True)
USERS_FILE = DATA_DIR / "users.json"
USERS_LOCK = threading.Lock()
SESSIONS = set()
FIELD_STATE = {
    "district": "Mandya",
    "water_level_cm": 3.2,
    "crop_stage": "Tillering",
    "borewell_on": False,
    "ai_detection_on": False,
}
KARNATAKA_DISTRICTS = [
    "Bagalkot", "Ballari", "Belagavi", "Bengaluru Rural", "Bengaluru Urban",
    "Bidar", "Chamarajanagar", "Chikkaballapur", "Chikkamagaluru", "Chitradurga",
    "Dakshina Kannada", "Davanagere", "Dharwad", "Gadag", "Hassan", "Haveri",
    "Kalaburagi", "Kodagu", "Kolar", "Koppal", "Mandya", "Mysuru", "Raichur",
    "Ramanagara", "Shivamogga", "Tumakuru", "Udupi", "Uttara Kannada",
    "Vijayapura", "Vijayanagara", "Yadgir",
]
IRRIGATION_INSTRUCTIONS = [
    {"stage": "After transplanting", "water": "Maintain 2-3 cm during the first week."},
    {"stage": "Vegetative stage", "water": "Target about 5 cm; allow safe drying when suitable."},
    {"stage": "Flowering", "water": "Avoid water stress and check the field daily."},
    {"stage": "Before harvest", "water": "Drain the field completely 10 days before harvest."},
]
WEATHER_DATA = {
    "district": "Mandya",
    "temperature_c": 28,
    "humidity_percent": 78,
    "cloud_cover_percent": 82,
    "wind_kph": 12,
    "pressure_hpa": 1008,
    "recent_rainfall_mm": 4,
    "rain_probability": 65,
    "rainfall_mm": 12,
    "advice": "Delay irrigation if rain arrives tomorrow.",
}
DISTRICT_COORDINATES = {
    "Bagalkot": (16.18, 75.70), "Ballari": (15.14, 76.92), "Belagavi": (15.85, 74.50),
    "Bengaluru Rural": (13.20, 77.70), "Bengaluru Urban": (12.97, 77.59), "Bidar": (17.91, 77.52),
    "Chamarajanagar": (11.92, 76.94), "Chikkaballapur": (13.44, 77.73), "Chikkamagaluru": (13.32, 75.77),
    "Chitradurga": (14.23, 76.40), "Dakshina Kannada": (12.87, 74.88), "Davanagere": (14.47, 75.92),
    "Dharwad": (15.46, 75.01), "Gadag": (15.43, 75.63), "Hassan": (13.00, 76.10), "Haveri": (14.79, 75.40),
    "Kalaburagi": (17.33, 76.83), "Kodagu": (12.42, 75.74), "Kolar": (13.14, 78.13), "Koppal": (15.35, 76.15),
    "Mandya": (12.52, 76.90), "Mysuru": (12.30, 76.65), "Raichur": (16.21, 77.36), "Ramanagara": (12.72, 77.28),
    "Shivamogga": (13.93, 75.57), "Tumakuru": (13.34, 77.10), "Udupi": (13.34, 74.75),
    "Uttara Kannada": (14.80, 74.13), "Vijayapura": (16.83, 75.71), "Vijayanagara": (15.27, 76.39),
    "Yadgir": (16.77, 77.14),
}
WEATHER_CACHE = {}
WEATHER_CACHE_LOCK = threading.Lock()
CROP_CALENDAR = {
    "season": "Kharif",
    "variety": "Sona Masuri",
    "nursery": "May 20 - June 05",
    "transplanting": "June 18 - June 25",
    "tillering": "July 12 - August 28",
    "flowering": "September 17 - October 02",
    "harvest": "October - November",
}
DISEASE_CATALOG = [
    {"name": "Leaf Blast", "symptoms": "Spindle-shaped grey or brown lesions on leaves."},
    {"name": "Brown Spot", "symptoms": "Round brown spots with a lighter centre."},
    {"name": "Sheath Blight", "symptoms": "Oval lesions spreading from the water line."},
    {"name": "Stem Borer", "symptoms": "Dead hearts in young plants or white heads."},
    {"name": "Hopper", "symptoms": "Yellowing or hopper burn near the base of tillers."},
]
DEFAULT_SETTINGS = {"language": "en", "notifications": True, "auto_irrigation": True}
USER_SETTINGS = {}
DAILY_ADVISORIES = [
    [
        {"en": {"title": "Rain expected tomorrow", "text": "Delay irrigation and save approximately 2,000 litres."}, "kn": {"title": "ನಾಳೆ ಮಳೆಯ ನಿರೀಕ್ಷೆ", "text": "ನೀರಾವರಿ ಮುಂದೂಡಿ ಮತ್ತು ಸುಮಾರು 2,000 ಲೀಟರ್ ಉಳಿಸಿ."}, "hi": {"title": "कल बारिश की संभावना", "text": "सिंचाई रोकें और लगभग 2,000 लीटर बचाएं।"}},
        {"en": {"title": "Scout for leaf blast", "text": "Check lower leaves after rainfall."}, "kn": {"title": "ಎಲೆ ಅಂಗಮಾರಿಗಾಗಿ ಪರಿಶೀಲಿಸಿ", "text": "ಮಳೆಯ ನಂತರ ಕೆಳಗಿನ ಎಲೆಗಳನ್ನು ಪರಿಶೀಲಿಸಿ."}, "hi": {"title": "लीफ ब्लास्ट की जांच करें", "text": "बारिश के बाद निचली पत्तियों की जांच करें।"}},
        {"en": {"title": "Keep nitrogen balanced", "text": "Excess nitrogen can increase disease pressure."}, "kn": {"title": "ಸಮತೋಲಿತ ಸಾರಜನಕ ಬಳಸಿ", "text": "ಹೆಚ್ಚಿನ ಸಾರಜನಕವು ಕೀಟ ಮತ್ತು ರೋಗದ ಒತ್ತಡ ಹೆಚ್ಚಿಸಬಹುದು."}, "hi": {"title": "नाइट्रोजन संतुलित रखें", "text": "अधिक नाइट्रोजन से कीट और रोग का खतरा बढ़ सकता है।"}},
    ],
    [
        {"en": {"title": "Check field water level", "text": "Maintain a shallow layer and avoid unnecessary flooding."}, "kn": {"title": "ಹೊಲದ ನೀರಿನ ಮಟ್ಟ ಪರಿಶೀಲಿಸಿ", "text": "ಕಡಿಮೆ ನೀರಿನ ಪದರ ಇರಿಸಿ ಮತ್ತು ಅನಗತ್ಯವಾಗಿ ತುಂಬಿಸಬೇಡಿ."}, "hi": {"title": "खेत का पानी जांचें", "text": "कम पानी रखें और अनावश्यक जलभराव से बचें।"}},
        {"en": {"title": "Inspect for stem borer", "text": "Look for dead hearts and white heads in tillers."}, "kn": {"title": "ಕಾಂಡ ಕೊರೆಯುವ ಹುಳು ಪರಿಶೀಲಿಸಿ", "text": "ಹೊಡೆಯುವ ಹಂತದಲ್ಲಿ ಒಣಗಿದ ಮಧ್ಯ ಎಲೆಗಳನ್ನು ನೋಡಿ."}, "hi": {"title": "तना छेदक की जांच करें", "text": "कलियों में सूखे मध्य पत्ते और सफेद बालियां देखें।"}},
        {"en": {"title": "Use safe field scouting", "text": "Walk in a zigzag pattern and record affected plants."}, "kn": {"title": "ಸುರಕ್ಷಿತ ಹೊಲ ಪರಿಶೀಲನೆ ಮಾಡಿ", "text": "ಜಿಗ್‌ಜಾಗ್ ರೀತಿಯಲ್ಲಿ ನಡೆದು ಬಾಧಿತ ಸಸಿಗಳನ್ನು ದಾಖಲಿಸಿ."}, "hi": {"title": "सुरक्षित खेत निरीक्षण करें", "text": "जिगजैग तरीके से चलें और प्रभावित पौधों को दर्ज करें।"}},
    ],
    [
        {"en": {"title": "Protect flowering crop", "text": "Do not allow water stress during flowering."}, "kn": {"title": "ಹೂ ಬಿಡುವ ಬೆಳೆಯನ್ನು ರಕ್ಷಿಸಿ", "text": "ಹೂ ಬಿಡುವಾಗ ನೀರಿನ ಕೊರತೆ ಆಗದಂತೆ ನೋಡಿಕೊಳ್ಳಿ."}, "hi": {"title": "फूल वाली फसल बचाएं", "text": "फूल आने के समय पानी की कमी न होने दें।"}},
        {"en": {"title": "Scout for hopper", "text": "Inspect the base of tillers before spraying anything."}, "kn": {"title": "ಹಾಪರ್ ಕೀಟ ಪರಿಶೀಲಿಸಿ", "text": "ಔಷಧಿ ಸಿಂಪಡಿಸುವ ಮೊದಲು ಹೊಡೆಗಳ ಬುಡ ಪರಿಶೀಲಿಸಿ."}, "hi": {"title": "हॉपर की जांच करें", "text": "दवा छिड़कने से पहले कलियों के आधार की जांच करें।"}},
        {"en": {"title": "Keep the field clean", "text": "Remove volunteer rice plants and maintain field hygiene."}, "kn": {"title": "ಹೊಲವನ್ನು ಸ್ವಚ್ಛವಾಗಿಡಿ", "text": "ಸ್ವಯಂ ಬೆಳೆದ ಭತ್ತದ ಸಸಿಗಳನ್ನು ತೆಗೆದು ಹೊಲ ಸ್ವಚ್ಛವಾಗಿಡಿ."}, "hi": {"title": "खेत साफ रखें", "text": "अपने आप उगे धान के पौधे हटाकर खेत साफ रखें।"}},
    ],
]


def password_hash(password):
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def load_users():
    configured_user = os.environ.get("PADDY_USER")
    configured_password = os.environ.get("PADDY_PASSWORD")
    if USERS_FILE.exists():
        try:
            users = json.loads(USERS_FILE.read_text(encoding="utf-8"))
            if configured_user and configured_password:
                users[configured_user] = {"password_hash": password_hash(configured_password), "name": "Farmer"}
            return users
        except (json.JSONDecodeError, OSError):
            pass
    return {LOGIN_USER: {"password_hash": password_hash(LOGIN_PASSWORD), "name": "Ravi"}}


def save_users(users):
    USERS_FILE.write_text(json.dumps(users, indent=2), encoding="utf-8")


def predict_rain(weather):
    """Estimate rain likelihood from current conditions; no external AI key required."""
    score = float(weather.get("rain_probability", 0)) * 0.35
    factors = []
    humidity = float(weather.get("humidity_percent", 0))
    clouds = float(weather.get("cloud_cover_percent", 0))
    pressure = float(weather.get("pressure_hpa", 1013))
    wind = float(weather.get("wind_kph", 0))
    recent_rain = float(weather.get("recent_rainfall_mm", 0))
    if humidity >= 80:
        score += 20
        factors.append("high humidity")
    elif humidity >= 65:
        score += 12
        factors.append("moderate humidity")
    if clouds >= 75:
        score += 20
        factors.append("heavy cloud cover")
    elif clouds >= 50:
        score += 12
        factors.append("increasing cloud cover")
    if pressure <= 1008:
        score += 15
        factors.append("low atmospheric pressure")
    elif pressure <= 1012:
        score += 8
        factors.append("slightly low pressure")
    if 8 <= wind <= 25:
        score += 8
        factors.append("moisture-carrying wind")
    if recent_rain >= 2:
        score += 7
        factors.append("recent rainfall pattern")
    probability = max(5, min(95, round(score)))
    category = "High" if probability >= 70 else "Moderate" if probability >= 45 else "Low"
    timing = "within 24 hours" if category == "High" else "possibly within 24 hours" if category == "Moderate" else "unlikely in the next 24 hours"
    return {
        "probability": probability,
        "category": category,
        "timing": timing,
        "model": "Paddy Mitra AI condition model",
        "factors": factors or ["limited rain signals"],
    }


def live_weather(district):
    """Fetch changing weather conditions, falling back when the device is offline."""
    now = time.time()
    today = date.today().isoformat()
    with WEATHER_CACHE_LOCK:
        cached = WEATHER_CACHE.get(district)
        if cached and cached["date"] == today and now - cached["time"] < 600:
            return dict(cached["weather"])
    latitude, longitude = DISTRICT_COORDINATES.get(district, (12.52, 76.90))
    query = urllib.parse.urlencode({
        "latitude": latitude, "longitude": longitude,
        "current": "temperature_2m,relative_humidity_2m,cloud_cover,wind_speed_10m,surface_pressure,precipitation",
        "daily": "precipitation_probability_max,precipitation_sum",
        "forecast_days": 1, "timezone": "auto",
    })
    try:
        with urllib.request.urlopen(f"https://api.open-meteo.com/v1/forecast?{query}", timeout=4) as response:
            payload = json.loads(response.read().decode("utf-8"))
        current = payload["current"]
        daily = payload["daily"]
        weather = {
            "district": district,
            "forecast_date": daily["time"][0],
            "updated_at": date.today().isoformat(),
            "temperature_c": round(current["temperature_2m"]),
            "humidity_percent": round(current["relative_humidity_2m"]),
            "cloud_cover_percent": round(current["cloud_cover"]),
            "wind_kph": round(current["wind_speed_10m"]),
            "pressure_hpa": round(current["surface_pressure"]),
            "recent_rainfall_mm": round(current["precipitation"], 1),
            "rain_probability": round(daily["precipitation_probability_max"][0]),
            "rainfall_mm": round(daily["precipitation_sum"][0], 1),
            "advice": "Delay irrigation if useful rain is likely today." if daily["precipitation_probability_max"][0] >= 50 else "Check soil moisture before irrigating.",
            "source": "Open-Meteo live weather",
        }
    except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError):
        weather = dict(WEATHER_DATA)
        weather["district"] = district
        weather["forecast_date"] = today
        weather["updated_at"] = today
        weather["source"] = "Offline fallback values"
    with WEATHER_CACHE_LOCK:
        WEATHER_CACHE[district] = {"date": today, "time": now, "weather": weather}
    return weather


USERS = load_users()


class DashboardHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def do_GET(self):
        path = urlparse(self.path).path
        if path in ("/", "/index.html"):
            self.path = "/login.html"
            return super().do_GET()
        if path == "/register":
            self.path = "/register.html"
            return super().do_GET()
        if path == "/dashboard" or path == "/dashboard.html":
            if not self.is_authenticated():
                self.redirect("/")
                return
            self.path = "/dashboard.html"
            return super().do_GET()
        if path == "/api/health":
            self.send_json({"status": "ok", "service": "paddy-mitra"})
            return
        if path == "/api/session":
            self.send_json({"authenticated": self.is_authenticated()})
            return
        if path.startswith("/api/") and not self.is_authenticated():
            self.send_json({"error": "Authentication required"}, 401)
            return
        if path == "/api/state":
            self.send_json(FIELD_STATE)
            return
        if path == "/api/districts":
            self.send_json({"districts": KARNATAKA_DISTRICTS})
            return
        if path == "/api/instructions":
            self.send_json({"instructions": IRRIGATION_INSTRUCTIONS})
            return
        if path == "/api/water-manager":
            self.send_json({"state": FIELD_STATE, "instructions": IRRIGATION_INSTRUCTIONS})
            return
        if path == "/api/paddy-doctor":
            self.send_json({"diagnosis_available": FIELD_STATE["ai_detection_on"], "diseases": DISEASE_CATALOG})
            return
        if path == "/api/weather":
            weather = live_weather(FIELD_STATE["district"])
            weather["prediction"] = predict_rain(weather)
            self.send_json(weather)
            return
        if path == "/api/calendar":
            calendar = dict(CROP_CALENDAR)
            calendar["district"] = FIELD_STATE["district"]
            self.send_json(calendar)
            return
        if path == "/api/settings":
            self.send_json(USER_SETTINGS.get(self.session_token(), DEFAULT_SETTINGS))
            return
        if path == "/api/advisories":
            today = date.today()
            cycle_index = today.toordinal() % len(DAILY_ADVISORIES)
            self.send_json({"date": today.isoformat(), "cycle": cycle_index + 1, "items": DAILY_ADVISORIES[cycle_index]})
            return
        return super().do_GET()

    def do_POST(self):
        path = urlparse(self.path).path
        if path == "/api/login":
            try:
                length = int(self.headers.get("Content-Length", "0"))
                body = json.loads(self.rfile.read(length) or b"{}")
                username = body["username"]
                password = body["password"]
            except (KeyError, json.JSONDecodeError):
                self.send_json({"error": "Username and password are required"}, 400)
                return
            user = USERS.get(username)
            if not user or user["password_hash"] != password_hash(password):
                self.send_json({"error": "Invalid username or password"}, 401)
                return
            token = secrets.token_urlsafe(32)
            SESSIONS.add(token)
            self.send_json({"status": "ok", "redirect": "/dashboard"}, 200,
                           {"Set-Cookie": f"paddy_session={token}; HttpOnly; SameSite=Lax; Path=/"})
            return
        if path == "/api/register":
            try:
                length = int(self.headers.get("Content-Length", "0"))
                body = json.loads(self.rfile.read(length) or b"{}")
                username = body["username"].strip().lower()
                password = body["password"]
                name = body.get("name", "Farmer").strip() or "Farmer"
                if len(username) < 3 or len(password) < 6:
                    raise ValueError("Username must be 3 characters and password 6 characters")
                if not username.replace("_", "").isalnum():
                    raise ValueError("Username contains invalid characters")
            except (KeyError, TypeError, ValueError, json.JSONDecodeError) as error:
                self.send_json({"error": str(error) or "Enter valid registration details"}, 400)
                return
            with USERS_LOCK:
                if username in USERS:
                    self.send_json({"error": "Username already exists"}, 409)
                    return
                USERS[username] = {"password_hash": password_hash(password), "name": name}
                save_users(USERS)
            self.send_json({"status": "ok", "redirect": "/"})
            return
        if path == "/api/logout":
            token = self.session_token()
            if token:
                SESSIONS.discard(token)
            self.send_json({"status": "ok"}, 200,
                           {"Set-Cookie": "paddy_session=; Max-Age=0; HttpOnly; SameSite=Lax; Path=/"})
            return
        if path.startswith("/api/") and not self.is_authenticated():
            self.send_json({"error": "Authentication required"}, 401)
            return
        if path == "/api/district":
            try:
                length = int(self.headers.get("Content-Length", "0"))
                body = json.loads(self.rfile.read(length) or b"{}")
                district = body["district"]
                if district not in KARNATAKA_DISTRICTS:
                    raise ValueError("unknown district")
            except (ValueError, KeyError, json.JSONDecodeError):
                self.send_json({"error": "Choose a valid Karnataka district"}, 400)
                return
            FIELD_STATE["district"] = district
            self.send_json({"status": "ok", "state": FIELD_STATE})
            return

        if path == "/api/diagnosis":
            try:
                length = int(self.headers.get("Content-Length", "0"))
                body = json.loads(self.rfile.read(length) or b"{}")
                query = body.get("symptom", "").lower()
            except (json.JSONDecodeError, AttributeError):
                self.send_json({"error": "Provide a symptom description"}, 400)
                return
            matches = [item for item in DISEASE_CATALOG if any(word in query for word in item["name"].lower().split())]
            self.send_json({"matches": matches, "message": "Confirm any diagnosis with an agronomist."})
            return

        if path == "/api/expert-requests":
            try:
                length = int(self.headers.get("Content-Length", "0"))
                body = json.loads(self.rfile.read(length) or b"{}")
                message = body["message"].strip()
                if not message:
                    raise ValueError("Message is required")
            except (KeyError, TypeError, ValueError, json.JSONDecodeError) as error:
                self.send_json({"error": str(error) or "Message is required"}, 400)
                return
            self.send_json({"status": "received", "message": "An agronomist will contact you soon."})
            return

        if path == "/api/settings":
            try:
                length = int(self.headers.get("Content-Length", "0"))
                body = json.loads(self.rfile.read(length) or b"{}")
                settings = {
                    "language": body.get("language", "en"),
                    "notifications": bool(body.get("notifications", True)),
                    "auto_irrigation": bool(body.get("auto_irrigation", True)),
                }
            except json.JSONDecodeError:
                self.send_json({"error": "Invalid settings"}, 400)
                return
            USER_SETTINGS[self.session_token()] = settings
            self.send_json({"status": "ok", "settings": settings})
            return

        if path not in ("/api/borewell", "/api/ai-detection"):
            self.send_json({"error": "Endpoint not found"}, 404)
            return

        try:
            length = int(self.headers.get("Content-Length", "0"))
            body = json.loads(self.rfile.read(length) or b"{}")
            enabled = body["enabled"]
            if not isinstance(enabled, bool):
                raise ValueError("enabled must be true or false")
        except (ValueError, KeyError, json.JSONDecodeError):
            self.send_json({"error": "Request must contain boolean enabled"}, 400)
            return

        state_key = "borewell_on" if path == "/api/borewell" else "ai_detection_on"
        FIELD_STATE[state_key] = enabled
        self.send_json({"status": "ok", "state": FIELD_STATE})

    def end_headers(self):
        origin = self.headers.get("Origin")
        self.send_header("Access-Control-Allow-Origin", origin or "*")
        if origin:
            self.send_header("Access-Control-Allow-Credentials", "true")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(204)
        self.end_headers()

    def session_token(self):
        cookie_header = self.headers.get("Cookie", "")
        for cookie in cookie_header.split(";"):
            name, _, value = cookie.strip().partition("=")
            if name == "paddy_session":
                return value
        return None

    def is_authenticated(self):
        return self.session_token() in SESSIONS

    def redirect(self, location):
        self.send_response(302)
        self.send_header("Location", location)
        self.end_headers()

    def send_json(self, data, status=200, extra_headers=None):
        payload = json.dumps(data).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Cache-Control", "no-store")
        for name, value in (extra_headers or {}).items():
            self.send_header(name, value)
        self.end_headers()
        self.wfile.write(payload)


if __name__ == "__main__":
    host = os.environ.get("PADDY_HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", os.environ.get("PADDY_PORT", "8000")))
    local_ip = socket.gethostbyname(socket.gethostname())
    print(f"Paddy Mitra dashboard running at http://{local_ip}:{port}")
    print(f"Phone access on the same Wi-Fi: http://{local_ip}:{port}")
    print(f"Health check: http://{local_ip}:{port}/api/health")
    ThreadingHTTPServer((host, port), DashboardHandler).serve_forever()
