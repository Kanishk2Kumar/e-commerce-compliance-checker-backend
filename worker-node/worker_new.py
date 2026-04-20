# worker_api.py
import os
import time
import boto3
import random
import json
from datetime import datetime
from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
from playwright.sync_api import sync_playwright

# ----- AWS CONFIG -----
S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME", "sih-25057-prod-916273703597")
S3_REGION = os.getenv("S3_REGION", "us-east-1")
DYNAMODB_TABLE = os.getenv("DYNAMODB_TABLE", "TextractProductImages")

# AWS clients
s3_client = boto3.client("s3", region_name=S3_REGION)
dynamodb = boto3.resource("dynamodb", region_name=S3_REGION)
table = dynamodb.Table(DYNAMODB_TABLE)

# ----- FASTAPI SETUP -----
app = FastAPI(title="Worker Node Listener")

# ----- REQUEST MODEL -----
class ScanRequest(BaseModel):
    start: int
    end: int
    headless: bool = True

# ----- RATE LIMITING CONFIG -----
PRODUCTS_BEFORE_DELAY = 50  # Process 50 products before taking a break
DELAY_DURATION = 45         # 45 second delay
REQUEST_DELAY_MIN = 0.5       # Minimum delay between individual requests
REQUEST_DELAY_MAX = 1.5       # Maximum delay between individual requests
DEBUG_BODY_SNIPPET_CHARS = 400
PRODUCT_FETCH_MAX_ATTEMPTS = 2

# ----- HELPERS -----
def upload_to_s3(image_data, s3_key, product_id, image_index):
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
    print(f"✅ Uploaded: {s3_key}")


def check_if_processed(product_id, image_index):
    try:
        resp = table.get_item(Key={"ProductID": str(product_id), "ImageIndex": str(image_index)})
        return "Item" in resp
    except Exception as e:
        print(f"Error checking DynamoDB: {e}")
        return False


def calculate_progress(current, start, end):
    """Calculate and display progress percentage"""
    total = end - start + 1
    processed = current - start + 1
    percentage = (processed / total) * 100
    return percentage


def _shorten(value, max_len=DEBUG_BODY_SNIPPET_CHARS):
    if value is None:
        return ""
    text = str(value)
    if len(text) <= max_len:
        return text
    return f"{text[:max_len]}...(truncated)"


def log_session_debug(context, page):
    try:
        ua = page.evaluate("() => navigator.userAgent")
        cookies = context.cookies("https://blinkit.com")
        cookie_names = [c.get("name", "") for c in cookies[:10]]
        print(f"🧪 Debug session: page_url={page.url}")
        print(f"🧪 Debug session: user_agent={ua}")
        print(f"🧪 Debug session: cookie_count={len(cookies)} first_cookies={cookie_names}")
    except Exception as exc:
        print(f"⚠️ Could not collect session debug info: {exc}")


def fetch_product_payload(page, pid):
    last_result = None
    for attempt in range(1, PRODUCT_FETCH_MAX_ATTEMPTS + 1):
        result = page.evaluate("""async ({ productId, bodySnippetChars }) => {
            try {
                const reqHeaders = {
                    'Content-Type': 'application/json',
                    'Accept': 'application/json, text/plain, */*',
                    'Origin': 'https://blinkit.com',
                    'Referer': 'https://blinkit.com/'
                };

                const response = await fetch(`https://blinkit.com/v1/layout/product/${productId}`, {
                    method: 'POST',
                    headers: reqHeaders,
                    credentials: 'include',
                    body: JSON.stringify({})
                });

                const text = await response.text();
                const responseHeaders = {};
                for (const [k, v] of response.headers.entries()) {
                    const lk = k.toLowerCase();
                    if (['content-type', 'server', 'via', 'cf-ray', 'x-cache'].includes(lk)) {
                        responseHeaders[k] = v;
                    }
                }

                if (!response.ok) {
                    return {
                        success: false,
                        status: response.status,
                        error: `HTTP ${response.status}`,
                        body_snippet: text.slice(0, bodySnippetChars),
                        response_url: response.url,
                        response_headers: responseHeaders,
                        request_headers: reqHeaders,
                        page_url: window.location.href
                    };
                }

                try {
                    const data = JSON.parse(text);
                    return {
                        success: true,
                        data: data,
                        status: response.status
                    };
                } catch (parseErr) {
                    return {
                        success: false,
                        status: response.status,
                        error: `JSON parse error: ${String(parseErr)}`,
                        body_snippet: text.slice(0, bodySnippetChars),
                        response_url: response.url,
                        response_headers: responseHeaders,
                        request_headers: reqHeaders,
                        page_url: window.location.href
                    };
                }
            } catch (error) {
                return {
                    success: false,
                    status: 0,
                    error: String(error),
                    page_url: window.location.href
                };
            }
        }""", {"productId": pid, "bodySnippetChars": DEBUG_BODY_SNIPPET_CHARS})

        if result.get("success"):
            if attempt > 1:
                print(f"✅ Product {pid}: succeeded on retry attempt {attempt}")
            return result

        last_result = result
        status = result.get("status")
        print(f"❌ Product {pid}: attempt {attempt}/{PRODUCT_FETCH_MAX_ATTEMPTS} failed - {result.get('error', 'Unknown error')}")
        print(f"🧪 Product {pid} debug: status={status} response_url={result.get('response_url', '')} page_url={result.get('page_url', '')}")
        if result.get("response_headers"):
            print(f"🧪 Product {pid} headers: {json.dumps(result.get('response_headers'), ensure_ascii=True)}")
        if result.get("request_headers"):
            print(f"🧪 Product {pid} request headers: {json.dumps(result.get('request_headers'), ensure_ascii=True)}")
        if result.get("body_snippet"):
            print(f"🧪 Product {pid} body snippet: {_shorten(result.get('body_snippet'))}")

        if status == 403 and attempt < PRODUCT_FETCH_MAX_ATTEMPTS:
            wait_seconds = 3 * attempt
            print(f"⏳ Product {pid}: got 403, re-warming session and retrying in {wait_seconds}s...")
            page.goto("https://blinkit.com/", wait_until='domcontentloaded', timeout=60000)
            page.wait_for_timeout(2500)
            time.sleep(wait_seconds)
            continue

        break

    return last_result or {"success": False, "status": 0, "error": "Unknown fetch failure"}

