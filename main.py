import sys
import aiohttp
import asyncio
from loguru import logger

logger.add(sys.stdout, colorize=True, format="<g>{time:HH:mm:ss:SSS}</g> | <level>{message}</level>")
asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

BASE_URL = "https://fapi.binance.com"
PROXY = "http://127.0.0.1:7890"

class ROSE:
    def __init__(self):
        self.session = None

    async def __aenter__(self):
        timeout = aiohttp.ClientTimeout(15)
        self.session = aiohttp.ClientSession(timeout=timeout)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.session.close()

    #------------symbols------------
    async def fetch_symbols(self):
        url = f"{BASE_URL}/fapi/v1/exchangeInfo"
        try:
            async with self.session.get(url, proxy=PROXY) as rep:
                data = await rep.json()
                return [
                    s["symbol"]
                    for s in data["symbols"]
                    if s["contractType"] == "PERPETUAL"
                       and s["quoteAsset"] == "USDT"
                       and s["status"] == "TRADING"
                ]
        except Exception as e:
            logger.error(e)

    # ------------k线数据------------
    async def fetch_ohlcv(self, symbol, interval):
        url = f"{BASE_URL}/fapi/v1/klines"
        params = {"symbol": symbol, "interval": interval, "limit": 2}
        try:
            async with self.session.get(url, proxy=PROXY, params=params) as rep:
                result = await rep.json()
                print(result)
        except Exception as e:
            logger.error(e)

#------------运行函数------------
async def main():
    async with ROSE() as rose:
        symbols = await rose.fetch_symbols()
        tasks = [asyncio.create_task(rose.fetch_ohlcv(symbol, "1m")) for symbol in symbols]
        data = await asyncio.gather(*tasks)
        if not isinstance(data, list):
            return None
        if len(data) < 2:
            return None

if __name__ == "__main__":
    asyncio.run(main())

