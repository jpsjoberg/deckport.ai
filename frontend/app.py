import os
import secrets
import time
import uuid
import logging
from functools import wraps
from urllib.parse import urlencode

import requests
from flask import Flask, render_template, request, redirect, url_for, make_response, g

# Load environment variables from .env file if it exists
def load_env_file():
    env_path = os.path.join(os.path.dirname(__file__), '.env')
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ.setdefault(key.strip(), value.strip())

load_env_file()

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-key-change-in-production")
API_BASE = os.environ.get("API_BASE", "http://127.0.0.1:8002")

# Add path for imports
import sys
import os
sys.path.append(os.path.dirname(__file__))

# Register admin blueprint
from admin_routes import admin_bp
from console_deployment import deploy_bp
from admin_routes.card_generation_ai import card_gen_bp
from admin_routes.card_set_generator_ai import card_set_gen_bp

app.register_blueprint(admin_bp)
app.register_blueprint(deploy_bp)
app.register_blueprint(card_gen_bp)
app.register_blueprint(card_set_gen_bp)

# Register asset generation blueprint
from admin_routes.asset_generation import asset_gen_bp
app.register_blueprint(asset_gen_bp)

# Register card batch production blueprint
# from admin_routes.card_batch_production import card_batch_bp
# app.register_blueprint(card_batch_bp)

# Register card database production blueprint (database-only)
from admin_routes.card_database_production import card_db_bp
app.register_blueprint(card_db_bp)

# Register print portal blueprint
from admin_routes.print_portal import print_portal_bp
app.register_blueprint(print_portal_bp)


# ---------- Logging setup ----------

LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger("frontend")


@app.before_request
def _before_request_logging():
    g._t0 = time.time()
    # honor upstream request id if present
    rid = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    g.request_id = rid
    # Basic start log
    logger.info(
        "request.start",
        extra={
            "request_id": rid,
            "method": request.method,
            "path": request.path,
            "remote": request.headers.get("X-Forwarded-For", request.remote_addr),
            "ua": request.headers.get("User-Agent", ""),
        },
    )


@app.after_request
def _after_request_logging(response):
    try:
        dur_ms = int((time.time() - getattr(g, "_t0", time.time())) * 1000)
    except Exception:
        dur_ms = -1
    # Attach request id header
    if hasattr(g, "request_id"):
        response.headers["X-Request-ID"] = g.request_id
    logger.info(
        "request.end",
        extra={
            "request_id": getattr(g, "request_id", None),
            "method": request.method,
            "path": request.path,
            "status": response.status_code,
            "duration_ms": dur_ms,
        },
    )
    return response


@app.errorhandler(Exception)
def _unhandled_error(err):
    dur_ms = int((time.time() - getattr(g, "_t0", time.time())) * 1000)
    logger.exception(
        "request.error",
        extra={
            "request_id": getattr(g, "request_id", None),
            "method": request.method,
            "path": request.path,
            "duration_ms": dur_ms,
        },
    )
    return ("Internal Server Error", 500)


# Mock catalog for scaffolding (replace with API calls)
CATALOG = [
    {
        "product_sku": "RADIANT-001",
        "name": "Solar Vanguard",
        "rarity": "EPIC",
        "category": "CREATURE",
        "colors": ["RADIANT"],
    },
    {
        "product_sku": "AZURE-014",
        "name": "Tidecaller Sigil",
        "rarity": "RARE",
        "category": "ENCHANTMENT",
        "colors": ["AZURE"],
    },
]


def _get_player_jwt() -> str | None:
    return request.cookies.get("player_jwt")


def _auth_headers() -> dict:
    token = _get_player_jwt()
    return {"Authorization": f"Bearer {token}"} if token else {}


