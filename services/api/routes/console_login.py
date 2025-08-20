"""
Console QR login routes - allows players to login via phone
"""

from flask import Blueprint, request, jsonify, g, send_file
from datetime import datetime, timedelta, timezone
import secrets
import hashlib
import qrcode
from io import BytesIO
from shared.auth.jwt_handler import create_access_token, verify_token
from shared.database.connection import SessionLocal
from shared.models.base import Console, ConsoleLoginToken, LoginTokenStatus, Player

console_login_bp = Blueprint('console_login', __name__, url_prefix='/v1/console-login')

@console_login_bp.route('/start', methods=['POST'])
def start_console_login():
    """Start QR code login flow - generates login token and QR URL"""
    # TODO: Add device authentication middleware
    # For now, get device info from request or token
    
    # This should come from device JWT token in production
    device_uid = request.headers.get('X-Device-UID')  # Temporary for testing
    
    if not device_uid:
        return jsonify({"error": "Device authentication required"}), 401
    
    try:
        with SessionLocal() as session:
            # Find the console
            console = session.query(Console).filter(Console.device_uid == device_uid).first()
            if not console:
                return jsonify({"error": "Console not found"}), 404
            
            # Generate login token
            login_token = secrets.token_urlsafe(32)
            token_hash = hashlib.sha256(login_token.encode()).hexdigest()
            
            # Set expiration (5 minutes)
            expires_at = datetime.now(timezone.utc) + timedelta(minutes=5)
            
            # Clean up any existing tokens for this console
            session.query(ConsoleLoginToken).filter(
                ConsoleLoginToken.console_id == console.id,
                ConsoleLoginToken.status == LoginTokenStatus.pending
            ).update({"status": LoginTokenStatus.cancelled})
            
            # Create new login token
            new_token = ConsoleLoginToken(
                console_id=console.id,
                token_hash=token_hash,
                status=LoginTokenStatus.pending,
                expires_at=expires_at
            )
            
            session.add(new_token)
            session.commit()
            
            # Generate QR URL (points to public API service)
            import os
            
            # Get base URLs from environment
            public_base_url = os.getenv("PUBLIC_API_URL", "https://api.deckport.ai")
            console_base_url = os.getenv("CONSOLE_API_URL", "http://127.0.0.1:8002")
            
            # For development, you can set:
            # export PUBLIC_API_URL="https://your-ngrok-url.ngrok.io"
            # export CONSOLE_API_URL="http://127.0.0.1:8002"
            
            # QR URL uses public URL (for phones to access)
            qr_url = f"{public_base_url}/v1/console-login/link?token={login_token}"
            
            # QR Image URL - use console URL (might be same as public in production)
            qr_image_url = f"{console_base_url}/v1/console-login/qr/{login_token}"
            
            return jsonify({
                "login_token": login_token,
                "qr_url": qr_url,
                "qr_image_url": qr_image_url,
                "expires_at": expires_at.isoformat(),
                "expires_in": 300  # 5 minutes in seconds
            })
            
    except Exception as e:
        return jsonify({"error": "Failed to start login flow"}), 500

@console_login_bp.route('/confirm', methods=['POST'])
def confirm_console_login():
    """Confirm console login from player's phone"""
    data = request.get_json()
    
    if not data:
        return jsonify({"error": "No data provided"}), 400
    
    login_token = data.get('login_token', '').strip()
    
    if not login_token:
        return jsonify({"error": "login_token required"}), 400
    
    # Get player info from JWT token (player must be authenticated)
    auth_header = request.headers.get('Authorization', '')
    if not auth_header.startswith('Bearer '):
        return jsonify({"error": "Player authentication required"}), 401
    
    player_token = auth_header.split(' ')[1]
    token_payload = verify_token(player_token)
    
    if not token_payload or token_payload.get('type') != 'access':
        return jsonify({"error": "Invalid player token"}), 401
    
    player_id = token_payload.get('user_id')
    
    try:
        with SessionLocal() as session:
            # Hash the token to find it
            token_hash = hashlib.sha256(login_token.encode()).hexdigest()
            
            # Find the login token
            login_token_record = session.query(ConsoleLoginToken).filter(
                ConsoleLoginToken.token_hash == token_hash,
                ConsoleLoginToken.status == LoginTokenStatus.pending
            ).first()
            
            if not login_token_record:
                return jsonify({"error": "Invalid or expired login token"}), 404
            
            # Check expiration
            if datetime.now(timezone.utc) > login_token_record.expires_at:
                login_token_record.status = LoginTokenStatus.expired
                session.commit()
                return jsonify({"error": "Login token expired"}), 410
            
            # Confirm the login
            login_token_record.status = LoginTokenStatus.confirmed
            login_token_record.confirmed_player_id = player_id
            session.commit()
            
            return jsonify({
                "status": "confirmed",
                "message": "Console login confirmed successfully"
            })
            
    except Exception as e:
        return jsonify({"error": "Failed to confirm login"}), 500

