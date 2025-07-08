#!/usr/bin/env python3
"""
Test script for HTTP integration features of the redirect scraper.
"""

import asyncio
import httpx
import json
import time

BASE_URL = "http://127.0.0.1:8000"

async def test_health_check():
    """Test the health check endpoint."""
    print("🏥 Testing health check...")
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/health")
        print(f"Health check: {response.status_code} - {response.json()}")

async def test_sync_scrape():
    """Test the synchronous scrape endpoint."""
    print("\n🔄 Testing sync scrape endpoint...")
    async with httpx.AsyncClient() as client:
        test_url = "https://httpbin.org/redirect/2"
        response = await client.get(f"{BASE_URL}/scrape?url={test_url}")
        result = response.json()
        print(f"Sync scrape result:")
        print(f"  Final URL: {result['final_url']}")
        print(f"  Status: {result['status_code']}")
        print(f"  Redirects: {result['redirect_count']}")
        print(f"  Response time: {result['response_time']:.3f}s")

async def test_async_fetch():
    """Test the asynchronous fetch endpoint."""
    print("\n⚡ Testing async fetch endpoint...")
    async with httpx.AsyncClient() as client:
        payload = {
            "url": "https://httpbin.org/json",
            "user_agent": "Custom-Test-Agent/1.0",
            "timeout": 10
        }
        response = await client.post(f"{BASE_URL}/fetch/", json=payload)
        result = response.json()
        print(f"Async fetch result:")
        print(f"  Final URL: {result['final_url']}")
        print(f"  Status: {result['status_code']}")
        print(f"  Content type: {result['content_type']}")
        print(f"  Response time: {result['response_time']:.3f}s")
        print(f"  Preview: {result['content_preview'][:100]}...")

async def test_batch_fetch():
    """Test the batch fetch endpoint."""
    print("\n📦 Testing batch fetch endpoint...")
    async with httpx.AsyncClient(timeout=30) as client:
        urls = [
            "https://httpbin.org/status/200",
            "https://httpbin.org/redirect/1",
            "https://httpbin.org/json"
        ]
        response = await client.post(f"{BASE_URL}/batch-fetch/", json=urls)
        results = response.json()
        print(f"Batch fetch results ({len(results)} successful):")
        for i, result in enumerate(results):
            print(f"  {i+1}. {result['final_url']} - {result['status_code']} ({result['redirect_count']} redirects)")

async def test_error_handling():
    """Test error handling."""
    print("\n❌ Testing error handling...")
    async with httpx.AsyncClient() as client:
        # Test invalid URL
        payload = {"url": "invalid-url"}
        response = await client.post(f"{BASE_URL}/fetch/", json=payload)
        print(f"Invalid URL test: {response.status_code} - {response.json()['detail']}")
        
        # Test timeout
        payload = {"url": "https://httpbin.org/delay/20", "timeout": 2}
        response = await client.post(f"{BASE_URL}/fetch/", json=payload)
        print(f"Timeout test: {response.status_code} - {response.json()['detail']}")

async def main():
    """Run all tests."""
    print("🚀 Starting HTTP integration tests...")
    
    try:
        await test_health_check()
        await test_sync_scrape()
        await test_async_fetch()
        await test_batch_fetch()
        await test_error_handling()
        print("\n✅ All tests completed!")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")

if __name__ == "__main__":
    asyncio.run(main())

