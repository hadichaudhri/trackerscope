from typing import Dict, List, Any
import json
import pandas as pd
from datetime import datetime
import logging
from pathlib import Path


class ExperimentRunner:
    def __init__(self, output_dir: str = "experiment_results"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.setup_logging()

    def setup_logging(self):
        """Setup logging for experiment runs"""
        logging.basicConfig(
            filename=self.output_dir / 'experiment.log',
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )

    def run_experiment(self, config: Dict[str, Any]):
        """Run a complete tracking experiment"""
        experiment_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        logging.info(f"Starting experiment {experiment_id}")

        results = {
            'experiment_id': experiment_id,
            'config': config,
            'results': {},
            'metrics': {}
        }

        try:
            # Initialize components
            test_sites = TrackingTestSites(
                port_start=config.get('base_port', 8000))
            blocker = TrackingBlocker()
            monitors = {
                'cookie': CookieMonitor(),
                'storage': StorageMonitor(),
                'network': NetworkMonitor(),
                'javascript': JavaScriptMonitor()
            }
            analyzer = TrackingAnalysisEngine()

            # Run test websites
            test_sites.run()

            # Configure blocking rules if specified
            if config.get('blocking_enabled', False):
                self._setup_blocking_rules(
                    blocker, config.get('blocking_rules', []))

            # Start monitoring
            for monitor in monitors.values():
                monitor.start_monitoring(
                    f"http://localhost:{config['base_port']}")

            # Run test scenarios
            for scenario in config['scenarios']:
                scenario_results = self._run_scenario(
                    scenario,
                    monitors,
                    blocker if config.get('blocking_enabled') else None
                )
                results['results'][scenario['name']] = scenario_results

            # Analyze results
            results['metrics'] = analyzer.analyze_tracking_behavior()

            # Generate reports
            self._generate_reports(results)

        except Exception as e:
            logging.error(f"Experiment failed: {str(e)}")
            results['error'] = str(e)
        finally:
            # Cleanup
            for monitor in monitors.values():
                monitor.cleanup()
            if config.get('blocking_enabled'):
                blocker.cleanup()

        return results

    def _run_scenario(self,
                      scenario: Dict[str, Any],
                      monitors: Dict[str, Any],
                      blocker: Any = None) -> Dict[str, Any]:
        """Run a specific test scenario"""
        logging.info(f"Running scenario: {scenario['name']}")

        results = {
            'tracking_detected': [],
            'blocking_actions': [],
            'metrics': {}
        }

        # Execute scenario steps
        for step in scenario['steps']:
            step_result = self._execute_step(step, monitors, blocker)
            results['tracking_detected'].extend(step_result['tracking'])
            if blocker:
                results['blocking_actions'].extend(step_result['blocking'])

        # Calculate metrics
        results['metrics'] = self._calculate_metrics(results)

        return results

    def _generate_reports(self, results: Dict[str, Any]):
        """Generate comprehensive reports from experiment results"""
        experiment_dir = self.output_dir / results['experiment_id']
        experiment_dir.mkdir(exist_ok=True)

        # Save raw results
        with open(experiment_dir / 'raw_results.json', 'w') as f:
            json.dump(results, f, indent=2)

        # Generate CSV reports
        metrics_df = pd.DataFrame(results['metrics'])
        metrics_df.to_csv(experiment_dir / 'metrics.csv')

        # Generate summary report
        self._generate_summary_report(results, experiment_dir)

    def _generate_summary_report(self, results: Dict[str, Any], output_dir: Path):
        """Generate a human-readable summary report"""
        summary = []
        summary.append("Web Tracking Research - Experiment Summary")
        summary.append("=" * 50)
        summary.append(f"Experiment ID: {results['experiment_id']}")
        summary.append(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        summary.append("\nScenario Results:")

        for scenario_name, scenario_results in results['results'].items():
            summary.append(f"\n{scenario_name}:")
            summary.append("-" * len(scenario_name))
            summary.append(
                f"Tracking Methods Detected: {len(scenario_results['tracking_detected'])}")
            if scenario_results.get('blocking_actions'):
                summary.append(
                    f"Blocking Actions: {len(scenario_results['blocking_actions'])}")

            metrics = scenario_results['metrics']
            summary.append("\nKey Metrics:")
            for metric, value in metrics.items():
                summary.append(f"- {metric}: {value}")

        with open(output_dir / 'summary_report.txt', 'w') as f:
            f.write('\n'.join(summary))
