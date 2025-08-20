## Deckport.ai API Reference (v1) - Updated Structure

This document describes the REST API endpoints for the restructured Deckport.ai platform. All endpoints are organized by feature area and use the new modular service architecture.

### Current Status: Phase 1 Complete ✅ + Console Auth Ready 🔐
- ✅ Health endpoints
- ✅ User authentication (registration/login)
- ✅ Card catalog with database integration
- ✅ **Device authentication** (console hardware)
- ✅ **Console QR login** (player authentication via phone)
- 🔄 Phase 2: Real-time endpoints (planned)
- 📋 Phase 3: NFC endpoints (planned)
- 📋 Phase 4: Video/OTA endpoints (planned)

### Conventions
- **Base URL**: `http://127.0.0.1:8002` (development) / `https://api.deckport.ai` (production)
- **Auth**: Bearer JWT for protected endpoints
- **Content-Type**: `application/json`
- **Structure**: Blueprint-based routes in `services/api/routes/`

### Authentication
- **User JWT**: Issued after login/registration for web users
- **Device JWT**: ✅ **Implemented** - For console hardware authentication
- **Player JWT**: ✅ **Implemented** - For console player sessions via QR login
- **Token Format**: `Authorization: Bearer <token>`

### Authentication Flow
1. **Console Boot**: Device authenticates with RSA keypair → Device JWT
2. **Player Login**: QR code scan → Phone confirmation → Player JWT
3. **API Access**: JWTs used for all authenticated endpoints

---

## Health

### GET `/health`
- **Auth**: none
- **Description**: Health check with database connectivity test
- **Response**: 
  ```json
  {
    "status": "ok",
    "database": "connected",
    "service": "api"
  }
  ```
- **Implementation**: `services/api/routes/health.py`
- **Status**: ✅ Working

---

## Authentication

### POST `/v1/auth/player/register`
- **Auth**: none
- **Description**: Register a new player account
- **Request**:
  ```json
  {
    "email": "user@example.com",
    "password": "password123",
    "display_name": "Player Name" // optional
  }
  ```
- **Response**:
  ```json
  {
    "access_token": "jwt_token_here",
    "user": {
      "id": 1,
      "email": "user@example.com", 
      "display_name": "Player Name"
    }
  }
  ```
- **Validation**: Email format, password strength (8+ chars, letters + numbers)
- **Implementation**: `services/api/routes/auth.py`
- **Status**: ✅ Working

### POST `/v1/auth/player/login`
- **Auth**: none
- **Description**: Login with email and password
- **Request**:
  ```json
  {
    "email": "user@example.com",
    "password": "password123"
  }
  ```
- **Response**:
  ```json
  {
    "access_token": "jwt_token_here",
    "user": {
      "id": 1,
      "email": "user@example.com",
      "display_name": "Player Name",
      "elo_rating": 1000
    }
  }
  ```
- **Implementation**: `services/api/routes/auth.py`
- **Status**: ✅ Working

---

## Device Authentication (Console Hardware)

### POST `/v1/auth/device/register`
- **Auth**: none
- **Description**: Register a new console device (one-time setup)
- **Request**:
  ```json
  {
    "device_uid": "DECK_1642534567_1234",
    "public_key": "-----BEGIN PUBLIC KEY-----\nMIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEA...\n-----END PUBLIC KEY-----"
  }
  ```
- **Response**:
  ```json
  {
    "status": "pending",
    "message": "Device registration submitted for admin approval",
    "device_uid": "DECK_1642534567_1234"
  }
  ```
- **Implementation**: `services/api/routes/device_auth.py`
- **Status**: ✅ Working
- **Notes**: Requires admin approval via admin panel

### POST `/v1/auth/device/login`
- **Auth**: none (uses RSA signature)
- **Description**: Authenticate console device using signed nonce
- **Request**:
  ```json
  {
    "device_uid": "DECK_1642534567_1234",
    "nonce": "base64_encoded_nonce",
    "signature": "base64_encoded_signature"
  }
  ```
