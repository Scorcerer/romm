from fastapi import APIRouter, Request
from fastapi.responses import FileResponse
from decorators.auth import protected_route
from config import LIBRARY_BASE_PATH, ASSETS_BASE_PATH

router = APIRouter()


@protected_route(router.head, "/raw/roms/{path:path}", ["roms.read"])
def head_raw_rom(request: Request, path: str):
    rom_path = f"{LIBRARY_BASE_PATH}/{path}"
    return FileResponse(path=rom_path, filename=path.split("/")[-1])


@protected_route(router.get, "/raw/roms/{path:path}", ["roms.read"])
def get_raw_rom(request: Request, path: str):
    """Download a single rom file

    Args:
        request (Request): Fastapi Request object

    Returns:
        FileResponse: Returns a single rom file
    """

    rom_path = f"{LIBRARY_BASE_PATH}/{path}"
    return FileResponse(path=rom_path, filename=path.split("/")[-1])


@protected_route(router.head, "/raw/assets/{path:path}", ["assets.read"])
def head_raw_asset(request: Request, path: str):
    asset_path = f"{ASSETS_BASE_PATH}/{path}"
    return FileResponse(path=asset_path, filename=path.split("/")[-1])


@protected_route(router.get, "/raw/assets/{path:path}", ["assets.read"])
def get_raw_asset(request: Request, path: str):
    """Download a single asset file

    Args:
        request (Request): Fastapi Request object

    Returns:
        FileResponse: Returns a single asset file
    """

    asset_path = f"{ASSETS_BASE_PATH}/{path}"
    return FileResponse(path=asset_path, filename=path.split("/")[-1])
