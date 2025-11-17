import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "src"))

import pytest
from fix_parser import FixParser

def test_fix_parser_ok_order():
    raw = '8=FIX.4.2|35=D|55=AAPL|54=1|38=100|40=2|44=150|10=128'
    msg = FixParser().parse(raw)
    assert msg['55'] == 'AAPL'

def test_fix_parser_missing_tag_raises():
    raw = '8=FIX.4.2|35=D|55=AAPL|54=1|40=2|10=128'
    with pytest.raises(ValueError):
        FixParser().parse(raw)