import sys
import functools
import pydash
import requests
from redis import Redis

from unidecode import unidecode as uc
from requests.exceptions import HTTPError, Timeout

from config import CLIENT_ID, CLIENT_SECRET, REDIS_HOST, REDIS_PORT
from utils import get_file_name_with_no_tags as get_search_term
from logger.logger import log

redis_client = Redis(host=REDIS_HOST, port=REDIS_PORT, db=0, decode_responses=True)


class IGDBHandler:
    def __init__(self) -> None:
        self.platform_url = "https://api.igdb.com/v4/platforms/"
        self.games_url = "https://api.igdb.com/v4/games/"
        self.covers_url = "https://api.igdb.com/v4/covers/"
        self.screenshots_url = "https://api.igdb.com/v4/screenshots/"
        self.twitch_auth = TwitchAuth()
        self.headers = {
            "Client-ID": CLIENT_ID,
            "Authorization": f"Bearer {self.twitch_auth.get_oauth_token()}",
            "Accept": "application/json",
        }

    def check_twitch_token(func) -> tuple:
        @functools.wraps(func)
        def wrapper(*args):
            args[0].headers[
                "Authorization"
            ] = f"Bearer {args[0].twitch_auth.get_oauth_token()}"
            return func(*args)

        return wrapper

    def _request(self, url: str, data: str, timeout: int = 120) -> list:
        try:
            res = requests.post(url, data, headers=self.headers, timeout=timeout)
            res.raise_for_status()
        except (HTTPError, Timeout) as err:
            log.error(err)
            # All requests to the IGDB API return a list
            return []

        return res.json()

    def _search_rom(
        self, search_term: str, p_igdb_id: int, category: int = None
    ) -> dict:
        category_filter: str = f"& category={category}" if category else ""
        roms = self._request(
            self.games_url,
            data=f"""
                search "{search_term}";
                fields id, slug, name, summary, screenshots;
                where platforms=[{p_igdb_id}] {category_filter};
            """,
        )

        return pydash.get(roms, "[0]", {})

    @staticmethod
    def _normalize_cover_url(url: str) -> str:
        return f"https:{url.replace('https:', '')}"

    def _search_cover(self, rom_id: str) -> str:
        covers = self._request(
            self.covers_url,
            data=f"fields url; where game={rom_id};",
        )

        cover = pydash.get(covers, "[0]", None)
        if not cover:
            return ""

        return self._normalize_cover_url(cover["url"])

    def _search_screenshots(self, rom_id: str) -> list:
        screenshots = self._request(
            self.screenshots_url,
            data=f"fields url; where game={rom_id}; limit 5;",
        )

        return [
            self._normalize_cover_url(r["url"]).replace("t_thumb", "t_original")
            for r in screenshots
            if "url" in r.keys()
        ]

    @check_twitch_token
    def get_platform(self, p_slug: str):
        paltforms = self._request(
            self.platform_url,
            data=f'fields id, name; where slug="{p_slug.lower()}";',
        )

        platform = pydash.get(paltforms, "[0]", None)
        if not platform:
            return {
                "igdb_id": "",
                "name": p_slug,
                "slug": p_slug,
            }

        return {
            "igdb_id": platform["id"],
            "name": platform["name"],
            "slug": p_slug,
        }

    @check_twitch_token
    def get_rom(self, file_name: str, p_igdb_id: int):
        search_term = uc(get_search_term(file_name))
        res = (
            self._search_rom(search_term, p_igdb_id, 0)
            or self._search_rom(search_term, p_igdb_id, 10)
            or self._search_rom(search_term, p_igdb_id)
        )

        r_igdb_id = res.get("id", 0)
        r_slug = res.get("slug", "")
        r_name = res.get("name", search_term)
        summary = res.get("summary", "")

        return {
            "r_igdb_id": r_igdb_id,
            "r_slug": r_slug,
            "r_name": r_name,
            "summary": summary,
            "url_cover": self._search_cover(r_igdb_id),
            "url_screenshots": self._search_screenshots(r_igdb_id),
        }

    @check_twitch_token
    def get_rom_by_id(self, r_igdb_id: str):
        roms = self._request(
            self.games_url,
            f"fields slug, name, summary; where id={r_igdb_id};",
        )
        rom = pydash.get(roms, "[0]", {})

        return {
            "r_igdb_id": r_igdb_id,
            "r_slug": rom.get("slug", ""),
            "r_name": rom.get("name", ""),
            "summary": rom.get("summary", ""),
            "url_cover": self._search_cover(r_igdb_id),
            "url_screenshots": self._search_screenshots(r_igdb_id),
        }

    @check_twitch_token
    def get_matched_roms_by_id(self, r_igdb_id: str):
        matched_rom = self.get_rom_by_id(r_igdb_id)
        matched_rom.update(
            url_cover=matched_rom["url_cover"].replace("t_thumb", "t_cover_big"),
        )
        return [matched_rom]

    @check_twitch_token
    def get_matched_roms_by_name(self, search_term: str, p_igdb_id: int):
        matched_roms = self._request(
            self.games_url,
            data=f"""
                search "{uc(search_term)}";
                fields id, slug, name, summary;
                where platforms=[{p_igdb_id}];
            """,
        )

        return [
            dict(
                rom,
                url_cover=self._search_cover(rom["id"]).replace(
                    "t_thumb", "t_cover_big"
                ),
                url_screenshots=self._search_screenshots(rom["id"]),
                r_igdb_id=rom.pop("id"),
                r_slug=rom.pop("slug"),
                r_name=rom.pop("name"),
            )
            for rom in matched_roms
        ]

    @check_twitch_token
    def get_matched_roms(self, file_name: str, p_igdb_id: int):
        if not p_igdb_id:
            return []

        matched_roms = self._request(
            self.games_url,
            data=f"""
                search "{uc(get_search_term(file_name))}";
                fields id, slug, name, summary;
                where platforms=[{p_igdb_id}];
            """,
        )

        return [
            dict(
                rom,
                url_cover=self._search_cover(rom["id"]).replace(
                    "t_thumb", "t_cover_big"
                ),
                url_screenshots=self._search_screenshots(rom["id"]),
                r_igdb_id=rom.pop("id"),
                r_slug=rom.pop("slug"),
                r_name=rom.pop("name"),
            )
            for rom in matched_roms
        ]


class TwitchAuth:
    def _update_twitch_token(self) -> str:
        res = requests.post(
            url="https://id.twitch.tv/oauth2/token",
            params={
                "client_id": CLIENT_ID,
                "client_secret": CLIENT_SECRET,
                "grant_type": "client_credentials",
            },
            timeout=30,
        ).json()

        token = res.get("access_token", "")
        expires_in = res.get("expires_in", 0)
        if not token or expires_in == 0:
            log.error(
                "Could not get twitch auth token: check client_id and client_secret"
            )
            sys.exit(2)

        # Set token in redis to expire in <expires_in> seconds
        redis_client.set("twitch_token", token, ex=expires_in - 10)
        log.info("Twitch token fetched!")

        return token

    def get_oauth_token(self) -> str:
        # Use a fake token when running tests
        if "pytest" in sys.modules:
            return "test_token"

        token = redis_client.get("twitch_token")
        if not token:
            log.warning("Twitch token invalid: fetching a new one...")
            return self._update_twitch_token()

        return token
