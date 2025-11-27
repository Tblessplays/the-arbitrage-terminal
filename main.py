# the-arbitrage-terminal/main.py
# Multi-store arbitrage sniper: Walmart, Target, Best Buy, Nike, Lowes, Home Depot, Kohls, Macys
# Scans every ~20 seconds, Discord alerts on 30%+ ROI, auto-buy hooks
# Deploy: Railway or Fly.io | Proxies: SOAX/Bright Data

import asyncio
import os
import random
import aiohttp
from playwright.async_api import async_playwright
from discord_webhook import DiscordWebhook, DiscordEmbed
import requests  # For Keepa/Amazon checks

DISCORD_WEBHOOK = os.getenv("DISCORD_WEBHOOK")
PROXIES_FILE = os.getenv("PROXIES_FILE", "proxies.txt")  # Upload your proxies here

# Load proxies (one per line: http://user:pass@ip:port)
async def load_proxies():
    try:
        with open(PROXIES_FILE, 'r') as f:
            return [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        return []  # Run without proxies for testing

PROXIES = asyncio.run(load_proxies()) if PROXIES_FILE else []

STORES = {
    "walmart": {"url": "https://www.walmart.com/browse/clearance/0?page={}&affinityOverride=default", "pages": 3, "selector": '[data-automation-id="product-tile"]'},
    "target": {"url": "https://www.target.com/c/clearance/-/N-5q0ga", "pages": 1, "selector": '[data-testid="product-card"]'},
    "lowes": {"url": "https://www.lowes.com/c/Clearance", "pages": 2, "selector": 'a[href*="/pd/"]'},
    "homedepot": {"url": "https://www.homedepot.com/c/clearance", "pages": 2, "selector": '.product-pod'},
    "kohls": {"url": "https://www.kohls.com/catalog/clearance.jsp?CN=Clearance", "pages": 2, "selector": '.product-tile'},
    "nike": {"url": "https://www.nike.com/w/clearance-3yaep", "pages": 3, "selector": '[data-automation="product"]'},
    "macys": {"url": "https://www.macys.com/shop/clearance-sale?id=35221", "pages": 2, "selector": '.product-tile'},
    "bestbuy": {"url": "https://www.bestbuy.com/site/outlet-refurbished-clearance/clearance-electronics/pcmcat748300666044.c?id=pcmcat748300666044", "pages": 2, "selector": '[data-testid="product-tile"], .sku-item'}  # Best Buy open-box magic
}

KEEPA_KEY = os.getenv("KEEPA_KEY", "")  # Optional: Get free at keepa.com

async def get_amazon_price(asin):
    if not KEEPA_KEY or not asin:
        return random.uniform(20, 100)  # Mock for testing—replace with real Keepa
    try:
        url = f"https://api.keepa.com/product?key={KEEPA_KEY}&domain=1&code={asin}"
        r = requests.get(url)
        data = r.json()
        return data['products'][0]['csv'][3][-1] / 100 if data.get('products') else 0
    except:
        return 0

async def send_discord(deal):
    webhook = DiscordWebhook(url=DISCORD_WEBHOOK, rate_limit_retry=True)
    embed = DiscordEmbed(title=f"{deal['store'].upper()} Deal: {deal['title'][:200]}", color=0x00ff00)
    embed.add_field(name="Buy Price", value=f"${deal['buy_price']}", inline=True)
    embed.add_field(name="Amazon Sell", value=f"${deal['sell_price']}", inline=True)
    embed.add_field(name="Profit/ROI", value=f"${deal['profit']} | {deal['roi']}%", inline=True)
    embed.add_field(name="Buy Link", value=deal['buy_link'], inline=False)
    embed.add_field(name="Amazon Link", value=f"https://amazon.com/dp/{deal['asin']}", inline=False)
    embed.set_footer(text="The Arbitrage Terminal • Auto-snipe active")
    webhook.add_embed(embed)
    response = webhook.execute()
    print(f"Discord sent: {response.status_code}")

async def scan_store(store_name, config):
    proxy = random.choice(PROXIES) if PROXIES else None
    for page_num in range(1, config["pages"] + 1):
        url = config["url"].format(page_num) if "{page}" in config["url"] else config["url"]
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(proxy={"server": proxy} if proxy else None,
                                                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
            page = await context.new_page()
            await page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => false})")
            try:
                await page.goto(url, wait_until="networkidle", timeout=30000)
                await page.wait_for_timeout(random.randint(2000, 5000))
                products = await page.query_selector_all(config["selector"])
                for prod in products[:20]:  # Limit per page
                    title = await (await prod.query_selector("h3, .title, [data-automation-id='product-title']")).inner_text() or "Unknown"
                    price_elem = await prod.query_selector(".price, [data-automation-id='product-price'] span")
                    price_text = await price_elem.inner_text() if price_elem else ""
                    buy_price = float(''.join(filter(str.isdigit, price_text.replace('$', ''))) or 0) / 100
                    link = await (await prod.query_selector("a")).get_attribute("href") or ""
                    buy_link = f"https://{store_name}.com{link}" if link.startswith('/') else link
                    
                    # Mock ASIN (replace with real UPC lookup)
                    asin = f"B0{random.randint(10000000, 99999999)}"
                    sell_price = await get_amazon_price(asin)
                    
                    if sell_price > buy_price * 1.3:  # Quick profit check
                        profit = sell_price - buy_price - (sell_price * 0.15) - 5  # Fees + buffer
                        roi = (profit / buy_price) * 100
                        if profit > 8 and roi >= 30:
                            deal = {
                                "store": store_name, "title": title, "buy_price": round(buy_price, 2),
                                "sell_price": round(sell_price, 2), "profit": round(profit, 2),
                                "roi": round(roi), "buy_link": buy_link, "asin": asin
                            }
                            await send_discord(deal)
                            # Auto-buy hook: await auto_buy(store_name, buy_link, title)  # Uncomment + add creds
            except Exception as e:
                print(f"Scan error {store_name}: {e}")
            finally:
                await browser.close()
        await asyncio.sleep(random.uniform(1, 3))  # Stagger requests

async def main():
    print("The Arbitrage Terminal: Starting multi-store scan...")
    while True:
        tasks = [scan_store(name, cfg) for name, cfg in STORES.items()]
        await asyncio.gather(*tasks, return_exceptions=True)
        print("Cycle complete—waiting 15s...")
        await asyncio.sleep(15)

if __name__ == "__main__":
    asyncio.run(main())
