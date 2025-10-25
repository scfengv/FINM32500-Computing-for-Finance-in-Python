from __future__ import annotations
import pandas as pd
from typing import Dict
from src.decorator import (
    Instrument,
    VolatilityDecorator,
    BetaDecorator,
    DrawdownDecorator,
)

def compute_all_metrics(inst: Instrument, market_df: pd.DataFrame, benchmark: str) -> Dict:
    decorated = DrawdownDecorator(
        BetaDecorator(VolatilityDecorator(inst, market_df), market_df, benchmark),
        market_df,
    )
    return decorated.get_metrics()
