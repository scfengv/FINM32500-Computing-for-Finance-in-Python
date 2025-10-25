from __future__ import annotations
import json
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

from src.patterns.strategy import MarketDataPoint

class YahooFinanceAdapter:
    def __init__(self, path: str | Path):
        self.data = json.loads(Path(path).read_text())

    def get_data(self, symbol: str) -> Optional[MarketDataPoint]:
        node = self.data.get(symbol)
        if not node:
            return None
        ts = datetime.fromisoformat(node["ts"])
        return MarketDataPoint(symbol=symbol, timestamp=ts, price=float(node["price"]), volume=node.get("volume"))

class BloombergXMLAdapter:
    def __init__(self, path: str | Path):
        self.root = ET.fromstring(Path(path).read_text())

    def get_data(self, symbol: str) -> Optional[MarketDataPoint]:
        for security in self.root.findall(".//security"):
            if security.attrib.get("symbol") == symbol:
                px = float(security.findtext("./field[@name='PX_LAST']"))
                vol_text = security.findtext("./field[@name='VOLUME']")
                ts_text = security.findtext("./field[@name='TIME']")
                vol = float(vol_text) if vol_text is not None else None
                ts = datetime.fromisoformat(ts_text) if ts_text else datetime.utcnow()
                return MarketDataPoint(symbol=symbol, timestamp=ts, price=px, volume=vol)
        return None
