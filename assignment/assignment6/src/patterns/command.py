# command.py
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class ExecutionContext:
    cash: float = 0.0
    positions: Dict[str, float] = field(default_factory=dict)
    trades: List[Dict] = field(default_factory=list)  # audit log


class Command(ABC):
    @abstractmethod
    def execute(self) -> None:
        ...

    @abstractmethod
    def undo(self) -> None:
        ...


class ExecuteOrderCommand(Command):
    """
    Applies an order to context.positions and logs it.
    """
    def __init__(self, context: ExecutionContext, signal: Dict):
        self.ctx = context
        self.signal = signal
        self._applied = False

    def execute(self) -> None:
        if self._applied:
            return
        side = str(self.signal.get("action", "")).upper()
        symbol = self.signal["symbol"]
        qty = float(self.signal["qty"])
        price = float(self.signal.get("price", 0.0))

        delta = qty if side == "BUY" else -qty
        self.ctx.positions[symbol] = self.ctx.positions.get(symbol, 0.0) + delta
        self.ctx.cash -= delta * price  # negative when buying, positive when selling
        self.ctx.trades.append({"event": "EXECUTE", **self.signal})
        self._applied = True

    def undo(self) -> None:
        if not self._applied:
            return
        side = str(self.signal.get("action", "")).upper()
        symbol = self.signal["symbol"]
        qty = float(self.signal["qty"])
        price = float(self.signal.get("price", 0.0))

        delta = qty if side == "BUY" else -qty
        self.ctx.positions[symbol] = self.ctx.positions.get(symbol, 0.0) - delta
        self.ctx.cash += delta * price
        self.ctx.trades.append({"event": "UNDO", **self.signal})
        self._applied = False


class UndoOrderCommand(Command):
    def __init__(self, execute_cmd: ExecuteOrderCommand):
        self.execute_cmd = execute_cmd

    def execute(self) -> None:
        self.execute_cmd.undo()

    def undo(self) -> None:
        self.execute_cmd.execute()


class CommandInvoker:
    def __init__(self):
        self._undo_stack: List[Command] = []
        self._redo_stack: List[Command] = []

    def execute(self, cmd: Command) -> None:
        cmd.execute()
        self._undo_stack.append(cmd)
        self._redo_stack.clear()

    def undo(self) -> Optional[Command]:
        if not self._undo_stack:
            return None
        cmd = self._undo_stack.pop()
        cmd.undo()
        self._redo_stack.append(cmd)
        return cmd

    def redo(self) -> Optional[Command]:
        if not self._redo_stack:
            return None
        cmd = self._redo_stack.pop()
        cmd.execute()
        self._undo_stack.append(cmd)
        return cmd



if __name__ == "__main__":
    ctx = ExecutionContext(cash=100000.0)
    inv = CommandInvoker()

    buy_sig = {"action": "BUY", "symbol": "AAA", "qty": 100, "price": 50.0, "type": "ORDER", "ts": "T1", "reason": "test", "strategy": "Demo"}
    sell_sig = {"action": "SELL", "symbol": "AAA", "qty": 40, "price": 55.0, "type": "ORDER", "ts": "T2", "reason": "test", "strategy": "Demo"}

    c1 = ExecuteOrderCommand(ctx, buy_sig)
    inv.execute(c1)
    print("After BUY:", ctx.positions, ctx.cash)

    c2 = ExecuteOrderCommand(ctx, sell_sig)
    inv.execute(c2)
    print("After SELL:", ctx.positions, ctx.cash)

    inv.undo()
    print("After UNDO (SELL):", ctx.positions, ctx.cash)

    inv.undo()
    print("After UNDO (BUY):", ctx.positions, ctx.cash)

    inv.redo()
    print("After REDO (BUY):", ctx.positions, ctx.cash)

    inv.redo()
    print("After REDO (SELL):", ctx.positions, ctx.cash)



