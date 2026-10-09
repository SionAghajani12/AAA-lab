"""Tiny 'finance system' demonstrating AAA with Keycloak.
Authentication -> Keycloak (password + OTP)
Authorization  -> realm roles checked on every route
Accounting     -> JSON audit log in ../logs/audit.log (shipped to Loki)
"""
import os, json, time
from functools import wraps
from urllib.parse import quote

import jwt  # PyJWT, only used to READ role claims
from flask import Flask, session, redirect, url_for, request, render_template_string, Response
from authlib.integrations.flask_client import OAuth

KEYCLOAK = os.environ.get("KEYCLOAK_URL", "http://localhost:8080/realms/company")
CLIENT_ID = os.environ.get("CLIENT_ID", "finance-app")
CLIENT_SECRET = os.environ["CLIENT_SECRET"]  # Keycloak > Clients > finance-app > Credentials
APP_URL = "http://localhost:5000"
LOG_FILE = os.path.join(os.path.dirname(__file__), "..", "logs", "audit.log")

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "lab-only-secret")

oauth = OAuth(app)
oauth.register(
    name="keycloak",
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET,
    server_metadata_url=f"{KEYCLOAK}/.well-known/openid-configuration",
    client_kwargs={"scope": "openid profile email"},
)

# ---------- Accounting ----------
def audit(action, result, **extra):
    entry = {
        "time": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "user": session.get("user", "anonymous"),
        "action": action,
        "result": result,
        "ip": request.remote_addr,
        **extra,
    }
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    with open(LOG_FILE, "a") as f:
        f.write(json.dumps(entry) + "\n")

PAGE = """
<!doctype html><title>Finance System</title>
<body style="font-family:sans-serif;max-width:640px;margin:40px auto">
<h1>Finance System</h1>
{% if user %}<p>Signed in as <b>{{ user }}</b> &middot; roles: {{ roles or 'none' }}
 &middot; <a href="/logout">Log out</a></p>{% endif %}
<p><a href="/">Home</a> | <a href="/report">Report</a> | <a href="/admin">Admin</a></p><hr>
{{ body|safe }}
</body>"""

def render(body):
    return render_template_string(PAGE, user=session.get("user"), roles=session.get("roles"), body=body)

# ---------- Authentication / Authorization helpers ----------
def login_required(f):
    @wraps(f)
    def wrapper(*a, **kw):
        if "user" not in session:
            audit(f"access:{request.path}", "denied", reason="not_authenticated")
            return redirect(url_for("login"))
        return f(*a, **kw)
    return wrapper

def roles_required(*allowed):
    def deco(f):
        @wraps(f)
        @login_required
        def wrapper(*a, **kw):
            if not set(allowed) & set(session.get("roles", [])):
                audit(f"access:{request.path}", "denied",
                      reason="missing_role", needed=list(allowed))
                return render(f"<h2>403 Forbidden</h2><p>You need one of: <b>{', '.join(allowed)}</b>. "
                              "This attempt was recorded.</p>"), 403
            return f(*a, **kw)
        return wrapper
    return deco

# ---------- Routes ----------
@app.route("/")
def home():
    if "user" in session:
        audit("view_home", "allowed")
        return render("<p>Welcome. Try the Report and Admin pages.</p>")
    return render('<p>You are not signed in. <a href="/login">Log in with Keycloak</a></p>')

@app.route("/login")
def login():
    return oauth.keycloak.authorize_redirect(f"{APP_URL}/callback")

@app.route("/callback")
def callback():
    token = oauth.keycloak.authorize_access_token()
    info = token["userinfo"]
    access = jwt.decode(token["access_token"], options={"verify_signature": False})
    session["user"] = info.get("preferred_username", "unknown")
    session["roles"] = access.get("realm_access", {}).get("roles", [])
    session["id_token"] = token["id_token"]
    audit("login", "allowed", roles=session["roles"])
    return redirect("/")

@app.route("/logout")
def logout():
    audit("logout", "allowed")
    idt = session.get("id_token", "")
    session.clear()
    return redirect(f"{KEYCLOAK}/protocol/openid-connect/logout"
                    f"?id_token_hint={idt}&post_logout_redirect_uri={quote(APP_URL + '/')}")

@app.route("/report")
@roles_required("finance-viewer", "finance-admin")
def report():
    audit("view_report_page", "allowed")
    return render('<h2>Q3 Financial Report</h2><p>Revenue: $4.2M</p>'
                  '<p><a href="/report/download">Download CSV</a></p>')

@app.route("/report/download")
@roles_required("finance-viewer", "finance-admin")
def download():
    audit("download_report", "allowed", file="q3_report.csv")
    csv = "quarter,revenue,cost\nQ3,4200000,3100000\n"
    return Response(csv, mimetype="text/csv",
                    headers={"Content-Disposition": "attachment; filename=q3_report.csv"})

@app.route("/admin")
@roles_required("finance-admin")
def admin():
    audit("view_admin_page", "allowed")
    return render("<h2>Admin</h2><p>Here you could change budgets and approve payments.</p>")

if __name__ == "__main__":
    app.run(port=5000, debug=True)
