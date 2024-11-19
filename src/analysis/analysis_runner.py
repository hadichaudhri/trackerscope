from tracking_analysis_engine import TrackingAnalysisEngine
import argparse
from datetime import datetime


def main():
    parser = argparse.ArgumentParser(description='Web Tracking Analysis Tool')
    parser.add_argument('--format', choices=['html', 'json', 'csv'],
                        default='html', help='Output format')
    parser.add_argument('--output', help='Output file path')
    parser.add_argument('--visualize', action='store_true',
                        help='Visualize tracking network')
    parser.add_argument('--detailed', action='store_true',
                        help='Generate detailed analysis')
    args = parser.parse_args()

    # Initialize the analysis engine
    engine = TrackingAnalysisEngine()

    print("Starting analysis...")

    # Generate report
    if args.format == 'html':
        report = engine.generate_report(format='html')
        output_file = args.output or f'tracking_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.html'
        with open(output_file, 'w') as f:
            f.write(report)
        print(f"HTML report generated: {output_file}")

    elif args.format == 'json':
        analysis = engine.analyze_tracking_behavior()
        output_file = args.output or f'tracking_analysis_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        engine.export_data(format='json', filepath=output_file)
        print(f"JSON analysis exported: {output_file}")

    elif args.format == 'csv':
        output_file = args.output or f'tracking_data_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        engine.export_data(format='csv', filepath=output_file)
        print(f"CSV data exported: {output_file}")

    # Generate visualization if requested
    if args.visualize:
        print("Generating tracking network visualization...")
        engine.visualize_tracking_network()

    # Generate detailed analysis if requested
    if args.detailed:
        analysis = engine.analyze_tracking_behavior()
        print("\nDetailed Analysis Summary:")
        print("-" * 50)
        print(
            f"Total Tracking Methods: {len(analysis['summary']['tracking_methods'])}")
        print(
            f"High Risk Activities: {len(analysis['privacy_risks']['high_risk'])}")
        print(
            f"Privacy Risk Score: {analysis['privacy_risks']['risk_score']}/100")
        print("\nTop Recommendations:")
        for rec in analysis['recommendations'][:3]:
            print(f"- [{rec['priority']}] {rec['description']}")


if __name__ == "__main__":
    main()
