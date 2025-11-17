# fix_parser.py
class FixParser:
    def parse(self, raw_msg: str):
        fields = {}
        for part in raw_msg.split('|'):
            if not part:
                continue
            if '=' not in part:
                continue
            tag, value = part.split('=', 1)
            fields[tag] = value

        if '35' not in fields:
            raise ValueError('Missing FIX tag 35 (MsgType)')

        msg_type = fields['35']

        if msg_type == 'D': # Order
            required = ['55', '54', '38', '40']  # symbol, side, qty, order type
            missing = [t for t in required if t not in fields]
            if missing:
                raise ValueError(f'Missing FIX tag(s) for order: {missing}')
        
            if fields['40'] == '2' and '44' not in fields: # Need price for limit order
                    raise ValueError('Missing FIX tag 44 (Price) for limit order')
        
        if msg_type == 'S': # Quote
            quote_required = ['55', '132']  # symbol + bid/offer price
            missing = [t for t in quote_required if t not in fields]
            if missing:
                raise ValueError(f'Missing FIX tag(s) for quote: {missing}')

        return fields

if __name__ == "__main__":
    msg = "8=FIX.4.2|35=D|55=AAPL|54=1|38=100|40=2|10=128"
    print(FixParser().parse(msg))