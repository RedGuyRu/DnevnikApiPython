from typing import Optional
from playwright.async_api import async_playwright, Browser
from dnevnik import Authenticator, IncorrectLoginPassword
import logging
import asyncio
from dnevnik import TOTPRequested
from mintotp import totp as totp_gen


class PlayWrightAuthenticator(Authenticator):
    _browser: Optional[Browser]
    _logger = logging.getLogger("dnevnik.PlayWrightAuthenticator")
    _studentId: Optional[int]
    _authFinished: bool
    _token: Optional[str]

    def __init__(self, login, password, browser=None, headless=True, sandbox=True, disableAutomationControlled=True,
                 browserArgs=None, totp=None):
        super().__init__()
        if browserArgs is None:
            browserArgs = []
        self._browser = None
        self._options = {}
        self._login = login
        self._password = password
        self._options["browser"] = browser
        self._options["headless"] = headless
        self._options["sandbox"] = sandbox
        self._options["disableAutomationControlled"] = disableAutomationControlled
        self._options["browserArgs"] = browserArgs
        self._options["totp"] = totp

    async def init(self) -> None:
        if self._options["browser"] is None:
            args = []
            if not self._options["sandbox"]:
                args.append("--no-sandbox")
            if self._options["disableAutomationControlled"]:
                args.append("--disable-blink-features=AutomationControlled")
            for browserArg in self._options["browserArgs"]:
                args.append(browserArg)
            p = await async_playwright().start()
            self._browser = await p.chromium.launch(headless=self._options["headless"],
                                                    args=self._options["browserArgs"])
        else:
            self._browser = self._options["browser"]

    async def authenticate(self) -> bool:
        self._authFinished = False
        await self.process_auth()
        return self._authFinished

    async def get_student_id(self) -> int:
        return self._studentId

    async def get_token(self) -> str:
        return self._token

    async def close(self) -> None:
        await self._browser.close()
        self._browser = None

    async def sms_task(self, page):
        await page.wait_for_selector("#sms-code")
        if self._options["totp"] is not None:
            self._logger.debug("SMS request, redirecting to TOTP")
            await page.wait_for_selector("div.twoFa__social--main > div > a:nth-child(2)")
            await page.click("div.twoFa__social--main > div > a:nth-child(2)")
        else:
            self._logger.debug("SMS request, we cannot do anything")
            raise TOTPRequested()

    async def true_input_text(self, page, to_input, input_selector):
        inputted = ""
        while inputted != to_input:
            await page.focus(input_selector)
            for i in range(len(inputted)):
                await page.keyboard.press('Backspace')
            await page.type(input_selector, to_input, delay=100)
            inputted = await page.evaluate(f'() => document.querySelector("{input_selector}").value')

    async def async_true_input_text(self, page, input_lamda, input_selector):
        inputted = ""
        while inputted != input_lamda():
            await page.focus(input_selector)
            for i in range(len(inputted)):
                await page.keyboard.press('Backspace')
            await page.type(input_selector, input_lamda(), delay=100)
            inputted = await page.evaluate(f'() => document.querySelector("{input_selector}").value')

    async def totp_task(self, page):
        await page.wait_for_selector("#otp")
        if self._options["totp"] is not None:
            self._logger.debug("TOTP request")
            await self.async_true_input_text(page, lambda: totp_gen(self._options["totp"]), "#otp")
            self._logger.debug("TOTP sent")
            await page.click("#save")
        else:
            self._logger.debug("TOTP request, we cannot do anything")
            raise TOTPRequested()

    async def trust_task(self, page):
        await page.wait_for_selector("body > div.system__layout > main > section > div > section > h1")
        await page.wait_for_selector("#agree")
        self._logger.debug("Trust request")
        await page.click("#agree")
        self._logger.debug("Trusted")

    async def wait_mobile_profile(self, page):
        await page.wait_for_selector("div.UyNIYBAyL0e8_PyymJKTb")

    async def wait_family_profile(self, page):
        await page.wait_for_url("https://dnevnik.mos.ru/diary/schedules/schedule")

    async def wait_incorrect_password(self, page):
        await page.wait_for_selector("#pswdMethod-c > blockquote > p", timeout=60000)

    async def wait_timeout(self, page):
        await asyncio.sleep(90)

    async def process_auth(self):
        context = await self._browser.new_context()
        page = await context.new_page()
        try:
            self._logger.debug("Loading start page")
            await page.goto('https://school.mos.ru')
            await page.wait_for_selector(
                "#root > div > div.style_main-container__3z5Nv > main > section > div > div.style_sec-intro_left__2XBWp > div.style_sec-intro_aside__2Be41 > div > div.style_aside-login__3YTaH > div.style_aside-login_action__2KJI4 > div")
            await page.click(
                "#root > div > div.style_main-container__3z5Nv > main > section > div > div.style_sec-intro_left__2XBWp > div.style_sec-intro_aside__2Be41 > div > div.style_aside-login__3YTaH > div.style_aside-login_action__2KJI4 > div")

            self._logger.debug("Loading oauth page")
            await page.wait_for_selector("#login")
            await self.true_input_text(page, self._login, "#login")
            await page.wait_for_selector("#password")
            await self.true_input_text(page, self._password, "#password")
            await page.wait_for_selector("#bind")

            self._logger.debug("Authing")
            await page.click("#bind")

            # Create tasks for sms and totp and trust this browser
            sms_task = asyncio.create_task(self.sms_task(page))
            totp_task = asyncio.create_task(self.totp_task(page))
            trust_task = asyncio.create_task(self.trust_task(page))

            # Create finish tasks
            mobile = asyncio.create_task(self.wait_mobile_profile(page))
            family = asyncio.create_task(self.wait_family_profile(page))
            incorrect = asyncio.create_task(self.wait_incorrect_password(page))
            timeout = asyncio.create_task(self.wait_timeout(page))

            self._logger.debug("Waiting for any finish task")
            done = set()
            pending = [mobile, family, incorrect, timeout, sms_task, totp_task, trust_task]
            while not done.intersection([mobile, family, incorrect, timeout]):
                done, pending = await asyncio.wait(pending, return_when=asyncio.FIRST_COMPLETED)

            # Cancel all tasks
            for task in pending:
                task.cancel()

            # Get result from done task
            for task in done:
                if task == mobile:
                    self._logger.debug("Mobile profile finished")
                    await self.finish(page, context)
                    return
                elif task == family:
                    self._logger.debug("Family profile finished")
                    await self.finish(page, context)
                    return
                elif task == incorrect:
                    self._logger.debug("Incorrect password")
                    await context.close()
                    raise IncorrectLoginPassword()
                elif task == timeout:
                    self._logger.debug("Timeout")
                    await context.close()
                    raise TimeoutError()
        except Exception as e:
            await context.close()
            raise

    async def finish(self, page, context):
        self._logger.debug("Finishing")
        cookies = await context.cookies("https://dnevnik.mos.ru/")
        await page.close()
        await context.close()
        profileId = None
        authToken = None
        for cookie in cookies:
            if cookie["name"] == "profile_id":
                profileId = cookie["value"]
            elif cookie["name"] == "auth_token":
                authToken = cookie["value"]
        if profileId is None or authToken is None:
            raise Exception("Auth failed")
        self._authFinished = True
        self._studentId = profileId
        self._token = authToken

    def _set_token(self, token: str) -> None:
        self._token = token
