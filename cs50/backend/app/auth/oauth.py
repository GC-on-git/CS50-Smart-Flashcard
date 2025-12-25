"""
OAuth2 authentication support (Google/GitHub)
"""
from typing import Optional, Dict
from fastapi import HTTPException, status
from authlib.integrations.starlette_client import OAuth
from starlette.config import Config
from app.core.config import settings

# Initialize OAuth
config_dict = {}
if settings.GOOGLE_CLIENT_ID:
    config_dict.update({
        "GOOGLE_CLIENT_ID": settings.GOOGLE_CLIENT_ID,
        "GOOGLE_CLIENT_SECRET": settings.GOOGLE_CLIENT_SECRET or "",
    })

if settings.GITHUB_CLIENT_ID:
    config_dict.update({
        "GITHUB_CLIENT_ID": settings.GITHUB_CLIENT_ID,
        "GITHUB_CLIENT_SECRET": settings.GITHUB_CLIENT_SECRET or "",
    })

oauth = OAuth(Config(environ=config_dict))

# Register OAuth providers
if settings.GOOGLE_CLIENT_ID:
    oauth.register(
        name='google',
        server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
        client_kwargs={
            'scope': 'openid email profile'
        }
    )

# GitHub OAuth
if settings.GITHUB_CLIENT_ID:
    oauth.register(
        name='github',
        client_id=settings.GITHUB_CLIENT_ID,
        client_secret=settings.GITHUB_CLIENT_SECRET,
        authorize_url='https://github.com/login/oauth/authorize',
        authorize_params=None,
        access_token_url='https://github.com/login/oauth/access_token',
        access_token_params=None,
        refresh_token_url=None,
        client_kwargs={'scope': 'user:email'},
    )

async def get_oauth_user_info(provider: str, token: Dict) -> Optional[Dict[str, str]]:
    """
    Get user information from OAuth provider.
    
    Args:
        provider: OAuth provider name ('google', 'github', etc.)
        token: OAuth access token
        
    Returns:
        dict: User information (email, username, oauth_id) or None
    """
    try:
        if provider == 'google':
            client = oauth.google
            resp = await client.get('userinfo', token=token)
            user_info = resp.json()
            return {
                'email': user_info.get('email'),
                'username': user_info.get('name') or user_info.get('email', '').split('@')[0],
                'oauth_id': user_info.get('sub'),
                'provider': 'google'
            }
        elif provider == 'github':
            client = oauth.github
            resp = await client.get('user', token=token)
            user_info = resp.json()
            # Get email from GitHub (might need separate call)
            email_resp = await client.get('user/emails', token=token)
            emails = email_resp.json()
            primary_email = next((e['email'] for e in emails if e.get('primary')), emails[0]['email'] if emails else None)
            
            return {
                'email': primary_email or f"{user_info.get('login')}@users.noreply.github.com",
                'username': user_info.get('login'),
                'oauth_id': str(user_info.get('id')),
                'provider': 'github'
            }
        return None
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to get user info from {provider}: {str(e)}"
        )

