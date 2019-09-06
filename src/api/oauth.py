import json
import re
import requests

from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from oauth2_provider.models import AccessToken


def generate_github_access_token(github_client_id, github_client_secret, github_code):
    """
    create an access token to access the GitHub API. Exchange the code for an access token
    :param github_client_id: client_id from https://github.com/settings/developers
    :param github_client_secret: client secret from https://github.com/settings/developers
    :param github_code: authentication code generated by client from http://github.com/login/oauth/authorize/
    :return: json content containing access token
    """
    auth_response = requests.post(
        'https://github.com/login/oauth/access_token/',
        data=json.dumps({
            'client_id': github_client_id,
            'client_secret': github_client_secret,
            'code': github_code
        }),
        headers={'content-type': 'application/json'}
    )
    token = re.search(r'access_token=([a-zA-Z0-9]+)', auth_response.content.decode('utf-8'))
    if token is None:
        raise PermissionDenied(auth_response)
    return token.group(1)


def convert_to_auth_token(url, client_id, client_secret, backend, token):
    """
    given a previously generated access_token use the django-rest-framework-social-oauth2
    endpoint `/convert-token/` to authenticate the user and return a django auth
    token
    :param client_id: generated from the OathToolkit application
    :param client_secret: generated from the OathToolkit application
    :param backend: backend used for authentication('github', 'facebook', etc.)
    :param token: access token generated from the backend
    :return: json containing the django auth token
    """
    params = {
        'grant_type': 'convert_token',
        'client_id': client_id,
        'client_secret': client_secret,
        'backend': backend,
        'token': token,
    }
    response = requests.post(url + 'auth/convert-token/', params=params)
    return response.json()['access_token']


def get_user_from_token(django_auth_token):
    """
    Retrieve the user object given an access token
    :param django_auth_token: Oathtoolkit access token
    :return: user object
    """
    userID = AccessToken.objects.get(token=django_auth_token).user_id
    return User.objects.get(id=userID)