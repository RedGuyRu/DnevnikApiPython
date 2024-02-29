import json

from dnevnik import Authenticator


class FileAuthenticator(Authenticator):

    def __init__(self, file):
        super().__init__()
        data = json.loads(open(file).read())
        self._studentId = data["studentId"]
        self._token = data["token"]

    async def authenticate(self) -> bool:
        return True

    async def get_student_id(self) -> int:
        return self._studentId

    async def get_token(self) -> str:
        return self._token

    async def _set_token(self, token: str) -> None:
        self._token = token
