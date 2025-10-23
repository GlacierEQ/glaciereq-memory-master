#!/usr/bin/env python3
"""
Security Middleware
API key authentication and local-only binding
"""

import os
from fastapi import HTTPException, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional

security = HTTPBearer(auto_error=False)

class SecurityMiddleware:
    def __init__(self):
        self.api_key_enabled = bool(os.getenv('API_KEY'))
        self.required_api_key = os.getenv('API_KEY', '')
        self.bind_local = os.getenv('API_BIND_LOCAL', 'false').lower() == 'true'
    
    async def validate_api_key(self, request: Request) -> bool:
        """Validate API key if enabled"""
        if not self.api_key_enabled:
            return True  # No API key required
        
        # Check X-API-Key header
        api_key = request.headers.get('X-API-Key')
        if not api_key:
            # Check Authorization header as fallback
            auth_header = request.headers.get('Authorization', '')
            if auth_header.startswith('Bearer '):
                api_key = auth_header[7:]  # Remove 'Bearer ' prefix
        
        if not api_key:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="API key required. Provide X-API-Key header or Bearer token.",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        if api_key != self.required_api_key:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid API key",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        return True
    
    async def validate_local_access(self, request: Request) -> bool:
        """Validate local-only access if enabled"""
        if not self.bind_local:
            return True  # Allow all IPs
        
        client_host = request.client.host if request.client else None
        
        # Allow localhost and loopback
        allowed_hosts = ['127.0.0.1', 'localhost', '::1']
        
        if client_host not in allowed_hosts:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access restricted to localhost only. Client IP: {client_host}"
            )
        
        return True

# Global security instance
security_middleware = SecurityMiddleware()

async def security_dependency(request: Request):
    """FastAPI dependency for security checks"""
    await security_middleware.validate_local_access(request)
    await security_middleware.validate_api_key(request)
    return True

def get_security_status() -> dict:
    """Get current security configuration status"""
    return {
        'api_key_enabled': security_middleware.api_key_enabled,
        'local_binding_enabled': security_middleware.bind_local,
        'uvicorn_host': os.getenv('UVICORN_HOST', '0.0.0.0'),
        'security_level': 'HIGH' if security_middleware.api_key_enabled and security_middleware.bind_local else 'MEDIUM'
    }