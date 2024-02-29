from dnevnik import Authenticator


class PredefinedAuthenticator(Authenticator):
    def __init__(self, student_id, token):
        super().__init__()
        self._studentId = student_id
        self._token = token

    async def authenticate(self) -> bool:
        return True

    async def get_student_id(self) -> int:
        return self._studentId

    async def get_token(self) -> str:
        return self._token

    async def _set_token(self, token: str) -> None:
        self._token = token
