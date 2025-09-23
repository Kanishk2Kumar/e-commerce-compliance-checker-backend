from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import httpx
import math
import asyncio
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Simple Central Server")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # or ["http://localhost:3000"] for stricter
    allow_credentials=True,
    allow_methods=["*"],  # allow POST, GET, OPTIONS, etc.
    allow_headers=["*"],
)

# Manually managed worker nodes
WORKERS = {
    "worker1": "http://3.109.32.215",
    "worker2": "http://65.1.135.96",
    "worker3": "http://43.205.117.94",
    "worker4": "http://13.127.179.164",
    "worker5": "http://15.206.212.158",
    "worker6": "http://43.204.145.94",
    "worker7": "http://13.203.156.229",
    "worker8": "http://3.111.36.65",
    "worker9": "http://13.203.227.37",
    "worker10": "http://3.110.177.200",
    # Add more like:
    # "worker4": "http://NEW_IP:8000"
}

class RangeRequest(BaseModel):
    start: int
    end: int

@app.post("/dispatch")
async def dispatch_range(req: RangeRequest):
    start, end = req.start, req.end
    if start >= end:
        raise HTTPException(status_code=400, detail="Invalid range")

    num_workers = len(WORKERS)
    total = end - start + 1
    chunk_size = math.ceil(total / num_workers)

    tasks = []
    assignments = {}

    worker_items = list(WORKERS.items())
    for i, (worker_name, worker_url) in enumerate(worker_items):
        chunk_start = start + i * chunk_size
        chunk_end = min(chunk_start + chunk_size - 1, end)
        if chunk_start > end:
            break

        payload = {"start": chunk_start, "end": chunk_end}
        assignments[worker_name] = {"url": worker_url, "range": payload}

        tasks.append(send_to_worker(worker_url, payload, worker_name))

    results = await asyncio.gather(*tasks, return_exceptions=True)

    for worker_name, result in zip(assignments.keys(), results):
        if isinstance(result, Exception):
            assignments[worker_name]["status"] = f"Error: {str(result)}"
        else:
            assignments[worker_name]["status"] = result

    return {"workers_assigned": assignments}

async def send_to_worker(worker_url: str, payload: dict, worker_name: str):
    try:
        async with httpx.AsyncClient(timeout=20) as client:
            resp = await client.post(f"{worker_url}/scan-range", json=payload)
            return {"code": resp.status_code, "response": resp.text}
    except Exception as e:
        return {"error": str(e)}
