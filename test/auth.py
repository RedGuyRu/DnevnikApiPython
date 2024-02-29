import os

import dnevnik

async def test_auth():
    login = os.getenv("login")
    password = os.getenv("password")
    totp = os.getenv("totp")

    authenticator = dnevnik.PlayWrightAuthenticator(login, password, headless=False, totp=totp)
    await authenticator.init()
    await authenticator.authenticate()
    print(await authenticator.get_student_id())
    print(await authenticator.get_token())
    await authenticator.close()
    await authenticator.save("auth.json")


if __name__ == "__main__":
    import asyncio
    asyncio.run(test_auth())
