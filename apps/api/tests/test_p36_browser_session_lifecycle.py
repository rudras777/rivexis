def test_revoked_cookie_session_cannot_refresh_csrf(client):
    signup=client.post('/api/v1/auth/web/signup',json={
        'email':'session-lifecycle@example.com',
        'password':'correct-horse-battery',
        'role':'Analyst',
    })
    assert signup.status_code==200
    csrf=signup.json()['csrf_token']

    assert client.get('/api/v1/auth/web/csrf').status_code==200
    out=client.post('/api/v1/auth/logout',headers={'X-Rivexis-CSRF':csrf})
    assert out.status_code==200
    assert out.json()['status']=='revoked'

    refreshed=client.get('/api/v1/auth/web/csrf')
    assert refreshed.status_code==401
    assert 'csrf_token' not in refreshed.text


def test_logout_with_invalid_csrf_keeps_cookie_session_valid(client):
    signup=client.post('/api/v1/auth/web/signup',json={
        'email':'session-csrf-guard@example.com',
        'password':'correct-horse-battery',
        'role':'Analyst',
    })
    assert signup.status_code==200

    denied=client.post('/api/v1/auth/logout',headers={'X-Rivexis-CSRF':'invalid-token'})
    assert denied.status_code==403
    assert denied.json()['detail']=='CSRF validation failed'

    # A rejected logout must not silently revoke or clear the authenticated session.
    me=client.get('/api/v1/me')
    assert me.status_code==200
    assert me.json()['email']=='session-csrf-guard@example.com'