@console_login_bp.route('/poll', methods=['GET'])
def poll_console_login():
    """Poll for console login confirmation status"""
    login_token = request.args.get('login_token', '').strip()
    
    if not login_token:
        return jsonify({"error": "login_token required"}), 400
    
    try:
        with SessionLocal() as session:
            # Hash the token to find it
            token_hash = hashlib.sha256(login_token.encode()).hexdigest()
            
            # Find the login token
            login_token_record = session.query(ConsoleLoginToken).filter(
                ConsoleLoginToken.token_hash == token_hash
            ).first()
            
            if not login_token_record:
                return jsonify({"error": "Invalid login token"}), 404
            
            # Check expiration
            if datetime.now(timezone.utc) > login_token_record.expires_at:
                if login_token_record.status == LoginTokenStatus.pending:
                    login_token_record.status = LoginTokenStatus.expired
                    session.commit()
                return jsonify({"status": "expired"}), 410
            
            # Return status
            response_data = {"status": login_token_record.status.value}
            
            # If confirmed, include player JWT
            if login_token_record.status == LoginTokenStatus.confirmed and login_token_record.confirmed_player_id:
                # Get player info
                player = session.query(Player).filter(Player.id == login_token_record.confirmed_player_id).first()
                if player:
                    # Create player JWT for console use
                    player_jwt = create_access_token(player.id, player.email, {"console_login": True})
                    response_data["player_jwt"] = player_jwt
                    response_data["player"] = {
                        "id": player.id,
                        "email": player.email,
                        "display_name": player.display_name,
                        "elo_rating": player.elo_rating
                    }
                
                # Mark token as used
                login_token_record.status = LoginTokenStatus.expired
                session.commit()
            
            return jsonify(response_data)
            
    except Exception as e:
        return jsonify({"error": "Failed to check login status"}), 500

@console_login_bp.route('/cancel', methods=['POST'])
def cancel_console_login():
    """Cancel a pending console login"""
    data = request.get_json()
    
    if not data:
        return jsonify({"error": "No data provided"}), 400
    
    login_token = data.get('login_token', '').strip()
    
    if not login_token:
        return jsonify({"error": "login_token required"}), 400
    
    try:
        with SessionLocal() as session:
            # Hash the token to find it
            token_hash = hashlib.sha256(login_token.encode()).hexdigest()
            
            # Find and cancel the login token
            login_token_record = session.query(ConsoleLoginToken).filter(
                ConsoleLoginToken.token_hash == token_hash,
                ConsoleLoginToken.status == LoginTokenStatus.pending
            ).first()
            
            if login_token_record:
                login_token_record.status = LoginTokenStatus.cancelled
                session.commit()
                return jsonify({"status": "cancelled"})
            else:
                return jsonify({"error": "Login token not found or already processed"}), 404
                
    except Exception as e:
        return jsonify({"error": "Failed to cancel login"}), 500

