async def test_register_is_closed_without_token(api):
    response = await api.post(
        "/register",
        json={"email": "new@test.com", "full_name": "New Manager", "password": "pass12345"},
    )

    assert response.status_code in (401, 403)


async def test_register_with_token_does_not_leak_password(api, auth_headers):
    response = await api.post(
        "/register",
        json={"email": "new@test.com", "full_name": "New Manager", "password": "pass12345"},
        headers=auth_headers,
    )

    assert response.status_code == 200
    body = response.json()
    assert body["email"] == "new@test.com"
    assert "password" not in body
    assert "hashed_password" not in body


async def test_login_success(api, manager_account):
    response = await api.post(
        "/login",
        json={"email": manager_account["email"], "password": manager_account["password"]},
    )

    assert response.status_code == 200
    assert "access_token" in response.json()


async def test_login_wrong_password(api, manager_account):
    response = await api.post(
        "/login",
        json={"email": manager_account["email"], "password": "wrong-password"},
    )

    assert response.status_code == 401