- **Response**:
  ```json
  {
    "access_token": "device_jwt_token_here",
    "token_type": "bearer",
    "expires_in": 86400,
    "device_id": 123
  }
  ```
- **Implementation**: `services/api/routes/device_auth.py`
- **Status**: ✅ Working
- **Security**: RSA 2048-bit signature verification

### GET `/v1/auth/device/status`
- **Auth**: Device JWT or query parameter
- **Description**: Check device registration status
- **Query**: `?device_uid=DECK_1642534567_1234`
- **Response**:
  ```json
  {
    "device_uid": "DECK_1642534567_1234",
    "status": "active",
    "registered_at": "2025-01-18T06:12:34.567890Z",
    "owner_player_id": null
  }
  ```
- **Implementation**: `services/api/routes/device_auth.py`
- **Status**: ✅ Working

---

## Console QR Login (Player Authentication)

### POST `/v1/console-login/start`
- **Auth**: Device JWT
- **Description**: Start QR code login flow for player authentication
- **Request**: `{}`
- **Response**:
  ```json
  {
    "login_token": "random_secure_token",
    "qr_url": "https://deckport.ai/console-link?token=random_secure_token",
    "expires_at": "2025-01-18T06:17:34.567890Z",
    "expires_in": 300
  }
  ```
- **Implementation**: `services/api/routes/console_login.py`
- **Status**: ✅ Working

### POST `/v1/console-login/confirm`
- **Auth**: Player JWT (from phone)
- **Description**: Confirm console login from player's phone
- **Request**:
  ```json
  {
    "login_token": "random_secure_token"
  }
  ```
- **Response**:
  ```json
  {
    "status": "confirmed",
    "message": "Console login confirmed successfully"
  }
  ```
- **Implementation**: `services/api/routes/console_login.py`
- **Status**: ✅ Working

### GET `/v1/console-login/poll`
- **Auth**: Device JWT
- **Description**: Poll for console login confirmation status
- **Query**: `?login_token=random_secure_token`
- **Response** (pending):
  ```json
  {
    "status": "pending"
  }
  ```
- **Response** (confirmed):
  ```json
  {
    "status": "confirmed",
    "player_jwt": "player_jwt_for_console",
    "player": {
      "id": 123,
      "email": "player@example.com",
      "display_name": "Player Name",
      "elo_rating": 1000
    }
  }
  ```
- **Implementation**: `services/api/routes/console_login.py`
- **Status**: ✅ Working

### POST `/v1/console-login/cancel`
- **Auth**: Device JWT
- **Description**: Cancel a pending console login
- **Request**:
  ```json
  {
    "login_token": "random_secure_token"
  }
  ```
- **Response**:
  ```json
  {
    "status": "cancelled"
  }
  ```
- **Implementation**: `services/api/routes/console_login.py`
- **Status**: ✅ Working

---

## Console QR Login (phone-assisted)

- POST `/v1/console-login/start`
  - Auth: Device JWT
  - Resp: `{ login_token, qr_url, expires_at }`

- POST `/v1/console-login/confirm`
  - Auth: Player JWT (phone)
  - Req: `{ login_token }`
  - Resp: `{ status: "confirmed" }`

- GET `/v1/console-login/poll?login_token=...`
  - Auth: Device JWT
  - Resp: `{ status: "pending" | "confirmed", player_jwt? }`

---

## NFC and Cards

### NFC Verification
- POST `/v1/nfc/verify`
  - Auth: Player or Device JWT (context-dependent)
  - Req: `{ uid, product_sku, url_params }`
  - Resp: `{ nfc_card_id, valid }`

## Card Catalog

### GET `/v1/catalog/cards`
- **Auth**: none (public)
- **Description**: Get card catalog with filtering and pagination
- **Query Parameters**:
  - `q` - Search by card name (optional)
  - `category` - Filter by category: CREATURE, ENCHANTMENT, etc. (optional)
  - `rarity` - Filter by rarity: COMMON, RARE, EPIC, LEGENDARY (optional)
  - `page` - Page number (default: 1)
  - `page_size` - Items per page (default: 20, max: 100)