@console_login_bp.route('/link', methods=['GET'])
def console_link_page():
    """Serve the console login confirmation page"""
    login_token = request.args.get('token', '').strip()
    
    if not login_token:
        return """
        <!DOCTYPE html>
        <html><head><title>Console Login - Error</title></head>
        <body style="font-family: Arial; text-align: center; padding: 50px;">
            <h1>❌ Invalid Request</h1>
            <p>No login token provided.</p>
        </body></html>
        """, 400
    
    # Verify token exists and is valid
    try:
        with SessionLocal() as session:
            token_hash = hashlib.sha256(login_token.encode()).hexdigest()
            login_token_record = session.query(ConsoleLoginToken).filter(
                ConsoleLoginToken.token_hash == token_hash,
                ConsoleLoginToken.status == LoginTokenStatus.pending
            ).first()
            
            if not login_token_record:
                return """
                <!DOCTYPE html>
                <html><head><title>Console Login - Error</title></head>
                <body style="font-family: Arial; text-align: center; padding: 50px;">
                    <h1>❌ Invalid Token</h1>
                    <p>Login token not found or expired.</p>
                </body></html>
                """, 404
            
            # Check expiration
            if datetime.now(timezone.utc) > login_token_record.expires_at:
                return """
                <!DOCTYPE html>
                <html><head><title>Console Login - Expired</title></head>
                <body style="font-family: Arial; text-align: center; padding: 50px;">
                    <h1>⏰ Token Expired</h1>
                    <p>This login request has expired. Please try again from the console.</p>
                </body></html>
                """, 410
    
    except Exception as e:
        return """
        <!DOCTYPE html>
        <html><head><title>Console Login - Error</title></head>
        <body style="font-family: Arial; text-align: center; padding: 50px;">
            <h1>❌ Server Error</h1>
            <p>Unable to verify login token.</p>
        </body></html>
        """, 500
    
    # Return the login page
    return f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Console Login - Deckport</title>
        <style>
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                margin: 0;
                padding: 20px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                display: flex;
                align-items: center;
                justify-content: center;
            }}
            .login-container {{
                background: white;
                border-radius: 20px;
                padding: 40px;
                box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
                max-width: 400px;
                width: 100%;
                text-align: center;
            }}
            .logo {{
                font-size: 2.5em;
                font-weight: bold;
                margin-bottom: 10px;
                color: #333;
            }}
            .subtitle {{
                color: #666;
                margin-bottom: 30px;
                font-size: 1.1em;
            }}
            .console-info {{
                background: #f8f9fa;
                border-radius: 12px;
                padding: 20px;
                margin-bottom: 30px;
                border-left: 4px solid #667eea;
            }}
            .form-group {{
                margin-bottom: 20px;
                text-align: left;
            }}
            .form-group label {{
                display: block;
                margin-bottom: 8px;
                color: #333;
                font-weight: 500;
            }}
            .form-group input {{
                width: 100%;
                padding: 12px;
                border: 2px solid #e1e5e9;
                border-radius: 8px;
                font-size: 16px;
                box-sizing: border-box;
                transition: border-color 0.3s;
            }}
            .form-group input:focus {{
                outline: none;
                border-color: #667eea;
            }}
            .login-btn {{
                width: 100%;
                padding: 15px;
                background: #667eea;
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 16px;
                font-weight: 600;
                cursor: pointer;
                transition: background 0.3s;
                margin-bottom: 15px;
            }}
            .login-btn:hover {{
                background: #5a67d8;
            }}
            .login-btn:disabled {{
                background: #cbd5e0;
                cursor: not-allowed;
            }}
            .cancel-btn {{
                width: 100%;
                padding: 15px;
                background: transparent;
                color: #666;
                border: 2px solid #e1e5e9;
                border-radius: 8px;
                font-size: 16px;
                cursor: pointer;
                transition: all 0.3s;
            }}
            .cancel-btn:hover {{
                border-color: #f56565;
                color: #f56565;
            }}
            .status {{
                margin-top: 20px;
                padding: 15px;
                border-radius: 8px;
                display: none;
            }}
            .status.success {{
                background: #f0fff4;
                color: #38a169;
                border: 1px solid #9ae6b4;
            }}
            .status.error {{
                background: #fef5e7;
                color: #d69e2e;
                border: 1px solid #f6e05e;
            }}
            .loading {{
                display: inline-block;
                width: 20px;
                height: 20px;
                border: 3px solid #f3f3f3;
                border-top: 3px solid #667eea;
                border-radius: 50%;
                animation: spin 1s linear infinite;
            }}
            @keyframes spin {{
                0% {{ transform: rotate(0deg); }}
                100% {{ transform: rotate(360deg); }}
            }}
        </style>
    </head>
    <body>
        <div class="login-container">
            <div class="logo">🎮 DECKPORT</div>
            <div class="subtitle">Console Login</div>
            
            <div class="console-info">
                <strong>🖥️ Console Access Request</strong><br>
                A Deckport console is requesting access to your account.
                Please login to authorize this device.
            </div>
            
            <form id="loginForm">
                <div class="form-group">
                    <label for="email">Email</label>
                    <input type="email" id="email" name="email" required>
                </div>
                
                <div class="form-group">
                    <label for="password">Password</label>
                    <input type="password" id="password" name="password" required>
                </div>
                
                <button type="submit" class="login-btn" id="loginBtn">
                    Login & Authorize Console
                </button>
                
                <button type="button" class="cancel-btn" onclick="cancelLogin()">
                    Cancel
                </button>
            </form>
            
            <div id="status" class="status"></div>
        </div>
        
        <script>
            const token = '{login_token}';
            
            document.getElementById('loginForm').addEventListener('submit', async (e) => {{
                e.preventDefault();
                
                const email = document.getElementById('email').value;
                const password = document.getElementById('password').value;
                const loginBtn = document.getElementById('loginBtn');
                const status = document.getElementById('status');
                
                // Show loading state
                loginBtn.disabled = true;
                loginBtn.innerHTML = '<span class="loading"></span> Logging in...';
                status.style.display = 'none';
                
                try {{
                    // First, login the user
                    const loginResponse = await fetch('/v1/auth/player/login', {{
                        method: 'POST',
                        headers: {{
                            'Content-Type': 'application/json',
                        }},
                        body: JSON.stringify({{ email, password }})
                    }});
                    
                    if (!loginResponse.ok) {{
                        throw new Error('Invalid email or password');
                    }}
                    
                    const loginData = await loginResponse.json();
                    const playerToken = loginData.access_token;
                    
                    // Then confirm console login
                    const confirmResponse = await fetch('/v1/console-login/confirm', {{
                        method: 'POST',
                        headers: {{
                            'Content-Type': 'application/json',
                            'Authorization': `Bearer ${{playerToken}}`
                        }},
                        body: JSON.stringify({{ login_token: token }})
                    }});
                    
                    const confirmData = await confirmResponse.json();
                    
                    if (confirmData.status === 'confirmed') {{
                        status.className = 'status success';
                        status.innerHTML = '✅ Console login authorized! You can return to the console now.';
                        status.style.display = 'block';
                        loginBtn.innerHTML = 'Success!';
                    }} else {{
                        throw new Error(confirmData.error || 'Failed to authorize console');
                    }}
                }} catch (error) {{
                    status.className = 'status error';
                    status.innerHTML = '❌ ' + error.message;
                    status.style.display = 'block';
                    loginBtn.disabled = false;
                    loginBtn.innerHTML = 'Login & Authorize Console';
                }}
            }});
            
            async function cancelLogin() {{
                try {{
                    await fetch('/v1/console-login/cancel', {{
                        method: 'POST',
                        headers: {{
                            'Content-Type': 'application/json',
                        }},
                        body: JSON.stringify({{ login_token: token }})
                    }});
                    
                    const status = document.getElementById('status');
                    status.className = 'status error';
                    status.innerHTML = '❌ Console login cancelled.';
                    status.style.display = 'block';
                }} catch (error) {{
                    console.error('Cancel error:', error);
                }}
            }}
        </script>
    </body>
    </html>
    """

@console_login_bp.route('/link', methods=['POST'])
def console_link_confirm():
    """Handle console login confirmation via the web page"""
    # This endpoint is called by JavaScript from the web page
    # The actual confirmation logic is in the /confirm endpoint
    return jsonify({"message": "Use the /confirm endpoint directly"}), 400

@console_login_bp.route('/qr/<login_token>', methods=['GET'])
def generate_qr_code(login_token: str):
    """Generate and serve QR code image for the given login token"""
    if not login_token:
        return jsonify({"error": "Login token required"}), 400
    
    try:
        # Verify token exists and is valid
        with SessionLocal() as session:
            token_hash = hashlib.sha256(login_token.encode()).hexdigest()
            login_token_record = session.query(ConsoleLoginToken).filter(
                ConsoleLoginToken.token_hash == token_hash,
                ConsoleLoginToken.status == LoginTokenStatus.pending
            ).first()
            
            if not login_token_record:
                return jsonify({"error": "Invalid or expired token"}), 404
            
            # Check expiration
            if datetime.now(timezone.utc) > login_token_record.expires_at:
                return jsonify({"error": "Token expired"}), 410
        
        # Generate QR code URL using public base URL
        import os
        public_base_url = os.getenv("PUBLIC_API_URL", "https://api.deckport.ai")
        qr_url = f"{public_base_url}/v1/console-login/link?token={login_token}"
        
        # Create QR code
        qr = qrcode.QRCode(
            version=1,  # Controls the size of the QR Code
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,  # Size of each box in pixels
            border=4,  # Border size
        )
        qr.add_data(qr_url)
        qr.make(fit=True)
        
        # Create image
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Save to BytesIO
        img_buffer = BytesIO()
        img.save(img_buffer, format='PNG')
        img_buffer.seek(0)
        
        return send_file(
            img_buffer,
            mimetype='image/png',
            as_attachment=False,
            download_name=f'qr_code_{login_token[:8]}.png'
        )
        
    except Exception as e:
        return jsonify({"error": "Failed to generate QR code"}), 500
