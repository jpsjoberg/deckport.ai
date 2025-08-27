"""
API Service for communicating with the Deckport API
Handles authentication, requests, and error handling
"""

import requests
import os
from typing import Optional, Dict, Any
from flask import current_app, session
import logging

logger = logging.getLogger(__name__)

class APIService:
    """Service for making authenticated requests to the Deckport API"""
    
    def __init__(self):
        self.base_url = os.getenv('API_BASE_URL', 'http://127.0.0.1:8002')
        self.timeout = 30
        
    def _get_headers(self, use_admin_token: bool = True) -> Dict[str, str]:
        """Get headers for API requests"""
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        
        # Get admin JWT from request context
        if use_admin_token:
            try:
                from flask import request
                admin_jwt = request.cookies.get("admin_jwt")
                if admin_jwt:
                    headers['Authorization'] = f'Bearer {admin_jwt}'
                else:
                    logger.warning("No admin JWT token found in request cookies")
            except RuntimeError:
                # Outside request context - no fallback token
                logger.warning("No request context available for admin JWT")
        
        return headers
    
    def _make_request(self, method: str, endpoint: str, data: Optional[Dict] = None) -> Optional[Dict[str, Any]]:
        """Make HTTP request to API"""
        url = f"{self.base_url}{endpoint}"
        headers = self._get_headers()
        
        try:
            if method.upper() == 'GET':
                response = requests.get(url, headers=headers, timeout=self.timeout)
            elif method.upper() == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=self.timeout)
            elif method.upper() == 'PUT':
                response = requests.put(url, json=data, headers=headers, timeout=self.timeout)
            elif method.upper() == 'DELETE':
                response = requests.delete(url, headers=headers, timeout=self.timeout)
            else:
                logger.error(f"Unsupported HTTP method: {method}")
                return None
            
            # Log request for debugging
            logger.info(f"API {method} {url} -> {response.status_code}")
            if response.status_code != 200 and response.status_code != 201:
                logger.error(f"API Error Response: {response.text}")
            
            if response.status_code == 200:
                json_response = response.json()
                logger.info(f"API Success Response: {len(str(json_response))} chars")
                return json_response
            elif response.status_code == 201:
                json_response = response.json()
                logger.info(f"API Success Response: {len(str(json_response))} chars")
                return json_response
            elif response.status_code == 404:
                logger.warning(f"API endpoint not found: {url}")
                return None
            else:
                logger.error(f"API request failed: {response.status_code} - {response.text}")
                return None
                
        except requests.exceptions.Timeout:
            logger.error(f"API request timeout: {url}")
            return None
        except requests.exceptions.ConnectionError:
            logger.error(f"API connection error: {url}")
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"API request error: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error in API request: {e}")
            return None
    
    def get(self, endpoint: str) -> Optional[Dict[str, Any]]:
        """Make GET request to API"""
        return self._make_request('GET', endpoint)
    
    def post(self, endpoint: str, data: Optional[Dict] = None) -> Optional[Dict[str, Any]]:
        """Make POST request to API"""
        return self._make_request('POST', endpoint, data)
    
    def put(self, endpoint: str, data: Optional[Dict] = None) -> Optional[Dict[str, Any]]:
        """Make PUT request to API"""
        return self._make_request('PUT', endpoint, data)
    
    def delete(self, endpoint: str) -> Optional[Dict[str, Any]]:
        """Make DELETE request to API"""
        return self._make_request('DELETE', endpoint)
    
    def health_check(self) -> bool:
        """Check if API is healthy"""
        try:
            response = self.get('/health')
            return response is not None and response.get('status') == 'ok'
        except Exception:
            return False