- **Response**:
  ```json
  {
    "items": [
      {
        "product_sku": "RADIANT-001",
        "name": "Solar Vanguard",
        "rarity": "EPIC",
        "category": "CREATURE",
        "subtype": null,
        "base_stats": {
          "attack": 3,
          "defense": 2,
          "health": 5,
          "mana_cost": {"RADIANT": 3},
          "energy_cost": 0
        },
        "display_label": null
      }
    ],
    "total": 5,
    "page": 1,
    "page_size": 20,
    "has_more": false
  }
  ```
- **Implementation**: `services/api/routes/cards.py`
- **Status**: ✅ Working with database

### GET `/v1/catalog/cards/{product_sku}`
- **Auth**: none (public)
- **Description**: Get detailed card information
- **Parameters**: `product_sku` - Card identifier (e.g., "RADIANT-001")
- **Response**:
  ```json
  {
    "product_sku": "RADIANT-001",
    "name": "Solar Vanguard",
    "rarity": "EPIC",
    "category": "CREATURE",
    "subtype": null,
    "base_stats": {
      "attack": 3,
      "defense": 2,
      "health": 5,
      "mana_cost": {"RADIANT": 3},
      "energy_cost": 0
    },
    "attachment_rules": null,
    "duration": null,
    "token_spec": null,
    "reveal_trigger": null,
    "display_label": null,
    "created_at": "2025-01-18T06:12:34.567890"
  }
  ```
- **Implementation**: `services/api/routes/cards.py`
- **Status**: ✅ Working with database

### Activation
- POST `/v1/cards/activate`
  - Auth: Player JWT
  - Req: `{ uid, activation_code }`
  - Resp: `{ nfc_card_id, activated: true }`

### Trading
- POST `/v1/cards/transfer/start`
  - Auth: Player JWT (seller)
  - Req: `{ nfc_card_id }`
  - Resp: `{ transfer_code, transfer_id, expires_at }`

- POST `/v1/cards/transfer/claim`
  - Auth: Player JWT (buyer)
  - Req: `{ uid, transfer_code }`
  - Resp: `{ nfc_card_id, owner_player_id }`

- POST `/v1/cards/transfer/cancel`
  - Auth: Player JWT (seller)
  - Req: `{ transfer_id }`
  - Resp: `{ status: "cancelled" }`

---

## Matchmaking

- POST `/v1/matchmaking/enqueue`
  - Auth: Device or Player JWT (choose policy; device JWT is typical for consoles)
  - Req: `{ mode }`
  - Resp: `{ enqueued: true }`

- POST `/v1/matchmaking/cancel`
  - Auth: same as enqueue
  - Req: `{}`
  - Resp: `{ cancelled: true }`

---

## Matches

- GET `/v1/matches/{match_id}`
  - Auth: Device or Player JWT (must participate or be admin)
  - Resp: `{ id, status, participants, created_at, started_at, ended_at }`

Optional (admin or system):
- POST `/v1/matches/{match_id}/end`
  - Auth: Admin JWT or internal
  - Req: `{ results }`
  - Resp: `{ status: "finished" }`

---

## Game (profiles, inventory, rules, leaderboards)

### Player profile
- GET `/v1/me`
  - Auth: Player JWT
  - Resp: `{ id, email, display_name, elo_rating, created_at }`

- PATCH `/v1/me`
  - Auth: Player JWT
  - Req: `{ display_name? }`
  - Resp: `{ id, display_name }`

### Inventory
- GET `/v1/me/inventory`
  - Auth: Player JWT
  - Resp: `{ cards: [{ nfc_card_id, product_sku, level, xp, custom_state }] }`
  - Query (optional): `?q=&color=&rarity=&category=&page=&page_size=`

### User stats (performance)
- GET `/v1/me/matches`
  - Auth: Player JWT
  - Query: `?limit=20&before_id=`
  - Resp: `{ items: [{ id, created_at, result, opponent, mmr_delta }] }`

