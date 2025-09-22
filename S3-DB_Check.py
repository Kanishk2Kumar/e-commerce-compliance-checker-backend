from playwright.sync_api import sync_playwright
import time
import boto3
from datetime import datetime

# AWS Configuration
S3_BUCKET_NAME = "sih-25057-backend-storage"
S3_REGION = "ap-south-1"
DYNAMODB_TABLE = "TextractProductImages"

s3_client = boto3.client("s3", region_name=S3_REGION)
dynamodb = boto3.resource("dynamodb", region_name=S3_REGION)
table = dynamodb.Table(DYNAMODB_TABLE)

def upload_to_s3(image_data, s3_key, product_id, image_index):
    """Upload image to S3 with metadata"""
    metadata = {
        "ProductID": str(product_id),
        "ImageIndex": str(image_index),
        "upload-timestamp": datetime.utcnow().isoformat()
    }
    s3_client.put_object(
        Bucket=S3_BUCKET_NAME,
        Key=s3_key,
        Body=image_data,
        ContentType="image/jpeg",
        Metadata=metadata
    )
    print(f"✅ Uploaded to S3: s3://{S3_BUCKET_NAME}/{s3_key}")

def check_if_processed(product_id, image_index):
    """Check if item exists in DynamoDB"""
    try:
        resp = table.get_item(
            Key={
                "ProductID": str(product_id),
                "ImageIndex": str(image_index)
            }
        )
        return "Item" in resp
    except Exception as e:
        print(f"Error checking DynamoDB for {product_id}/{image_index}: {e}")
        return False

def main():
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()

        # Warmup
        page.goto("https://blinkit.com/prn/beanly-choco-hazelnut-spread-with-breadsticks/prid/507408")
        page.wait_for_timeout(3500)

        for pid in range(5, 10):  # test range first
            print(f"\n🔎 Fetching product {pid}...")

            try:
                resp = page.evaluate(
                    """async (pid) => {
                        const r = await fetch(`https://blinkit.com/v1/layout/product/${pid}`, {
                            method: "POST",
                            headers: { "content-type": "application/json" },
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
                print(f"❌ Fetch failed for {pid}: {e}")
                continue

            if resp["status"] != 200:
                print(f"❌ {pid}: {resp['status']}")
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
                print(f"⚠️ Not enough images for {pid}")
                continue

            selected_urls = urls[-4:-1]

            for i, url in enumerate(selected_urls, 1):
                if check_if_processed(pid, i):
                    print(f"⚠️ Already processed {pid}/image_{i}, skipping")
                    continue

                img_resp = page.evaluate(
                    """async (url) => {
                        const r = await fetch(url);
                        const buf = new Uint8Array(await r.arrayBuffer());
                        return Array.from(buf);
                    }""",
                    url,
                )
                image_data = bytes(img_resp)
                s3_key = f"product-images/{pid}/image_{i}.jpg"
                upload_to_s3(image_data, s3_key, pid, i)
                time.sleep(0.5)

        browser.close()

if __name__ == "__main__":
    main()
