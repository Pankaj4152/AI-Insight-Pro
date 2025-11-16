#!/usr/bin/env python3
"""
Startup script with better error handling for Cloud Run debugging
"""

import os
import sys
import traceback

def main():
    try:
        print("=== Starting Application ===")
        print(f"Python version: {sys.version}")
        print(f"Working directory: {os.getcwd()}")
        print(f"Environment PORT: {os.environ.get('PORT', 'NOT_SET')}")
        print(f"PYTHONPATH: {os.environ.get('PYTHONPATH', 'NOT_SET')}")
        
        # Test imports
        print("Testing imports...")
        try:
            import fastapi
            print(f"✓ FastAPI {fastapi.__version__}")
        except Exception as e:
            print(f"✗ FastAPI import failed: {e}")
            return 1
            
        try:
            import uvicorn
            print("✓ Uvicorn imported")
        except Exception as e:
            print(f"✗ Uvicorn import failed: {e}")
            return 1
        
        # Test agent imports
        sys.path.append('/app/agents')
        print("Testing agent module imports...")
        
        try:
            from agents.modular_discovery_agent import ModularDiscoveryAgent
            print("✓ ModularDiscoveryAgent")
        except Exception as e:
            print(f"✗ ModularDiscoveryAgent: {e}")
        
        try:
            from agents.modular_scanning_agent import ModularScanningAgent
            print("✓ ModularScanningAgent")
        except Exception as e:
            print(f"✗ ModularScanningAgent: {e}")
        
        try:
            from agents.modular_detection_agent import ModularDetectionAgent
            print("✓ ModularDetectionAgent")
        except Exception as e:
            print(f"✗ ModularDetectionAgent: {e}")
        
        try:
            from agents.sde_pg_agent import SDEAgent
            print("✓ SDEAgent")
        except Exception as e:
            print(f"✗ SDEAgent: {e}")
        
        # Test main app import
        print("Testing main app import...")
        try:
            from agents.driver import app
            print("✓ Main app imported successfully")
        except Exception as e:
            print(f"✗ Main app import failed: {e}")
            traceback.print_exc()
            return 1
        
        # Start the server
        port = int(os.environ.get('PORT', 8000))
        print(f"Starting server on port {port}...")
        
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=port,
            timeout_keep_alive=300,
            log_level="info"
        )
        
    except Exception as e:
        print(f"FATAL ERROR: {e}")
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
