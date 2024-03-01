import os

import dnevnik

async def test_auth():
    login = os.getenv("login")
    password = os.getenv("password")
    totp = os.getenv("totp")

    authenticator = dnevnik.PlayWrightAuthenticator(login, password, headless=False, totp=totp)
    await authenticator.init()
    await authenticator.authenticate()
    await authenticator.close()

    client = dnevnik.Client(authenticator)
    schedule = await client.get_schedule()
    print(schedule)

    await authenticator.save("auth.json")


if __name__ == "__main__":
    import asyncio
    asyncio.run(test_auth())