- GET `/v1/me/stats`
  - Auth: Player JWT
  - Resp: `{
      elo_history: [{ match_id, created_at, elo }],
      win_loss_draw: { win, loss, draw },
      recent_streak: { type: "win"|"loss"|"draw", length },
      avg_turn_time_ms: number,
      play_window_expired_rate: number,
      actions_per_turn: number,
      reaction_rate: number,
      color_usage: [{ color, count }]
    }`


### Game modes and rules
- GET `/v1/game/modes`
  - Auth: public
  - Resp: `{ modes: [{ id: "1v1", name, min_players, max_players }] }`

- GET `/v1/game/rules`
  - Auth: public
  - Resp: `{ version, rules: { ... } }`

### Pre-/Post-match hooks
- POST `/v1/matches/{match_id}/ready`
  - Auth: Player or Device JWT (participant)
  - Req: `{ }`
  - Resp: `{ ready: true }`

- POST `/v1/matches/{match_id}/result`
  - Auth: Player or Device JWT (participant) or system
  - Req: `{ outcome: "win"|"loss"|"draw", stats?: { ... } }`
  - Resp: `{ saved: true, new_rating?: number }`

### Leaderboards
- GET `/v1/leaderboards`
  - Auth: public
  - Query: `?mode=1v1&period=season|week|all`
  - Resp: `{ entries: [{ rank, player_id, display_name, rating }] }`

### Seasons (optional)
- GET `/v1/seasons/current`
  - Auth: public
  - Resp: `{ id, name, start_at, end_at }`

### Replays (optional)
- GET `/v1/matches/{match_id}/replay`
  - Auth: Player JWT (participant) or admin
  - Resp: `{ url }`

### Moderation (optional)
- POST `/v1/report`
  - Auth: Player JWT
  - Req: `{ type: "player"|"match", target_id, reason }`
  - Resp: `{ received: true }`

---

## Gameplay (timers, snapshots, concessions, arsenal)

### Timers and phases (defaults)
- Play window: 10 seconds (configurable)
- Turn clock: 60 seconds (configurable)
- Phases: `start`, `main`, `attack`, `end`
- Reaction policy: one reaction per window; defender has priority in the attack window; no complex stack

### REST endpoints
- GET `/v1/matches/{match_id}/snapshot`
  - Auth: Player or Device JWT (participant)
  - Resp: `{ match_id, seq, full_state }`

- POST `/v1/matches/{match_id}/concede`
  - Auth: Player or Device JWT (participant)
  - Req: `{ reason?: string }`
  - Resp: `{ conceded: true }`

- POST `/v1/matches/{match_id}/resync`
  - Auth: Player or Device JWT (participant)
  - Req: `{ since_seq?: number }`
  - Resp: `{ enqueued: true }` (server will push `sync.snapshot`/deltas over WS)

### Arsenal (no deck builder)
- Players may bring/scan any number of owned physical cards before a match. The scanned set is the Arsenal for the match.
- Managed over realtime (see WS events below); server validates ownership and availability.

---

## Video / RTC

Note: LiveKit tokens are minted by the API during matchmaking; typically not a public endpoint. If you expose one for testing:

- POST `/v1/rtc/token`
  - Auth: Player or Device JWT (restricted)
  - Req: `{ room, identity, ttl_seconds? }`
  - Resp: `{ access_token }`

---

## OTA Updates (Consoles)

- GET `/v1/updates/latest`
  - Auth: Device JWT
  - Query: `?platform=linux_x86_64`
  - Resp: `{ version, platform, artifact_url, sha256, signature, mandatory }`

Optional admin upload (artifact managed elsewhere or via admin UI):
- POST `/v1/admin/updates`
  - Auth: Admin JWT
  - Req: `{ version, platform, artifact_url, sha256, signature, mandatory }`
  - Resp: `{ id, created_at }`

---

## Admin

### Devices
- GET `/v1/admin/devices?status=pending`
  - Auth: Admin JWT
  - Resp: `{ devices: [...] }`

