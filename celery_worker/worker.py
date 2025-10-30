#!/usr/bin/env python3
"""
Script to start Celery worker
"""
import subprocess
import sys
import os
from pathlib import Path


def start_celery_worker():
    """Start Celery worker"""
    try:
        print("🚀 Starting Celery worker...")
        print("📋 Make sure Redis is running on localhost:6379")

        # Resolve project root dynamically
        project_root = Path(__file__).resolve().parent.parent
        print(f"📂 Working directory: {project_root}")

        cmd = [
            sys.executable,
            "-m",
            "celery",
            "-A",
            "celery_worker.celery_config",  # ✅ matches your structure
            "worker",
            "--loglevel=info",
            "--concurrency=2"
        ]

        subprocess.run(cmd, cwd=str(project_root))

    except KeyboardInterrupt:
        print("\n🛑 Celery worker stopped manually.")
    except Exception as e:
        print(f"❌ Error starting Celery worker: {e}")


if __name__ == "__main__":
    start_celery_worker()
