from playwright.sync_api import sync_playwright
import time
import boto3
from io import BytesIO
import os

# AWS S3 Configuration
S3_BUCKET_NAME = "sih-25057-backend-storage"
S3_REGION = "ap-south-1"

# Initialize S3 client
s3_client = boto3.client(
    's3',
    region_name=S3_REGION,
    # If not using AWS CLI configuration, uncomment and add your credentials:
    # aws_access_key_id='YOUR_ACCESS_KEY',
    # aws_secret_access_key='YOUR_SECRET_KEY'
)

BASE_URL = "https://blinkit.com/v1/layout/product/{}"

def upload_to_s3(image_data, s3_key):
    """Upload image data to S3 bucket"""
    try:
        s3_client.put_object(
            Bucket=S3_BUCKET_NAME,
            Key=s3_key,
            Body=image_data,
            ContentType='image/jpeg'
        )
        print(f"✅ Uploaded to S3: s3://{S3_BUCKET_NAME}/{s3_key}")
        return True
    except Exception as e:
        print(f"❌ Failed to upload to S3: {e}")
        return False

def main():
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()

        # visit a real product page once (sets cookies/session)
        page.goto("https://blinkit.com/prn/beanly-choco-hazelnut-spread-with-breadsticks/prid/507408")
        page.wait_for_timeout(4000)

        for idx, pid in enumerate(range(0, 101), start=1):
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
                    
                    # Convert to bytes
                    image_data = bytes(img_resp)
                    
                    # Create S3 key (path in bucket)
                    s3_key = f"product-images/{pid}/image_{i}.jpg"
                    
                    # Upload to S3
                    upload_to_s3(image_data, s3_key)
                    
                except Exception as e:
                    print(f"❌ Failed {url}: {e}")

            # delay after every 40 product IDs
            if idx % 40 == 0:
                print("⏳ Processed 40 product IDs, sleeping for 60s...")
                time.sleep(60)

        browser.close()

if __name__ == "__main__":
    main()