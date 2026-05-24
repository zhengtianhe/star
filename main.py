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
        self.semaphore = asyncio.Semaphore(20)

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
                data = await rep.json()
                if not isinstance(data, list):
                    return None
                if len(data) < 2:
                    return None
                k = data[-2]
                open_time = int(k[0])
                return {
                    "symbol": symbol,
                    "open_time": open_time,
                    "open": float(k[1]),
                    "high": float(k[2]),
                    "low": float(k[3]),
                    "close": float(k[4]),
                    "volume": float(k[5])
                }
        except Exception as e:
            logger.error(e)

    # ------------OI------------
    async def fetch_OI(self, symbol):
        url = f"{BASE_URL}/fapi/v1/openInterest"
        params = {"symbol": symbol}
        try:
            async with self.session.get(url, proxy=PROXY, params=params) as rep:
                data = await rep.json()
                return float(data.get("openInterest", 0))
        except Exception as e:
            logger.error(e)

    # ------------任务处理------------
    async def fetch_all(self, symbol):
        async with self.semaphore:
            kline_task = asyncio.create_task(self.fetch_ohlcv(symbol, "1m"))
            oi_task = asyncio.create_task(self.fetch_OI(symbol))
            kline = await kline_task
            oi = await oi_task
            return {
                "symbol": symbol,
                "kline": kline,
                "oi": oi
            }

#------------运行函数------------
async def main():
    async with ROSE() as rose:
        symbols = await rose.fetch_symbols()
        tasks = [asyncio.create_task(rose.fetch_all(symbol)) for symbol in symbols]
        data = await asyncio.gather(*tasks)
        print(data)
        # if not isinstance(data, list):
        #     return None
        # if len(data) < 2:
        #     return None

if __name__ == "__main__":
    asyncio.run(main())

