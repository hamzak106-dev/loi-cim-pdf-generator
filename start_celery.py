#!/usr/bin/env python3
"""
Simple script to start Celery worker
"""
import subprocess
import sys
import os

def start_celery_worker():
    """Start Celery worker"""
    try:
        print("🚀 Starting Celery worker...")
        print("📋 Make sure Redis is running on localhost:6379")
        print("⏳ Starting worker...")
        
        # Start Celery worker
        cmd = [
            sys.executable, "-m", "celery", 
            "-A", "celery_app", 
            "worker", 
            "--loglevel=info",
            "--concurrency=2"
        ]
        
        subprocess.run(cmd, cwd=os.path.dirname(os.path.abspath(__file__)))
        
    except KeyboardInterrupt:
        print("\n🛑 Celery worker stopped")
    except Exception as e:
        print(f"❌ Error starting Celery worker: {e}")

if __name__ == "__main__":
    start_celery_worker()