- POST `/v1/admin/devices/{device_id}/approve`
  - Auth: Admin JWT
  - Req: `{ approved: true }`
  - Resp: `{ status: "approved" }`

### Card catalog and provisioning
- POST `/v1/admin/card-batches`
  - Auth: Admin JWT
  - Req: `{ product_sku, name?, notes? }`
  - Resp: `{ id, created_at }`

- POST `/v1/admin/cards/provision`
  - Auth: Admin JWT
  - Req: `{ product_sku, batch_id?, uid_list? | uid?, generate_codes?: true }`
  - Resp: `{ created: [{ ntag_uid, activation_code? }], duplicates: [...] }`

- GET `/v1/admin/cards/search`
  - Auth: Admin JWT
  - Query: `?uid=...&batch_id=...&status=...`
  - Resp: `{ results: [...] }`

---

## Data model notes (relevant to API)

- `card_catalog` (product definitions: `product_sku`, `name`, `rarity`, `base_stats`)
- `nfc_cards` (produced units: `ntag_uid`, `product_sku`, `batch_id`, `status`, `activation_code_hash`)
- `player_cards` (ownership mapping)
- `card_transfer_offers` (trading)
- `console_login_tokens` (QR login flow if persisted in DB)
- `mm_queue` (Postgres queue for matchmaking, MVP)

Card catalog fields to support new categories (portal-themed display labels):
- `category` enum expanded:
  - CREATURE (display "Denizen"), STRUCTURE ("Bastion"),
  - ACTION_FAST ("Instant"), ACTION_SLOW ("Sorcery"),
  - SPECIAL ("Planar"), EQUIPMENT ("Relic"), ENCHANTMENT ("Sigil"),
  - ARTIFACT ("Artifact"), RITUAL ("Rite"), TRAP ("Ward"),
  - SUMMON ("Conjuration"), TERRAIN ("Realm"), OBJECTIVE ("Quest")
- `subtype` (e.g., AURA, BOON, CURSE, CHARM)
- `attachment_rules` (for Auras/Equipment: valid targets, stacking rules)
- `duration` (turns or condition for Terrain/Objective)
- `token_spec` (for Summon tokens: stats/effects)
- `reveal_trigger` (for Traps: condition to auto‑trigger)
- Optional `display_label` override per card if you want exceptions

---

## Realtime WebSocket (realtime.example.com/ws)

Auth: Bearer Device or Player JWT (as designed)

Client → Server events:
- `queue.join` → `{ mode: "1v1", preferred_range?: [min,max] }`
- `queue.leave` → `{}`
- `match.ready` → `{ match_id }`
- `state.update` → `{ match_id, delta }`
- `card.play` → `{ match_id, nfc_card_id, action, client_ts }`  (action examples: "summon", "attack", "defend", ...)
- `card.cancel` → `{ match_id, nfc_card_id, client_ts }`
- `sync.request` → `{ match_id, since_seq? }`
- `arsenal.add` → `{ match_id, nfc_card_id }`
- `arsenal.remove` → `{ match_id, nfc_card_id }`

Server → Client events:
- `queue.ack` → `{ mode }`
- `match.found` → `{ match_id, opponent, rtc: { livekit_url, access_token } }`
- `match.start` → `{ match_id, seed, rules }`
- `state.apply` → `{ match_id, patch }`
- `match.end` → `{ match_id, result }`
- `sync.snapshot` → `{ match_id, seq, full_state }`
- `timer.tick` → `{ match_id, server_ts, phase, remaining_ms }`
- `arsenal.updated` → `{ match_id, cards: [{ nfc_card_id }] }`

Errors:
- `{ type: "error", code, message }`

---

## Rate limiting and security

- Activation/transfer endpoints: strict per-card and per-account limits (e.g., 5/min with backoff)
- Console-login polling: cap to 0.5–1 Hz per token; short TTL (2–5 minutes)
- All codes/tokens are stored hashed (Argon2id); never log plaintext

