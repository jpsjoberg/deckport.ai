## Frontend Plan (Landing, Catalog, Auth, Shop, Admin)

Stack
- Flask (Jinja templates), HTMX/Alpine.js for interactivity
- TailwindCSS (CDN) for styling
- Stripe Checkout (redirect) for payments; Customer Portal link for billing

Routes
- `/` Landing: hero video/image, features, CTA buttons (Play, Buy)
- `/cards` Catalog listing with filters (server-rendered; HTMX partials)
  - Filters: text `q`, `color`, `rarity`, `category`, pagination
  - Data from API: `GET /v1/catalog/cards`
- `/cards/<product_sku>` Card detail (from `GET /v1/catalog/cards/{product_sku}`)
- `/login` (POST to API `/v1/auth/player/login`) → store JWT in httpOnly cookie via backend
- `/register` (POST to API `/v1/auth/player/register`)
- `/shop` Product list (bundles) from `GET /v1/shop/catalog` with Buy Now buttons
- `/checkout/success`, `/checkout/cancel` (Stripe return)

Admin (unified)
- `/admin` dashboard
- `/admin/players`, `/admin/consoles` (read-only initially)
- `/admin/cards/catalog`, `/admin/cards/batches` (read-only initially)
- `/admin/orders` (read-only initially)
- `/admin/updates` (read-only initially)

Security
- CSRF tokens on forms; httpOnly secure cookie for JWT
- Rate limit login/register; captcha if abused

UX notes
- Keep pages fast and simple; progressive enhancement via HTMX
- Accessible forms; clear errors from API responses

MVP Delivery
- Implement landing, catalog list/detail, login/register, shop list + Stripe Checkout redirect, and admin dashboard (read-only)

---

## Updates implemented in scaffold

- Routes added in `frontend/app.py`:
  - Public: `/`, `/cards`, `/cards/<product_sku>`, `/shop`, `/checkout/success`, `/checkout/cancel`
  - Auth: `/login`, `/register` (posts to API and sets httpOnly JWT cookie)
  - User area: `/me`, `/me/performance`, `/me/cards` (require auth; call API)
  - Admin: `/admin` (read-only placeholder)

- Templates created under `frontend/templates/` for all routes (HTMX-ready, Tailwind CDN):
  - `index.html`, `cards_list.html`, `card_detail.html`, `shop.html`, `checkout_success.html`, `checkout_cancel.html`
  - `login.html`, `register.html`
  - `me/index.html`, `me/performance.html`, `me/cards.html`
  - `admin/index.html`

- API integration helpers in `app.py`:
  - `API_BASE` env var to point to the API (default `http://localhost:8000`)
  - `api_get()` and `api_post()` wrappers using `requests`
  - JWT cookie via `player_jwt`; attached as `Authorization: Bearer <token>` on user routes
  - CSRF cookie `csrf` set server-side; forms include hidden `csrf` and are validated on POST

- Data sources wired:
  - Catalog list/detail → `GET /v1/catalog/cards`, `GET /v1/catalog/cards/{sku}` with mock fallback
  - Auth → `POST /v1/auth/player/login`, `POST /v1/auth/player/register`
  - User area → `GET /v1/me`, `GET /v1/me/matches`, `GET /v1/me/stats`, `GET /v1/me/inventory`

---

## Configuration

- Environment variable:
  - `API_BASE` (e.g., `http://localhost:8000` in dev; `https://api.example.com` in prod)

- Cookies:
  - `player_jwt` (httpOnly, SameSite=Lax) set on successful login/register
  - `csrf` (httpOnly) set on GET of login/register; must match hidden `csrf` field on POST

---

## Running locally

1) Ensure API is available (or accept mock fallback for catalog only).
2) Set API base (bash):
   - `export API_BASE=http://localhost:8000`
3) Run frontend app:
   - `python frontend/app.py`
4) Visit `http://127.0.0.1:5000/`

---

## Security notes (MVP)

- Use TLS in prod; set `Secure` on cookies behind HTTPS
- Rate limit login/register endpoints at the API; basic server-side validation in frontend
- Add CSRF tokens to any new POST forms

---

## Next steps

- Replace mock catalog fallback with strict API dependency once endpoints are live
- Implement Buy Now: POST to API `/v1/shop/checkout/session` and redirect to `session.url`
  - Implemented: `/shop/checkout` posts to API and redirects to Stripe Checkout `url`
- Add logout route (clear `player_jwt`)
- Add minimal admin lists wired to API
- Add pagination/filters for `/me/cards` using `/v1/me/inventory` query params

