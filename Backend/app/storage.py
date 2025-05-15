# backend/app/storage.py
from rocksdict import Rdict, Options


class Storage:
    def __init__(self, path: str):
        # raw_mode=True → as chaves/valores já vêm em bytes,
        # deixa-os exactamente como estão.
        opts = Options(raw_mode=True)
        # NÃO mexemos em create_if_missing: o default já cria
        self.db = Rdict(path, options=opts)

    def put(self, k: bytes, v: bytes):
        self.db[k] = v

    def get(self, k: bytes):
        return self.db.get(k, None)

    def delete(self, k: bytes):
        if k in self.db:
            del self.db[k]

    def close(self):
        self.db.close()