def require_auth(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        if not _get_player_jwt():
            return redirect(url_for("login", next=request.path))
        return view(*args, **kwargs)

    return wrapper


def _csrf_get_or_set(resp=None):
    token = request.cookies.get("csrf")
    if not token:
        token = secrets.token_urlsafe(32)
        if resp is None:
            resp = make_response()
        resp.set_cookie("csrf", token, httponly=True, samesite="Lax")
    return token, resp


def _csrf_valid(form_token: str | None) -> bool:
    return form_token and form_token == request.cookies.get("csrf")


def api_get(path: str, params: dict | None = None, headers: dict | None = None):
    t0 = time.time()
    rid = getattr(g, "request_id", str(uuid.uuid4()))
    hdrs = {"X-Request-ID": rid, **(headers or {})}
    url = f"{API_BASE}{path}"
    try:
        r = requests.get(url, params=params, headers=hdrs, timeout=5)
        elapsed = int((time.time() - t0) * 1000)
        logger.info(
            "api.get",
            extra={"request_id": rid, "url": url, "status": r.status_code, "duration_ms": elapsed},
        )
        r.raise_for_status()
        return r.json()
    except Exception as e:
        elapsed = int((time.time() - t0) * 1000)
        logger.exception(
            "api.get.error",
            extra={"request_id": rid, "url": url, "duration_ms": elapsed, "params": (params or {})},
        )
        return None


def api_post(path: str, json: dict | None = None, headers: dict | None = None):
    t0 = time.time()
    rid = getattr(g, "request_id", str(uuid.uuid4()))
    hdrs = {"X-Request-ID": rid, **(headers or {})}
    url = f"{API_BASE}{path}"
    try:
        r = requests.post(url, json=json or {}, headers=hdrs, timeout=10)
        elapsed = int((time.time() - t0) * 1000)
        logger.info(
            "api.post",
            extra={"request_id": rid, "url": url, "status": r.status_code, "duration_ms": elapsed},
        )
        r.raise_for_status()
        return r.json()
    except Exception:
        elapsed = int((time.time() - t0) * 1000)
        logger.exception(
            "api.post.error",
            extra={"request_id": rid, "url": url, "duration_ms": elapsed, "json": (json or {})},
        )
        return None


@app.get("/")
def landing():
    return render_template("index_enhanced.html")

@app.get("/news")
def news():
    return render_template("news.html")

@app.get("/videos")
def videos():
    return render_template("videos.html")

@app.get("/news/<slug>")
def article_detail(slug):
    return render_template("article.html")

@app.get("/videos/<slug>")
def video_detail(slug):
    return render_template("video.html")


@app.get("/cards")
def cards_list():
    # Get all filter parameters
    q = request.args.get("q", "").strip()
    category = request.args.get("category", "").upper()
    color = request.args.get("color", "").upper()
    rarity = request.args.get("rarity", "").upper()
    card_set = request.args.get("card_set", "").lower().strip()
    
    # Pagination parameters
    page = request.args.get("page", 1, type=int)
    page_size = request.args.get("page_size", 24, type=int)  # Default to 24 cards per page
    page_size = min(page_size, 100)  # Max 100 per page
    
    # Advanced filters
    mana_cost_min = request.args.get("mana_cost_min", type=int)
    mana_cost_max = request.args.get("mana_cost_max", type=int)
    energy_cost_min = request.args.get("energy_cost_min", type=int)
    energy_cost_max = request.args.get("energy_cost_max", type=int)
    attack_min = request.args.get("attack_min", type=int)
    attack_max = request.args.get("attack_max", type=int)
    health_min = request.args.get("health_min", type=int)
    health_max = request.args.get("health_max", type=int)
    has_artwork = request.args.get("has_artwork")
    has_video = request.args.get("has_video")

    # Get filter options from API
    filter_data = api_get("/v1/catalog/filters")
    if filter_data:
        categories = filter_data.get("categories", [])
        colors = filter_data.get("colors", [])
        rarities = filter_data.get("rarities", [])
        card_sets = filter_data.get("card_sets", [])
        stat_ranges = filter_data.get("stat_ranges", {})
    else:
        # Fallback filter options
        categories = ["CREATURE", "STRUCTURE", "ACTION_FAST", "ACTION_SLOW", "EQUIPMENT", "ENCHANTMENT", "HERO"]
        colors = ["CRIMSON", "AZURE", "VERDANT", "OBSIDIAN", "RADIANT"]
        rarities = ["COMMON", "RARE", "EPIC", "LEGENDARY"]
        card_sets = ["open_portal"]
        stat_ranges = {
            "mana_cost": {"min": 0, "max": 10},
            "energy_cost": {"min": 0, "max": 6},
            "attack": {"min": 0, "max": 15},
            "health": {"min": 0, "max": 20}
        }

    # Build API parameters with all filters and pagination
    params = {
        "q": q, "category": category, "color": color, "rarity": rarity, "card_set": card_set,
        "mana_cost_min": mana_cost_min, "mana_cost_max": mana_cost_max,
        "energy_cost_min": energy_cost_min, "energy_cost_max": energy_cost_max,
        "attack_min": attack_min, "attack_max": attack_max,
        "health_min": health_min, "health_max": health_max,
        "has_artwork": has_artwork, "has_video": has_video,
        "page": page, "page_size": page_size
    }
    
    # Remove None values
    params = {k: v for k, v in params.items() if v is not None and v != ""}
    
    # Get filtered cards from API
    api_data = api_get("/v1/catalog/cards", params=params)
    items = api_data.get("items", []) if api_data else []
    
    # Extract pagination info
    total = api_data.get("total", 0) if api_data else 0
    has_more = api_data.get("has_more", False) if api_data else False
    total_pages = (total + page_size - 1) // page_size if total > 0 else 1
    
    return render_template("cards_list.html", 
                         items=items, 
                         q=q, category=category, color=color, rarity=rarity, card_set=card_set,
                         mana_cost_min=mana_cost_min, mana_cost_max=mana_cost_max,
                         energy_cost_min=energy_cost_min, energy_cost_max=energy_cost_max,
                         attack_min=attack_min, attack_max=attack_max,
                         health_min=health_min, health_max=health_max,
                         has_artwork=has_artwork, has_video=has_video,
                         categories=categories, colors=colors, rarities=rarities, card_sets=card_sets,
                         stat_ranges=stat_ranges,
                         # Pagination data
                         page=page, page_size=page_size, total=total, total_pages=total_pages, has_more=has_more)


@app.get("/cards/<product_sku>")
def card_detail(product_sku: str):
    data = api_get(f"/v1/catalog/cards/{product_sku}")
    card = data if data else next((c for c in CATALOG if c["product_sku"].lower() == product_sku.lower()), None)
    if not card:
        return render_template("404.html"), 404
    return render_template("card_detail.html", card=card)


@app.get("/login")
def login():
    token, resp = _csrf_get_or_set()
    if resp is None:
        resp = make_response(render_template("login.html", error=None, csrf=token))
    else:
        # Update the existing response with the rendered template
        resp = make_response(render_template("login.html", error=None, csrf=token))
        resp.set_cookie("csrf", token, httponly=True, samesite="Lax")
    return resp


@app.post("/login")
def login_post():
    if not _csrf_valid(request.form.get("csrf")):
        return render_template("login.html", error="Invalid session, please retry.", csrf=request.cookies.get("csrf")), 400
    email = request.form.get("email", "").strip()
    password = request.form.get("password", "")
    next_url = request.args.get("next") or url_for("landing")
    if not email or not password:
        return render_template("login.html", error="Email and password required", csrf=request.cookies.get("csrf"))
    data = api_post("/v1/auth/player/login", json={"email": email, "password": password})
    if not data or "access_token" not in data:
        return render_template("login.html", error="Login failed", csrf=request.cookies.get("csrf")), 401
    resp = make_response(redirect(next_url))
    resp.set_cookie("player_jwt", data["access_token"], httponly=True, samesite="Lax")
    return resp


@app.get("/register")
def register():
    token, resp = _csrf_get_or_set()
    if resp is None:
        resp = make_response(render_template("register.html", error=None, csrf=token))
    else:
        # Update the existing response with the rendered template
        resp = make_response(render_template("register.html", error=None, csrf=token))
        resp.set_cookie("csrf", token, httponly=True, samesite="Lax")
    return resp


@app.post("/register")
def register_post():
    if not _csrf_valid(request.form.get("csrf")):
        return render_template("register.html", error="Invalid session, please retry.", csrf=request.cookies.get("csrf")), 400
    email = request.form.get("email", "").strip()
    password = request.form.get("password", "")
    if not email or not password:
        return render_template("register.html", error="Email and password required", csrf=request.cookies.get("csrf"))
    data = api_post("/v1/auth/player/register", json={"email": email, "password": password})
    if not data or "access_token" not in data:
        return render_template("register.html", error="Registration failed", csrf=request.cookies.get("csrf")), 400
    resp = make_response(redirect(url_for("landing")))
    resp.set_cookie("player_jwt", data["access_token"], httponly=True, samesite="Lax")
    return resp


@app.get("/shop")
def shop():
    # Placeholder: render Buy Now buttons (wired to API Checkout Session)
    bundles = [
        {"product_sku": "BUNDLE-STARTER", "name": "Starter Bundle", "price": "49.00", "currency": "USD"},
        {"product_sku": "BUNDLE-RADIANT", "name": "Radiant Bundle", "price": "39.00", "currency": "USD"},
    ]
    resp = make_response(render_template("shop.html", bundles=bundles, csrf=request.cookies.get("csrf")))
    _csrf_get_or_set(resp)
    return resp


@app.get("/checkout/success")
def checkout_success():
    return render_template("checkout_success.html")


@app.get("/checkout/cancel")
def checkout_cancel():
    return render_template("checkout_cancel.html")


# Admin authentication routes
@app.get("/admin/login")
def admin_login():
    token, resp = _csrf_get_or_set()
    if resp is None:
        resp = make_response(render_template("admin_login.html", error=None, csrf=token))
    else:
        # Update the existing response with the rendered template
        resp = make_response(render_template("admin_login.html", error=None, csrf=token))
        resp.set_cookie("csrf", token, httponly=True, samesite="Lax")
    return resp


@app.post("/admin/login")
def admin_login_post():
    if not _csrf_valid(request.form.get("csrf")):
        return render_template("admin_login.html", error="Invalid session, please retry.", csrf=request.cookies.get("csrf")), 400
    email = request.form.get("email", "").strip()
    password = request.form.get("password", "")
    next_url = request.args.get("next") or "/admin/"
    if not email or not password:
        return render_template("admin_login.html", error="Email and password required", csrf=request.cookies.get("csrf"))
    
    # Use proper admin login endpoint
    data = api_post("/v1/auth/admin/login", json={"email": email, "password": password})
    if not data or "access_token" not in data:
        error_msg = data.get("error", "Admin login failed") if data else "Admin login failed"
        return render_template("admin_login.html", error=error_msg, csrf=request.cookies.get("csrf")), 401
    
    resp = make_response(redirect(next_url))
    resp.set_cookie("admin_jwt", data["access_token"], httponly=True, samesite="Lax", secure=True)
    return resp


def _get_admin_jwt() -> str | None:
    return request.cookies.get("admin_jwt")


def _admin_auth_headers() -> dict:
    token = _get_admin_jwt()
    return {"Authorization": f"Bearer {token}"} if token else {}


def require_admin_auth(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        if not _get_admin_jwt():
            return redirect(url_for("admin_login", next=request.path))
        return view(*args, **kwargs)
    return wrapper


@app.get("/logout")
def logout():
    """Logout and clear authentication cookies"""
    resp = make_response(redirect(url_for("login")))
    resp.set_cookie("player_jwt", "", expires=0)
    resp.set_cookie("admin_jwt", "", expires=0)
    return resp


@app.post("/shop/checkout")
def shop_checkout():
    if not _csrf_valid(request.form.get("csrf")):
        return redirect(url_for("shop"))
    product_sku = request.form.get("product_sku", "").strip()
    try:
        quantity = int(request.form.get("quantity", "1"))
    except Exception:
        quantity = 1
    if not product_sku or quantity < 1:
        return redirect(url_for("shop"))
    success_url = request.host_url.rstrip("/") + url_for("checkout_success")
    cancel_url = request.host_url.rstrip("/") + url_for("checkout_cancel")
    payload = {
        "items": [{"product_sku": product_sku, "quantity": quantity}],
        "success_url": success_url,
        "cancel_url": cancel_url,
    }
    data = api_post("/v1/shop/checkout/session", json=payload, headers=_auth_headers())
    if not data or "url" not in data:
        return redirect(url_for("shop"))
    return redirect(data["url"])


# Admin routes now handled by admin_bp blueprint


@app.get("/me")
@require_auth
def me_home():
    profile = api_get("/v1/me", headers=_auth_headers()) or {"display_name": "Player", "elo_rating": 1000}
    recent = api_get("/v1/me/matches", headers=_auth_headers()) or {"items": []}
    return render_template("me/index.html", profile=profile, recent=recent)


@app.get("/me/performance")
@require_auth
def me_performance():
    stats = api_get("/v1/me/stats", headers=_auth_headers()) or {
        "win_loss_draw": {"win": 0, "loss": 0, "draw": 0},
        "avg_turn_time_ms": 0,
        "play_window_expired_rate": 0.0,
    }
    return render_template("me/performance.html", stats=stats)


@app.get("/me/cards")
@require_auth
def me_cards():
    q = request.args.get("q", "")
    params = {"q": q} if q else None
    inv = api_get("/v1/me/inventory", params=params, headers=_auth_headers()) or {"cards": []}
    return render_template("me/cards.html", items=inv.get("cards", []), q=q)


# WSGI entrypoint
if __name__ == "__main__":
    app.run()
