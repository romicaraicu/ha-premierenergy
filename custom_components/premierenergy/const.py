"""Constante pentru integrarea Premier Energy."""

from __future__ import annotations

DOMAIN = "premierenergy"
MANUFACTURER = "Premier Energy"

# --- Azure AD B2C (extrase din aplicația web app.premierenergy.ro) ---
B2C_HOST = "https://login.premierenergy.ro"
B2C_TENANT = "premierenergyrob2c.onmicrosoft.com"
B2C_POLICY = "B2C_1A_SIGNUP_SIGNIN"
B2C_CLIENT_ID = "5dc97de8-713e-431b-8d05-4319c180377a"
B2C_API_SCOPE = "https://login.premierenergy.ro/4fea07ee-cea1-441e-a2e3-382276f2f19e/access"
B2C_SCOPES = f"openid offline_access {B2C_API_SCOPE}"
# Redirect URI al aplicației web (client de tip SPA). B2C cere header Origin
# la endpoint-ul de token, iar refresh token-ul expiră după 24h - după aceea
# integrarea se reautentifică automat cu email + parolă.
B2C_REDIRECT_URI = "https://app.premierenergy.ro/"
B2C_ORIGIN = "https://app.premierenergy.ro"
B2C_AUTHORITY = f"{B2C_HOST}/{B2C_TENANT}/{B2C_POLICY}"
B2C_AUTHORIZE_URL = f"{B2C_AUTHORITY}/oauth2/v2.0/authorize"
B2C_TOKEN_URL = f"{B2C_AUTHORITY}/oauth2/v2.0/token"

# --- API ---
API_BASE_URL = "https://app.premierenergy.ro"

# --- Config entry ---
CONF_PODS = "pods"
CONF_SCAN_INTERVAL = "scan_interval"
DEFAULT_SCAN_INTERVAL_HOURS = 6
MIN_SCAN_INTERVAL_HOURS = 1
MAX_SCAN_INTERVAL_HOURS = 24

# Toleranța folosită și de aplicația web pentru sume (lei)
AMOUNT_EPSILON = 0.005

SERVICE_SUBMIT_READING = "trimite_index"
ATTR_POD = "pod"
ATTR_INDEX = "index"
