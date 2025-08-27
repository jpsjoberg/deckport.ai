import os
import secrets
import time
import uuid
import logging
from functools import wraps
from urllib.parse import urlencode

import requests
from flask import Flask, render_template, request, redirect, url_for, make_response, g

app = Flask(__name__)
API_BASE = os.environ.get("API_BASE", "http://localhost:8000")


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


def api_patch(path: str, json: dict | None = None, headers: dict | None = None):
    t0 = time.time()
    rid = getattr(g, "request_id", str(uuid.uuid4()))
    hdrs = {"X-Request-ID": rid, **(headers or {})}
    url = f"{API_BASE}{path}"
    try:
        r = requests.patch(url, json=json or {}, headers=hdrs, timeout=10)
        elapsed = int((time.time() - t0) * 1000)
        logger.info(
            "api.patch",
            extra={"request_id": rid, "url": url, "status": r.status_code, "duration_ms": elapsed},
        )
        r.raise_for_status()
        return r.json()
    except Exception:
        elapsed = int((time.time() - t0) * 1000)
        logger.exception(
            "api.patch.error",
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
    q = request.args.get("q", "").lower().strip()
    category = request.args.get("category", "").upper()
    color = request.args.get("color", "").upper()
    rarity = request.args.get("rarity", "").upper()

    # Try API; fallback to mock
    params = {"q": q, "category": category, "color": color, "rarity": rarity}
    api_data = api_get("/v1/catalog/cards", params=params)
    items = api_data.get("items", []) if api_data else CATALOG
    return render_template("cards_list.html", items=items, q=q, category=category, color=color, rarity=rarity)


@app.get("/cards/<product_sku>")
def card_detail(product_sku: str):
    data = api_get(f"/v1/catalog/cards/{product_sku}")
    card = data if data else next((c for c in CATALOG if c["product_sku"].lower() == product_sku.lower()), None)
    if not card:
        return render_template("404.html"), 404
    return render_template("card_detail.html", card=card)


@app.get("/login")
def login():
    resp = make_response(render_template("login.html", error=None, csrf=request.cookies.get("csrf")))
    _csrf_get_or_set(resp)
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
    resp = make_response(render_template("register.html", error=None, csrf=request.cookies.get("csrf")))
    _csrf_get_or_set(resp)
    return resp


@app.post("/register")
def register_post():
    if not _csrf_valid(request.form.get("csrf")):
        return render_template("register.html", error="Invalid session, please retry.", csrf=request.cookies.get("csrf")), 400
    email = request.form.get("email", "").strip()
    password = request.form.get("password", "")
    display_name = request.form.get("display_name", "").strip()
    username = request.form.get("username", "").strip()
    phone_number = request.form.get("phone_number", "").strip()
    
    if not email or not password:
        return render_template("register.html", error="Email and password required", csrf=request.cookies.get("csrf"))
    
    # Prepare registration data
    registration_data = {
        "email": email,
        "password": password
    }
    
    # Add optional fields if provided
    if display_name:
        registration_data["display_name"] = display_name
    if username:
        registration_data["username"] = username
    if phone_number:
        registration_data["phone_number"] = phone_number
    
    data = api_post("/v1/auth/player/register", json=registration_data)
    if not data or "access_token" not in data:
        return render_template("register.html", error="Registration failed", csrf=request.cookies.get("csrf")), 400
    resp = make_response(redirect(url_for("landing")))
    resp.set_cookie("player_jwt", data["access_token"], httponly=True, samesite="Lax")
    return resp


@app.get("/shop")
def shop():
    # Load products from API
    products_data = api_get("/v1/shop/products?featured=true&page_size=10")
    
    if products_data and "products" in products_data:
        bundles = []
        for product in products_data["products"]:
            bundles.append({
                "product_sku": product["sku"],
                "name": product["name"],
                "price": f"{product['price']:.2f}",
                "currency": product["currency"],
                "description": product.get("description", ""),
                "short_description": product.get("short_description", ""),
                "image_url": product.get("image_url"),
                "is_available": product.get("is_available", True),
                "is_featured": product.get("is_featured", False),
                "tags": product.get("tags", [])
            })
    else:
        # Fallback to placeholder data if API is unavailable
        bundles = [
            {"product_sku": "BUNDLE-STARTER", "name": "Starter Bundle", "price": "49.00", "currency": "USD", "description": "Perfect for new players", "is_available": True},
            {"product_sku": "BUNDLE-RADIANT", "name": "Radiant Bundle", "price": "39.00", "currency": "USD", "description": "Radiant-themed cards", "is_available": True},
        ]
    
    resp = make_response(render_template("shop.html", bundles=bundles, csrf=request.cookies.get("csrf")))
    _csrf_get_or_set(resp)
    return resp


@app.get("/checkout/process")
def checkout_process():
    session_id = request.args.get("session_id")
    if not session_id:
        return redirect(url_for("shop"))
    
    # For now, simulate successful checkout
    # In production, this would show a payment form and process payment
    return render_template("checkout_process.html", session_id=session_id)

@app.post("/checkout/complete")
def checkout_complete():
    if not _csrf_valid(request.form.get("csrf")):
        return redirect(url_for("shop"))
    
    session_id = request.form.get("session_id")
    payment_method = request.form.get("payment_method", "stripe")
    
    # Simulate payment processing
    payload = {
        "session_id": session_id,
        "payment_method": payment_method,
        "payment_token": "demo_stripe_payment_token_12345",
        "items": [{"product_sku": "BUNDLE-STARTER", "quantity": 1}],  # TODO: Get from session
        "customer": {
            "name": "Demo Customer",
            "email": "demo@example.com"
        },
        "billing_address": {
            "street": "123 Demo St",
            "city": "Demo City",
            "state": "CA",
            "zip": "12345",
            "country": "US"
        },
        "shipping_address": {
            "street": "123 Demo St",
            "city": "Demo City", 
            "state": "CA",
            "zip": "12345",
            "country": "US"
        }
    }
    
    result = api_post("/v1/shop/checkout/process", json=payload, headers=_auth_headers())
    
    if result and result.get("success"):
        return redirect(result.get("redirect_url", "/checkout/success"))
    else:
        return redirect(url_for("checkout_cancel"))

@app.get("/checkout/success")
def checkout_success():
    order_number = request.args.get("order")
    order_data = None
    
    if order_number:
        order_data = api_get(f"/v1/shop/orders/{order_number}", headers=_auth_headers())
    
    return render_template("checkout_success.html", order=order_data)


@app.get("/checkout/cancel")
def checkout_cancel():
    return render_template("checkout_cancel.html")


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
    data = api_post("/v1/shop/checkout/create-session", json=payload, headers=_auth_headers())
    if not data or "url" not in data:
        return redirect(url_for("shop"))
    return redirect(data["url"])


@app.get("/admin")
def admin_index():
    return render_template("admin/index.html")


@app.get("/me")
@require_auth
def me_home():
    # Get comprehensive dashboard data
    dashboard_data = api_get("/v1/me", headers=_auth_headers())
    
    if dashboard_data:
        return render_template("me/dashboard.html", 
                             profile=dashboard_data.get('profile', {}),
                             stats=dashboard_data.get('stats', {}),
                             recent_activity=dashboard_data.get('recent_activity', {}))
    else:
        # Fallback to basic data
        profile = {"display_name": "Player", "elo_rating": 1000}
        stats = {"total_cards": 0, "win_rate": 0, "active_trades": 0}
        recent_activity = {"matches": [], "orders": []}
        return render_template("me/dashboard.html", 
                             profile=profile, stats=stats, recent_activity=recent_activity)


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
    # Get query parameters
    q = request.args.get("q", "")
    page = request.args.get("page", "1")
    sort_by = request.args.get("sort_by", "activated_at")
    
    # Build API parameters
    params = {"page": page, "sort_by": sort_by}
    if q:
        params["search"] = q
    
    # Get user's cards from new API
    cards_data = api_get("/v1/me/cards", params=params, headers=_auth_headers())
    
    if cards_data:
        return render_template("me/cards.html", 
                             cards=cards_data.get("cards", []),
                             total=cards_data.get("total", 0),
                             page=int(page),
                             total_pages=cards_data.get("total_pages", 1),
                             q=q, sort_by=sort_by)
    else:
        return render_template("me/cards.html", cards=[], total=0, page=1, total_pages=1, q=q, sort_by=sort_by)

@app.get("/me/analytics")
@require_auth
def me_analytics():
    analytics_data = api_get("/v1/me/analytics", headers=_auth_headers())
    
    if analytics_data:
        return render_template("me/analytics.html", analytics=analytics_data)
    else:
        # Fallback data
        fallback_data = {
            "match_statistics": {"total_matches": 0, "wins": 0, "losses": 0, "draws": 0, "win_rate": 0},
            "elo_history": [],
            "card_statistics": [],
            "recent_activity": []
        }
        return render_template("me/analytics.html", analytics=fallback_data)

@app.get("/me/orders")
@require_auth
def me_orders():
    page = request.args.get("page", "1")
    params = {"page": page}
    
    orders_data = api_get("/v1/me/orders", params=params, headers=_auth_headers())
    
    if orders_data:
        return render_template("me/orders.html",
                             orders=orders_data.get("orders", []),
                             total=orders_data.get("total", 0),
                             page=int(page),
                             total_pages=orders_data.get("total_pages", 1))
    else:
        return render_template("me/orders.html", orders=[], total=0, page=1, total_pages=1)

@app.get("/me/settings")
@require_auth
def me_settings():
    profile = api_get("/v1/me", headers=_auth_headers())
    return render_template("me/settings.html", profile=profile.get('profile', {}) if profile else {})

@app.post("/me/settings")
@require_auth
def me_settings_update():
    if not _csrf_valid(request.form.get("csrf")):
        return redirect(url_for("me_settings"))
    
    # Get form data
    update_data = {}
    if request.form.get("display_name"):
        update_data["display_name"] = request.form.get("display_name").strip()
    if request.form.get("username"):
        update_data["username"] = request.form.get("username").strip()
    if request.form.get("avatar_url"):
        update_data["avatar_url"] = request.form.get("avatar_url").strip()
    
    # Update profile via API
    result = api_patch("/v1/me", json=update_data, headers=_auth_headers())
    
    if result and result.get("success"):
        return redirect(url_for("me_settings"))
    else:
        # Handle error
        profile = api_get("/v1/me", headers=_auth_headers())
        error = result.get("error", "Update failed") if result else "Update failed"
        return render_template("me/settings.html", 
                             profile=profile.get('profile', {}) if profile else {},
                             error=error)

@app.get("/me/cards/activate")
@require_auth
def me_cards_activate():
    return render_template("me/activate_card.html")

@app.post("/me/cards/activate")
@require_auth
def me_cards_activate_post():
    if not _csrf_valid(request.form.get("csrf")):
        return render_template("me/activate_card.html", error="Invalid session")
    
    nfc_uid = request.form.get("nfc_uid", "").strip()
    activation_code = request.form.get("activation_code", "").strip()
    
    if not nfc_uid or not activation_code:
        return render_template("me/activate_card.html", error="NFC UID and activation code required")
    
    # Call activation API
    result = api_post("/v1/nfc-cards/activate", 
                     json={"nfc_uid": nfc_uid, "activation_code": activation_code},
                     headers=_auth_headers())
    
    if result and result.get("success"):
        return render_template("me/activate_card.html", 
                             success=True,
                             card_name=result.get("card_name"),
                             public_url=result.get("public_url"))
    else:
        error = result.get("error", "Activation failed") if result else "Activation failed"
        return render_template("me/activate_card.html", error=error)

@app.get("/cards/public/<public_slug>")
def public_card_page(public_slug: str):
    """Display public NFC card page"""
    card_data = api_get(f"/v1/nfc-cards/public/{public_slug}")
    
    if card_data:
        return render_template("public_card.html", card_data=card_data)
    else:
        return render_template("public_card.html", error="Card not found"), 404



# WSGI entrypoint
if __name__ == "__main__":
    app.run()
