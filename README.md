# Dnevnik.mos.ru
Официальный порт библиотеки [dnevnik-mos-ru-api](https://github.com/RedGuyRu/DnevnikApi) на Python.

Вы можете задать любые вопросы по этой библиотеке, помочь нам исследовать или обсудить МЭШ в telegram чате https://t.me/sleeplessmash

## Установка

```bash
pip install dnevnik-mos-ru-api
```

## Пример использования

```python
from dnevnik import DnevnikClient, PredefinedAuthenticator

async def main():
    authenticator = PredefinedAuthenticator("123456789", "**REDACTED**")
    await authenticator.init()
    await authenticator.authenticate()
    client = DnevnikClient(authenticator)
    print(await client.get_profile())
    
if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
```
