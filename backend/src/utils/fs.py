import os
import shutil
from pathlib import Path

import requests
from fastapi import HTTPException

from config.config import user_config, LIBRARY_BASE_PATH, RESERVED_FOLDERS, DEFAULT_URL_COVER_L, DEFAULT_PATH_COVER_L, DEFAULT_URL_COVER_S, DEFAULT_PATH_COVER_S
from logger.logger import log


# ========= Defaults utils =========
def store_default_resources(overwrite: bool) -> None:
    """Store default no_cover resources in the filesystem
    
    Args:
        overwrite: flag to overwrite or not default resources
    """
    if overwrite or not r_cover_exists('default', 'cover', 'l'):
        store_r_cover('default', 'cover', DEFAULT_URL_COVER_L, 'l')
    if overwrite or not r_cover_exists('default', 'cover', 's'):
        store_r_cover('default', 'cover', DEFAULT_URL_COVER_S, 's')


# ========= Platforms utils =========
def get_platforms() -> list[str]:
    """Gets all filesystem platforms
    
    Returns list with all the filesystem platforms found in the LIBRARY_BASE_PATH.
    Automatically discards the reserved directories such resources or database directory.
    """
    try:
        if os.path.exists(f"{LIBRARY_BASE_PATH}/roms"):
            platforms: list[str] = list(os.walk(f"{LIBRARY_BASE_PATH}/roms"))[0][1]
        else:
            platforms: list[str] = list(os.walk(LIBRARY_BASE_PATH))[0][1]
        [platforms.remove(reserved) for reserved in RESERVED_FOLDERS if reserved in platforms]
        try:
            excluded_folders: list = user_config['exclude']['folders']
            try:
                [platforms.remove(excluded) for excluded in excluded_folders if excluded in platforms]
            except TypeError:
                pass
        except KeyError:
            pass
        log.info(f"filesystem platforms found: {platforms}")
        return platforms
    except IndexError:
        raise HTTPException(status_code=404, detail="Platforms not found.")


# ========= Roms utils =========
def r_cover_exists(p_slug: str, filename_no_ext: str, size: str) -> bool:
    """Check if rom cover exists in filesystem
    
    Args:
        p_slug: short name of the platform
        filename_no_ext: name of rom file without extension
        size: size of the cover -> big as 'l' | small as 's'
    Returns
        True if cover exists in filesystem else False
    """
    logo_path: str = f"{LIBRARY_BASE_PATH}/resources/{p_slug}/{filename_no_ext}_{size}.png"
    return True if os.path.exists(logo_path) else False


def get_r_cover_path(p_slug: str, filename_no_ext: str, size: str) -> str:
    """Returns platform logo filesystem path
    
    Args:
        p_slug: short name of the platform
        filename_no_ext: name of rom file without extension
        size: size of the cover -> big as 'l' | small as 's'
    """
    return f"/assets/library/resources/{p_slug}/{filename_no_ext}_{size}.png"


def store_r_cover(p_slug: str, filename_no_ext: str, url_cover: str, size: str) -> None:
    """Store roms resources in filesystem
    
    Args:
        p_slug: short name of the platform
        filename_no_ext: name of rom file without extension
        url_cover: url to get the cover
        size: size of the cover -> big as 'l' | small as 's'
    """
    cover_file: str = f"{filename_no_ext}_{size}.png"
    cover_path: str = f"{LIBRARY_BASE_PATH}/resources/{p_slug}/"
    sizes: dict = {'l': 'big', 's': 'small'}
    res = requests.get(url_cover.replace('t_thumb', f't_cover_{sizes[size]}'), stream=True)
    if res.status_code == 200:
        Path(cover_path).mkdir(parents=True, exist_ok=True)
        with open(f"{cover_path}/{cover_file}", 'wb') as f:
            shutil.copyfileobj(res.raw, f)
        log.info(f"{filename_no_ext} {sizes[size]} cover downloaded successfully!")
    else:
        log.warning(f"{filename_no_ext} {sizes[size]} cover couldn't be downloaded")


