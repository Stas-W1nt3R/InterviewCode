from urllib.parse import parse_qs
from rest_framework_simplejwt.tokens import AccessToken
from rest_framework_simplejwt.exceptions import TokenError
from channels.middleware import BaseMiddleware
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from .models import User
import logging

logger = logging.getLogger(__name__)

@database_sync_to_async
def get_user_from_token(token):
    try:
        token = AccessToken(token)
        user_id = token['user_id']
        return User.objects.get(id=user_id)

    except (TokenError, User.DoesNotExist, KeyError) as e:
        logger.warning('JWT auth is failed: %r', e)
        return AnonymousUser()

class JWTAuthMiddleware(BaseMiddleware):
    async def __call__(self, scope, receive, send):
        query_string = scope.get('query_string', b'').decode()
        params = parse_qs(query_string)
        token = params.get('token', [None])[0]

        if token:
            scope['user'] = await get_user_from_token(token)

        else:
            scope['user'] = AnonymousUser()

        return await super().__call__(scope, receive, send)