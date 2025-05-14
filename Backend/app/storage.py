# Backend/app/storage.py
from typing import Union
from rocksdict import Rdict, Options

class Storage:
    def __init__(self, path: str):
        self.db = Rdict(
            path,
            options=Options(raw_mode=True, create_if_missing=True)
        )

    def put(self, key: bytes, value: bytes):
        self.db[key] = value

    def get(self, key: bytes) -> Union[bytes, None]:
        return self.db.get(key, None)

    def delete(self, key: bytes):
        if key in self.db:
            del self.db[key]

    def close(self):
        self.db.close()
