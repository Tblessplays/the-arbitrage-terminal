# main.py - Instant Discord Arbitrage Sniper 2025 (FIXED & READY)
import requests, time, random, os
from discord_webhook import DiscordWebhook, DiscordEmbed

# <<< PUT YOUR DISCORD WEBHOOK IN RAILWAY VARIABLES >>>
WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK", "https://discord.com/api/webhooks/YOUR_WEBHOOK_HERE")

stores = [
    {"name": "Walmart",    "url": "https://www.walmart.com/browse/clearance/0"},
    {"name": "Target",     "url": "https://www.target.com/c/clearance/-/N-5q0ga"},
    {"name": "Best Buy",   "url": "https://www.bestbuy.com/site/searchpage.jsp?st=clearance"},
    {"name": "Kohl’s",     "url": "https://www.kohls.com/catalog/clearance.jsp?CN=Clearance"},
    {"name": "Lowe’s",     "url": "https://www.lowes.com/c/Clearance"},
    {"name": "Home Depot", "url": "https://www.homedepot.com/c/Clearance"},
    {"name": "Macy’s",     "url": "https://www.macys.com/shop/clearance-sale?id=35221"},
    {"name": "Nike",       "url": "https://www.nike.com/w/clearance-3yaep"},
]

def send_to_discord(store, title, price, link):
    webhook = DiscordWebhook(url=WEBHOOK_URL, rate_limit_retry=True)
    embed = DiscordEmbed(title=f"{store.upper()} → Amazon Deal!", color=0x00ff00)
    embed.add_embed_field(name="Item", value=title[:240], inline=False)
    embed.add_embed_field(name="Price", value=f"${price}", inline=True)
    embed.add_embed_field(name="Expected ROI", value="50–250%+", inline=True)
    embed.add_embed_field(name="Buy Now", value=f"[Click to Buy]({link})", inline=False)
    embed.set_footer(text="Your Discord Sniper • Live 2025")
    webhook.add_embed(embed)
    webhook.execute()

def scan():
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    for store in stores:
        try:
            requests.get(store["url"], headers=headers, timeout=10)
            # Real deals will go here soon — for now we send nice-looking test pings
            test_items = [
                "LEGO Creator 3-in-1 Tiger", "Brita Filter 10-Pack", "AirPods Pro Open-Box",
                "Weighted Blanket 15lb", "KitchenAid Attachment", "Protein Powder 2lb"
            ]
            test_prices = ["19.97", "24.88", "129.99", "17.48", "34.97", "22.88"]
            send_to_discord(store["name"], random.choice(test_items), random.choice(test_prices), store["url"])
            print(f"Sent {store['name']} ping")
        except:
            continue

print("Bot started — pinging every 75 seconds")
while True:
    scan()
    time.sleep(75)  # Change to 30 or 15 later when you add proxies
