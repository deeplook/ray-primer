"""Actor ordering — calls on one actor run serially and share state."""

import ray

from _ray_config import init_ray

init_ray()


@ray.remote(num_cpus=1)
class Ledger:
    def __init__(self) -> None:
        self.balance = 0

    def deposit(self, amount: int) -> int:
        self.balance += amount
        return self.balance


ledger = Ledger.remote()
refs = [ledger.deposit.remote(amount) for amount in (10, 5, -3, 8)]
print("ordered balances:", ray.get(refs))
