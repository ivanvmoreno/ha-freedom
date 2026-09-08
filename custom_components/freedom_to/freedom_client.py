"""Freedom.to API client implementation."""
from __future__ import annotations

import asyncio
import logging
import re
from typing import Any, Dict, List, Optional
import aiohttp

_LOGGER = logging.getLogger(__name__)

BASE_URL = "https://freedom.to"
DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/plain, */*",
}


class FreedomAuthError(Exception):
    """Raised when authentication fails."""


class FreedomApiError(Exception):
    """Raised when an API call fails."""


class FreedomClient:
    """Client for interfacing with the Freedom.to private web API."""

    def __init__(
        self,
        email: str,
        password: str,
        session: Optional[aiohttp.ClientSession] = None,
    ) -> None:
        """Initialize Freedom API client."""
        self.email = email
        self.password = password
        self._session = session
        self._close_session = False
        self._csrf_token: Optional[str] = None
        self._authenticated = False
        self._lock = asyncio.Lock()

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create an aiohttp client session with cookie jar."""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(
                cookie_jar=aiohttp.CookieJar(unsafe=True),
                headers=DEFAULT_HEADERS,
            )
            self._close_session = True
        return self._session

    async def close(self) -> None:
        """Close the underlying aiohttp session."""
        if self._close_session and self._session and not self._session.closed:
            await self._session.close()

    async def login(self, force: bool = False) -> bool:
        """Authenticate with Freedom.to using email and password."""
        async with self._lock:
            if self._authenticated and not force and self._csrf_token:
                return True

            session = await self._get_session()
            _LOGGER.debug("Attempting to log in to Freedom.to as %s", self.email)

            # Step 1: Fetch the login page to extract CSRF token and initial cookies
            try:
                async with session.get(f"{BASE_URL}/log-in") as resp:
                    if resp.status != 200:
                        raise FreedomAuthError(f"Failed to fetch login page: HTTP {resp.status}")
                    html = await resp.text()

                csrf_match = re.search(r'name="csrf-token" content="([^"]+)"', html)
                if not csrf_match:
                    raise FreedomAuthError("Could not find CSRF token on Freedom login page")

                login_csrf = csrf_match.group(1)

                # Step 2: Post login credentials
                form_data = {
                    "authenticity_token": login_csrf,
                    "session[email]": self.email,
                    "session[password]": self.password,
                }
                async with session.post(
                    f"{BASE_URL}/session",
                    data=form_data,
                    allow_redirects=True,
                ) as resp:
                    resp_text = await resp.text()
                    if resp.status not in (200, 302):
                        raise FreedomAuthError(f"Login failed: HTTP {resp.status}")

                    # Check if login redirected back to log-in or shows invalid credentials
                    if "Invalid email or password" in resp_text or "/log-in" in str(resp.url):
                        raise FreedomAuthError("Invalid Freedom.to email or password")

                    # Step 3: Extract fresh dashboard CSRF token
                    csrf_match = re.search(r'name="csrf-token" content="([^"]+)"', resp_text)
                    if csrf_match:
                        self._csrf_token = csrf_match.group(1)
                    else:
                        # Fallback: re-fetch dashboard to obtain current CSRF token
                        async with session.get(f"{BASE_URL}/dashboard") as dash_resp:
                            dash_text = await dash_resp.text()
                            dash_csrf = re.search(r'name="csrf-token" content="([^"]+)"', dash_text)
                            if dash_csrf:
                                self._csrf_token = dash_csrf.group(1)

                self._authenticated = True
                _LOGGER.info("Successfully authenticated with Freedom.to")
                return True

            except aiohttp.ClientError as err:
                self._authenticated = False
                raise FreedomAuthError(f"Network error during authentication: {err}") from err

    async def _request(
        self,
        method: str,
        path: str,
        json_data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        retry_auth: bool = True,
    ) -> Any:
        """Perform an authenticated request to Freedom.to."""
        if not self._authenticated:
            await self.login()

        session = await self._get_session()
        headers = {
            "X-CSRF-Token": self._csrf_token or "",
            "X-Requested-With": "XMLHttpRequest",
            "Accept": "application/json",
        }
        if json_data is not None:
            headers["Content-Type"] = "application/json"

        url = f"{BASE_URL}{path}" if path.startswith("/") else f"{BASE_URL}/{path}"

        try:
            async with session.request(
                method,
                url,
                json=json_data,
                params=params,
                headers=headers,
            ) as resp:
                if resp.status in (401, 403) and retry_auth:
                    _LOGGER.warning("Freedom session expired (HTTP %s). Re-authenticating...", resp.status)
                    await self.login(force=True)
                    return await self._request(method, path, json_data, params, retry_auth=False)

                if resp.status >= 400:
                    body = await resp.text()
                    raise FreedomApiError(f"Freedom API error {resp.status} on {path}: {body}")

                content_type = resp.headers.get("Content-Type", "")
                if "application/json" in content_type:
                    return await resp.json()
                return await resp.text()

        except aiohttp.ClientError as err:
            raise FreedomApiError(f"Network error on {path}: {err}") from err

    async def get_profile(self) -> Dict[str, Any]:
        """Fetch current user profile and settings."""
        return await self._request("GET", "/profile")

    async def get_devices(self) -> List[Dict[str, Any]]:
        """Fetch all registered user devices."""
        data = await self._request("GET", "/devices")
        return data.get("devices", [])

    async def get_filter_lists(self) -> List[Dict[str, Any]]:
        """Fetch user blocklists (filter lists)."""
        data = await self._request("GET", "/filter_lists")
        return data.get("filter_lists", [])

    async def get_schedules(self) -> List[Dict[str, Any]]:
        """Fetch all schedules and active sessions."""
        data = await self._request("GET", "/schedules")
        return data.get("schedule", [])

    async def get_concluded_sessions(self, page: int = 1) -> Dict[str, Any]:
        """Fetch page of concluded sessions (session history)."""
        return await self._request("GET", f"/concluded_sessions?page={page}")

    async def get_concluded_stats(self) -> Dict[str, Any]:
        """Fetch 7-day focus stats."""
        data = await self._request("GET", "/concluded_sessions/stats")
        return data.get("stats", {})

    async def set_locked_mode(self, enabled: bool) -> Dict[str, Any]:
        """Enable or disable Locked Mode (strong_mode)."""
        return await self._request("PATCH", "/settings/", json_data={"strong_mode": enabled})

    async def start_session(
        self,
        duration_minutes: int = 25,
        filter_list_ids: Optional[List[int]] = None,
        device_ids: Optional[List[int]] = None,
        block_everything: bool = False,
        block_apps: bool = False,
    ) -> Dict[str, Any]:
        """Start a new focus session now.
        
        If filter_list_ids is None, all available filter lists will be used.
        If device_ids is None, all user devices will be included.
        """
        if filter_list_ids is None:
            fl_data = await self.get_filter_lists()
            filter_list_ids = [fl["id"] for fl in fl_data if "id" in fl]

        if device_ids is None:
            dev_data = await self.get_devices()
            device_ids = [d["id"] for d in dev_data if "id" in d]

        payload = {
            "filter_list_ids": filter_list_ids,
            "device_ids": device_ids,
            "block_everything": block_everything,
            "block_apps": block_apps,
            "duration": duration_minutes * 60,
            "start_time": "now",
        }
        _LOGGER.info(
            "Starting Freedom session for %d mins with %d blocklists on %d devices",
            duration_minutes,
            len(filter_list_ids),
            len(device_ids),
        )
        return await self._request("POST", "/schedules/", json_data=payload)

    async def end_session(self, schedule_id: int) -> Dict[str, Any]:
        """End a specific active session."""
        return await self._request("POST", f"/schedules/{schedule_id}/end")

    async def end_all_sessions(self) -> Any:
        """End all currently running sessions."""
        return await self._request("DELETE", "/api/v1/schedules")

    async def save_session_note(self, session_id: int, note: str) -> Dict[str, Any]:
        """Save reflection note on a concluded session."""
        return await self._request("PATCH", f"/concluded_sessions/{session_id}", json_data={"note": note})