def get_cover_details(overwrite: bool, p_slug: str, filename_no_ext: str, url_cover: str) -> tuple:
    path_cover_s: str = DEFAULT_PATH_COVER_S
    path_cover_l: str = DEFAULT_PATH_COVER_L
    has_cover: int = 0
    if (overwrite or not r_cover_exists(p_slug, filename_no_ext, 's')) and url_cover:
        store_r_cover(p_slug, filename_no_ext, url_cover, 's')
    if r_cover_exists(p_slug, filename_no_ext, 's'):
        path_cover_s = get_r_cover_path(p_slug, filename_no_ext, 's')
    
    if (overwrite or not r_cover_exists(p_slug, filename_no_ext, 'l')) and url_cover:
        store_r_cover(p_slug, filename_no_ext, url_cover, 'l')
    if r_cover_exists(p_slug, filename_no_ext, 'l'):
        path_cover_l = get_r_cover_path(p_slug, filename_no_ext, 'l')
        has_cover = 1
    return path_cover_s, path_cover_l, has_cover


def get_roms(p_slug: str, only_amount: bool = False) -> list[dict]:
    """Gets all filesystem roms for a platform

    Args:
        p_slug: short name of the platform
        only_amount: flag to return only amount of roms instead of all info
    Returns: list with all the filesystem roms for a platform found in the LIBRARY_BASE_PATH. Just the amount of them if only_amount=True
    """
    try:
        roms: list[dict] = []
        if os.path.exists(f"{LIBRARY_BASE_PATH}/roms"):
            roms_path: str = f"{LIBRARY_BASE_PATH}/roms/{p_slug}"
            roms_filename = list(os.walk(f"{LIBRARY_BASE_PATH}/roms/{p_slug}"))[0][2]
        else:
            roms_path: str = f"{LIBRARY_BASE_PATH}/{p_slug}/roms"
            roms_filename = list(os.walk(f"{LIBRARY_BASE_PATH}/{p_slug}/roms"))[0][2]
        try:
            try:
                excluded_files: list = user_config['exclude']['files']
                filtered_files: list = []
                for filename in roms_filename:
                    if filename.split('.')[-1] in excluded_files:
                        filtered_files.append(filename)
                roms_filename = [f for f in roms_filename if f not in filtered_files]
            except TypeError:
                pass
        except KeyError:
            pass
        if only_amount: return len(roms_filename)
        [roms.append({'filename': rom, 'size': str(round(os.stat(f"{roms_path}/{rom}").st_size / (1024 * 1024), 2))}) for rom in roms_filename]
        log.info(f"filesystem roms found for {p_slug}: {roms}")
    except IndexError:
        log.warning(f"roms not found for {p_slug}")
    return roms


def r_exists(p_slug: str, filename: str) -> bool:
    """Check if rom exists in filesystem
    
    Args:
        p_slug: short name of the platform
        filename: rom filename
    Returns
        True if rom exists in filesystem else False
    """
    rom_path: str = f"{LIBRARY_BASE_PATH}/{p_slug}/roms/{filename}"
    exists: bool = True if os.path.exists(rom_path) else False
    return exists


def rename_rom(p_slug: str, filename: str, data: dict) -> None:
    if data['filename'] != filename:
        if r_exists(p_slug, data['filename']): raise HTTPException(status_code=500, detail=f"Can't rename: {data['filename']} already exists.")
        os.rename(f"{LIBRARY_BASE_PATH}/{p_slug}/roms/{filename}",
                  f"{LIBRARY_BASE_PATH}/{p_slug}/roms/{data['filename']}")
    

def delete_rom(p_slug: str, filename: str) -> None:
    try:
        os.remove(f"{LIBRARY_BASE_PATH}/{p_slug}/roms/{filename}")
    except FileNotFoundError:
        log.warning(f"Rom not found in filesystem: {p_slug}/{filename}")
