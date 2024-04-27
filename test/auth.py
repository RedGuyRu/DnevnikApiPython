import datetime
import os

import dnevnik

async def test_auth():
    login = os.getenv("login")
    password = os.getenv("password")
    totp = os.getenv("totp")

    #authenticator = dnevnik.PlayWrightAuthenticator(login, password, headless=False, totp=totp)
    authenticator = dnevnik.FileAuthenticator("auth.json")
    await authenticator.init()
    await authenticator.authenticate()
    await authenticator.close()
    await authenticator.save("auth.json")

    client = dnevnik.DnevnikClient(authenticator)
    schedule = await client.get_visits(datetime.datetime.strptime("2024-04-25","%Y-%m-%d"))
    print(schedule)


if __name__ == "__main__":
    import asyncio
    asyncio.run(test_auth())