# ----- MAIN WORKER FUNCTION WITH RATE LIMITING -----
def run_scan(start, end, headless=True):
    print(f"🚀 Starting scan from {start} to {end}")
    print(f"⚡ Rate limiting: {PRODUCTS_BEFORE_DELAY} products → {DELAY_DURATION}s delay")
    if not headless and not os.getenv("DISPLAY") and not os.getenv("WAYLAND_DISPLAY"):
        print("⚠️ No display server detected; forcing headless mode for Playwright.")
        headless = True
    
    with sync_playwright() as pw:
        # Launch browser with better stealth options
        browser = pw.chromium.launch(
            headless=headless,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--no-sandbox',
                '--disable-dev-shm-usage'
            ]
        )
        
        # Create context with stealth settings
        context = browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        )
        
        # Remove webdriver property
        page = context.new_page()
        page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined,
            });
        """)
        
        try:
            # Proper warmup - visit actual page and wait for full load
            print("🌐 Warming up browser session...")
            warmup_url = "https://blinkit.com/prn/beanly-choco-hazelnut-spread-with-breadsticks/prid/1"
            page.goto(warmup_url, wait_until='domcontentloaded', timeout=60000)
            page.wait_for_timeout(5000)  # Wait for full page load
            
            # Scroll to trigger more loading
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            page.wait_for_timeout(2000)
            
            print("✅ Warmup completed successfully")
            log_session_debug(context, page)
            
            success_count = 0
            fail_count = 0
            total_products = end - start + 1
            
            for index, pid in enumerate(range(start, end + 1)):
                current_progress = calculate_progress(pid, start, end)
                
                print(f"\n📊 Progress: {current_progress:.1f}% ({index + 1}/{total_products})")
                print(f"🔎 Processing Product ID: {pid}")
                
                # ---- RATE LIMITING: Check if we need to take a break ----
                if index > 0 and index % PRODUCTS_BEFORE_DELAY == 0:
                    print(f"⏳ Processed {PRODUCTS_BEFORE_DELAY} products. Taking {DELAY_DURATION} second break...")
                    
                    # Display progress before delay
                    elapsed_ids = index
                    remaining_ids = total_products - index - 1
                    print(f"📈 Progress: {elapsed_ids} done, {remaining_ids} remaining")
                    
                    # Countdown timer
                    for remaining in range(DELAY_DURATION, 0, -10):
                        if remaining > 10:
                            print(f"🕒 Resuming in {remaining} seconds...")
                            time.sleep(10)
                        else:
                            print(f"🕒 Resuming in {remaining} seconds...")
                            time.sleep(1)
                    
                    print("🚀 Resuming scan...")
                
                # Random delay between individual requests
                delay = random.uniform(REQUEST_DELAY_MIN, REQUEST_DELAY_MAX)
                time.sleep(delay)
                
                try:
                    result = fetch_product_payload(page, pid)
                    
                    if not result.get('success'):
                        fail_count += 1
                        continue
                    
                    data = result['data']
                    urls = []
                    
                    # Extract image URLs with better error handling
                    try:
                        if 'response' in data and 'snippets' in data['response']:
                            for snippet in data['response']['snippets']:
                                items = snippet.get('data', {}).get('itemList', [])
                                for item in items:
                                    assets = item.get('data', {}).get('click_action', {}).get('show_gallery', {}).get('assets', [])
                                    for asset in assets:
                                        if asset.get('asset_type') == 'image' and 'image_url' in asset:
                                            urls.append(asset['image_url'])
                    except Exception as e:
                        print(f"⚠️ Error extracting URLs for {pid}: {e}")
                    
                    if len(urls) < 3:
                        print(f"⚠️ Not enough images found for {pid} (found {len(urls)})")
                        fail_count += 1
                        continue
                    
                    # Take last 5 images (or available ones)
                    selected_urls = urls[-5:-1] if len(urls) >= 3 else urls
                    print(f"📷 Found {len(urls)} images, processing {len(selected_urls)}")
                    
                    image_count = 0
                    for i, url in enumerate(selected_urls, 1):
                        if check_if_processed(pid, i):
                            print(f"⏭️ Image {i} for {pid} already processed, skipping")
                            continue
                            
                        try:
                            # Download image through browser context
                            image_response = page.evaluate("""async (imageUrl) => {
                                try {
                                    const response = await fetch(imageUrl);
                                    if (!response.ok) throw new Error(`HTTP ${response.status}`);
                                    const arrayBuffer = await response.arrayBuffer();
                                    return Array.from(new Uint8Array(arrayBuffer));
                                } catch (error) {
                                    return { error: error.toString() };
                                }
                            }""", url)
                            
                            if isinstance(image_response, dict) and 'error' in image_response:
                                print(f"❌ Failed to download image {url}: {image_response['error']}")
                                continue
                            
                            image_data = bytes(image_response)
                            s3_key = f"product-images/{pid}/image_{i}.jpg"
                            
                            upload_to_s3(image_data, s3_key, pid, i)
                            image_count += 1
                            
                            # Small delay between image uploads
                            time.sleep(0.3)
                            
                        except Exception as e:
                            print(f"❌ Error processing image {i} for {pid}: {e}")
                    
                    if image_count > 0:
                        success_count += 1
                        print(f"✅ Successfully processed {image_count} images for product {pid}")
                    else:
                        fail_count += 1
                        
                except Exception as e:
                    print(f"❌ Unexpected error processing {pid}: {e}")
                    fail_count += 1
            
            print(f"\n🎉 Batch completed!")
            print(f"📊 Summary: {success_count} successful, {fail_count} failed out of {total_products} total")
            
        except Exception as e:
            print(f"💥 Critical error in scan process: {e}")
        finally:
            browser.close()

# ----- FASTAPI ENDPOINTS -----
@app.post("/scan-range")
async def scan_range(request: ScanRequest, background_tasks: BackgroundTasks):
    """Start a scan range in background with rate limiting"""
    if request.start > request.end:
        raise HTTPException(status_code=400, detail="Start must be less than or equal to end")
    
    if request.end - request.start > 1000:
        raise HTTPException(status_code=400, detail="Range too large. Max 1000 products per request")
    
    total_products = request.end - request.start + 1
    estimated_time = calculate_estimated_time(total_products)
    
    background_tasks.add_task(run_scan, request.start, request.end, request.headless)
    
    return {
        "status": "started", 
        "message": f"Scanning products from {request.start} to {request.end}",
        "total_products": total_products,
        "rate_limiting": f"{PRODUCTS_BEFORE_DELAY} products → {DELAY_DURATION}s delay",
        "estimated_duration": estimated_time,
        "task_id": f"scan_{request.start}_{request.end}_{int(time.time())}"
    }


def calculate_estimated_time(total_products):
    """Calculate estimated completion time"""
    batches = total_products // PRODUCTS_BEFORE_DELAY
    remaining = total_products % PRODUCTS_BEFORE_DELAY
    
    # Base time per product (seconds)
    time_per_product = (REQUEST_DELAY_MIN + REQUEST_DELAY_MAX) / 2 + 2  # 2 seconds for processing
    
    total_time = (total_products * time_per_product) + (batches * DELAY_DURATION)
    
    # Convert to minutes/hours
    if total_time > 3600:
        return f"{total_time/3600:.1f} hours"
    elif total_time > 60:
        return f"{total_time/60:.1f} minutes"
    else:
        return f"{total_time:.0f} seconds"

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy", 
        "timestamp": datetime.utcnow().isoformat(),
        "service": "Worker Node API",
        "rate_limiting": {
            "products_before_delay": PRODUCTS_BEFORE_DELAY,
            "delay_duration": DELAY_DURATION,
            "request_delay_range": f"{REQUEST_DELAY_MIN}-{REQUEST_DELAY_MAX}s"
        }
    }

@app.get("/check-product/{product_id}")
async def check_product(product_id: int):
    """Check if a product has been processed"""
    images_processed = []
    for i in range(1, 4):  # Check for images 1-3
        if check_if_processed(product_id, i):
            images_processed.append(i)
    
    return {
        "product_id": product_id,
        "processed_images": images_processed,
        "fully_processed": len(images_processed) == 3
    }

@app.get("/rate-limit-config")
async def get_rate_limit_config():
    """Get current rate limiting configuration"""
    return {
        "products_before_delay": PRODUCTS_BEFORE_DELAY,
        "delay_duration_seconds": DELAY_DURATION,
        "request_delay_min": REQUEST_DELAY_MIN,
        "request_delay_max": REQUEST_DELAY_MAX
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
