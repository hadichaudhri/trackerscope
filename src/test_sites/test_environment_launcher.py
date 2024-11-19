import os
from tracking_test_sites import TrackingTestSites


def main():
    # Initialize the test environment
    test_sites = TrackingTestSites(port_start=8000)

    print("Starting test environment...")
    print("\nTest sites available at:")
    print("Main site: http://localhost:8000")
    print("Third-party tracker: http://localhost:8001")
    print("Analytics service: http://localhost:8002")

    print("\nTracking implementations include:")
    print("1. First-party cookies")
    print("2. Third-party cookies")
    print("3. Local Storage tracking")
    print("4. Cookie syncing")
    print("5. Canvas fingerprinting")
    print("6. Browser fingerprinting")
    print("7. Cookie respawning")
    print("8. Analytics events")

    try:
        test_sites.run()
        print("\nPress Ctrl+C to stop the test environment")
        # Keep the main thread alive
        while True:
            pass
    except KeyboardInterrupt:
        print("\nShutting down test environment...")


if __name__ == "__main__":
    main()
