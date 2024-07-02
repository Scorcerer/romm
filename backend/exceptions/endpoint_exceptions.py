from fastapi import HTTPException, status
from logger.logger import log


class PlatformNotFoundInDatabaseException(Exception):
    def __init__(self, id):
        self.message = f"Platform with id '{id}' not found"
        super().__init__(self.message)
        log.critical(self.message)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=self.message)

    def __repr__(self) -> str:
        return self.message


class RomNotFoundInDatabaseException(Exception):
    def __init__(self, id):
        self.message = f"Rom with id '{id}' not found"
        super().__init__(self.message)
        log.critical(self.message)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=self.message)

    def __repr__(self) -> str:
        return self.message
