# Backend/app/consensus.py
import raftos

class RaftNode:
    def __init__(self, self_addr: str, peers: list[str]):
        raftos.configure({
            'log_path': f'./raft-{self_addr.replace(":", "_")}.log'
        })
        self.self_addr = self_addr
        raftos.register(self_addr, peers)

    async def start(self):
        # Isto vai arrancar a FSM; fica para implementar depois.
        pass
