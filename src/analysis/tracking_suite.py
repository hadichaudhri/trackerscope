import os
import argparse
from datetime import datetime
from tracking_test_sites import TrackingTestSites
from cookie_monitor import CookieMonitor
from storage_monitor import StorageMonitor
from network_monitor import NetworkMonitor
from javascript_monitor import JavaScriptMonitor
from tracking_analysis_engine import TrackingAnalysisEngine
import threading
import time


class TrackingResearchSuite:
    def __init__(self, base_port=8000):
        self.base_port = base_port
        self.monitors = {}
        self.test_sites = None
        self.analysis_engine = None

    def setup_environment(self):
        """Setup test environment and monitoring systems"""
        print("Setting up test environment...")

        # Initialize test sites
        self.test_sites = TrackingTestSites(port_start=self.base_port)

        # Initialize monitors
        self.monitors['cookie'] = CookieMonitor()
        self.monitors['storage'] = StorageMonitor()
        self.monitors['network'] = NetworkMonitor()
        self.monitors['javascript'] = JavaScriptMonitor()

        # Initialize analysis engine
        self.analysis_engine = TrackingAnalysisEngine()

        print("Environment setup complete.")

    def start_monitoring(self):
        """Start all monitoring systems"""
        print("Starting monitoring systems...")

        base_url = f"http://localhost:{self.base_port}"

        # Start monitors
        for name, monitor in self.monitors.items():
            print(f"Starting {name} monitor...")
            monitor.start_monitoring(base_url)

    def start_test_sites(self):
        """Start test websites"""
        print("Starting test websites...")
        self.test_sites.run()

    def run_analysis(self, output_format='html', output_file=None, visualize=False):
        """Run analysis and generate reports"""
        print("Running tracking analysis...")

        if not output_file:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f'tracking_analysis_{timestamp}.{output_format}'

        # Generate report
        if output_format == 'html':
            report = self.analysis_engine.generate_report(format='html')
            with open(output_file, 'w') as f:
                f.write(report)
        else:
            self.analysis_engine.export_data(
                format=output_format, filepath=output_file)

        print(f"Analysis exported to: {output_file}")

        if visualize:
            self.analysis_engine.visualize_tracking_network()

    def cleanup(self):
        """Cleanup resources"""
        print("Cleaning up resources...")
        for monitor in self.monitors.values():
            monitor.cleanup()


def main():
    parser = argparse.ArgumentParser(description='Web Tracking Research Suite')
    parser.add_argument('--port', type=int, default=8000,
                        help='Base port for test sites')
    parser.add_argument('--duration', type=int, default=300,
                        help='Duration to run the test in seconds')
    parser.add_argument('--format', choices=['html', 'json', 'csv'],
                        default='html', help='Output format for analysis')
    parser.add_argument('--output', help='Output file path')
    parser.add_argument('--visualize', action='store_true',
                        help='Visualize tracking network')
    args = parser.parse_args()

    suite = TrackingResearchSuite(base_port=args.port)

    try:
        # Setup and start everything
        suite.setup_environment()

        # Start test sites in a separate thread
        sites_thread = threading.Thread(target=suite.start_test_sites)
        sites_thread.daemon = True
        sites_thread.start()

        # Start monitoring
        suite.start_monitoring()

        print(f"\nTest environment running at http://localhost:{args.port}")
        print(f"Running for {args.duration} seconds...")
        print("Press Ctrl+C to stop early\n")

        # Wait for specified duration
        time.sleep(args.duration)

        # Run analysis
        suite.run_analysis(
            output_format=args.format,
            output_file=args.output,
            visualize=args.visualize
        )

    except KeyboardInterrupt:
        print("\nStopping test environment...")
    finally:
        suite.cleanup()
        print("Test environment shutdown complete.")


if __name__ == "__main__":
    main()
