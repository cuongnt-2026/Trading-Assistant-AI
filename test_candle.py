from datetime import datetime
from src.market.candle import Candle

c = Candle(
    datetime.now(),
    100,
    105,
    95,
    102,
    1000
)

print(c)