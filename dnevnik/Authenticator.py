import json
import aiohttp


class Authenticator:

    async def init(self) -> None:
        pass

    async def authenticate(self) -> bool:
        return False

    async def get_student_id(self) -> int:
        return None

    async def get_token(self) -> str:
        return None

    async def close(self) -> None:
        pass

    async def save(self, path: str) -> None:
        data = {
            "studentId": await self.get_student_id(),
            "token": await self.get_token()
        }
        with open(path, "w") as file:
            file.write(json.dumps(data))

    async def refresh(self) -> None:
        async with aiohttp.ClientSession() as session:
            async with session.get("https://school.mos.ru/v2/token/refresh", headers={
                "cookies": "cluster=0; aupd_current_role=2%3A1",
                "Authorization": f"Bearer {await self.get_token()}"
            }) as response:
                await self._set_token(await response.json())

    async def _set_token(self, token: str) -> None:
        pass
