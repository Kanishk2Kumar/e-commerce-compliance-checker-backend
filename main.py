from playwright.sync_api import sync_playwright
from pathlib import Path
import time

BASE_URL = "https://blinkit.com/v1/layout/product/{}"
OUTPUT_ROOT = Path("Product-Images")
OUTPUT_ROOT.mkdir(exist_ok=True)

def main():
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=False)  # set True if you want invisible
        context = browser.new_context()
        page = context.new_page()

        # visit a real product page once (sets cookies/session)
        page.goto("https://blinkit.com/prn/beanly-choco-hazelnut-spread-with-breadsticks/prid/507408")
        page.wait_for_timeout(4000)  # wait for Blinkit JS to fire

        for idx, pid in enumerate(range(0, 101), start=1):   # process IDs 0–100
            print(f"\n🔎 Fetching {pid}...")
            try:
                resp = page.evaluate(
                    """async (pid) => {
                        const r = await fetch(`https://blinkit.com/v1/layout/product/${pid}`, {
                            method: "POST",
                            headers: {
                                "content-type": "application/json"
                            },
                            body: "{}"
                        });
                        if (!r.ok) {
                            return {status: r.status, text: await r.text()};
                        }
                        return {status: r.status, data: await r.json()};
                    }""",
                    pid,
                )
            except Exception as e:
                print(f"❌ JS fetch failed for {pid}: {e}")
                continue

            if resp["status"] != 200:
                print(f"❌ {pid}: {resp['status']}")
                print("Snippet:", resp.get("text", "")[:300])
                continue

            data = resp["data"]
            urls = []
            try:
                snippets = data["response"]["snippets"]
                for sn in snippets:
                    itemlist = sn.get("data", {}).get("itemList", [])
                    for item in itemlist:
                        assets = (
                            item.get("data", {})
                                .get("click_action", {})
                                .get("show_gallery", {})
                                .get("assets", [])
                        )
                        urls.extend([a["image_url"] for a in assets if a.get("asset_type") == "image"])
            except Exception:
                pass

            if len(urls) < 4:
                print(f"⚠️ Not enough images found for {pid}")
                continue

            # take 4th-last to 2nd-last
            urls = urls[-4:-1]
            folder = OUTPUT_ROOT / str(pid)
            folder.mkdir(parents=True, exist_ok=True)

            for i, url in enumerate(urls, 1):
                try:
                    img_resp = page.evaluate(
                        """async (url) => {
                            const r = await fetch(url);
                            const buf = new Uint8Array(await r.arrayBuffer());
                            return Array.from(buf);
                        }""",
                        url,
                    )
                    path = folder / f"image_{i}.jpg"
                    with open(path, "wb") as f:
                        f.write(bytes(img_resp))
                    print(f"✅ Saved {path}")
                except Exception as e:
                    print(f"❌ Failed {url}: {e}")

            # delay after every 40 product IDs
            if idx % 40 == 0:
                print("⏳ Processed 40 product IDs, sleeping for 60s...")
                time.sleep(60)

        browser.close()

if __name__ == "__main__":
    main()
