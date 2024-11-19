import sqlite3
from datetime import datetime, timedelta
import json
import pandas as pd
import numpy as np
from urllib.parse import urlparse
import networkx as nx
from collections import defaultdict
import matplotlib.pyplot as plt
from typing import Dict, List, Any, Tuple

class TrackingAnalysisEngine:
    def __init__(self,
                 cookie_db="cookie_monitor.db",
                 storage_db="storage_monitor.db",
                 network_db="network_monitor.db",
                 js_db="javascript_monitor.db"):
        """Initialize the analysis engine with paths to monitor databases"""
        self.databases = {
            'cookie': cookie_db,
            'storage': storage_db,
            'network': network_db,
            'javascript': js_db
        }
        self.tracking_patterns = self._load_tracking_patterns()

    def _load_tracking_patterns(self) -> Dict[str, List[str]]:
        """Load known tracking patterns and identifiers"""
        return {
            'cookie_names': [
                'uid', 'guid', '_ga', 'visitor_id', 'trackingid',
                'userid', 'sessionid', '_fbp', '_gid', 'id'
            ],
            'storage_keys': [
                'localStorage', 'sessionStorage', 'userData',
                'fingerprint', 'device', 'canvas'
            ],
            'request_params': [
                'uid', 'guid', 'tracking', 'visitor', 'analytics',
                'fingerprint', 'canvas', 'device'
            ],
            'suspicious_apis': [
                'getImageData', 'toDataURL', 'getClientRects',
                'getFloatFrequencyData', 'enumerateDevices'
            ]
        }

    def analyze_tracking_behavior(self) -> Dict[str, Any]:
        """Perform comprehensive analysis of tracking behavior"""
        analysis = {
            'summary': self._generate_summary(),
            'cookie_analysis': self._analyze_cookies(),
            'storage_analysis': self._analyze_storage(),
            'network_analysis': self._analyze_network(),
            'javascript_analysis': self._analyze_javascript(),
            'cross_domain_tracking': self._analyze_cross_domain_tracking(),
            'fingerprinting_detection': self._detect_fingerprinting(),
            'privacy_risks': self._assess_privacy_risks(),
            'recommendations': self._generate_recommendations()
        }
        return analysis

    def _generate_summary(self) -> Dict[str, Any]:
        """Generate high-level summary of tracking activities"""
        summary = {
            'timestamp': datetime.now(),
            'total_trackers': 0,
            'tracking_methods': defaultdict(int),
            'high_risk_activities': [],
            'domains_involved': set()
        }

        # Analyze cookies
        conn = sqlite3.connect(self.databases['cookie'])
        c = conn.cursor()

        c.execute('''
            SELECT COUNT(*), COUNT(DISTINCT domain)
            FROM cookies
            WHERE name LIKE '%track%'
                OR name LIKE '%id%'
                OR name IN (''' + ','.join(['?']*len(self.tracking_patterns['cookie_names'])) + ')',
            self.tracking_patterns['cookie_names']
        )
        tracking_cookies, cookie_domains = c.fetchone()
        summary['tracking_methods']['cookies'] = tracking_cookies
        summary['domains_involved'].update(self._get_cookie_domains())

        # Similar analysis for other tracking methods
        summary.update(self._analyze_other_tracking_methods())

        return summary

    def _analyze_cookies(self) -> Dict[str, Any]:
        """Analyze cookie-based tracking patterns"""
        conn = sqlite3.connect(self.databases['cookie'])
        c = conn.cursor()

        analysis = {
            'tracking_cookies': [],
            'respawned_cookies': [],
            'synced_cookies': [],
            'persistent_cookies': []
        }

        # Identify tracking cookies
        c.execute('''
            SELECT name, domain, value, creation_time, expires, is_session
            FROM cookies
            WHERE name LIKE '%track%'
                OR name LIKE '%id%'
                OR name IN (''' + ','.join(['?']*len(self.tracking_patterns['cookie_names'])) + ')',
            self.tracking_patterns['cookie_names']
        )

        for row in c.fetchall():
            cookie = {
                'name': row[0],
                'domain': row[1],
                'value': row[2],
                'created': row[3],
                'expires': row[4],
                'is_session': row[5]
            }
            analysis['tracking_cookies'].append(cookie)

        # Detect cookie respawning
        analysis['respawned_cookies'] = self._detect_cookie_respawning(c)

        # Detect cookie syncing
        analysis['synced_cookies'] = self._detect_cookie_syncing(c)

        return analysis

    def _analyze_storage(self) -> Dict[str, Any]:
        """Analyze storage-based tracking"""
        conn = sqlite3.connect(self.databases['storage'])
        c = conn.cursor()

        analysis = {
            'localStorage_tracking': [],
            'sessionStorage_tracking': [],
            'backup_data': [],
            'fingerprinting_storage': []
        }

        # Analyze localStorage usage
        c.execute('''
            SELECT domain, key, value, timestamp
            FROM local_storage
            WHERE key LIKE '%track%'
                OR key LIKE '%id%'
                OR key IN (''' + ','.join(['?']*len(self.tracking_patterns['storage_keys'])) + ')',
            self.tracking_patterns['storage_keys']
        )

        for row in c.fetchall():
            storage_item = {
                'domain': row[0],
                'key': row[1],
                'value': row[2],
                'timestamp': row[3]
            }
            analysis['localStorage_tracking'].append(storage_item)

        # Analyze fingerprinting data in storage
        analysis['fingerprinting_storage'] = self._detect_storage_fingerprinting(c)

        return analysis

    def _analyze_network(self) -> Dict[str, Any]:
        """Analyze network-based tracking"""
        conn = sqlite3.connect(self.databases['network'])
        c = conn.cursor()

        analysis = {
            'tracking_requests': [],
            'data_sharing': [],
            'beacon_usage': [],
            'suspicious_endpoints': []
        }

        # Analyze tracking requests
        c.execute('''
            SELECT url, method, headers, query_params, domain
            FROM requests
            WHERE url LIKE '%track%'
                OR url LIKE '%analytic%'
                OR url LIKE '%beacon%'
        ''')

        for row in c.fetchall():
            request = {
                'url': row[0],
                'method': row[1],
                'headers': json.loads(row[2]),
                'params': json.loads(row[3]),
                'domain': row[4]
            }
            analysis['tracking_requests'].append(request)

        # Analyze beacon usage
        analysis['beacon_usage'] = self._analyze_beacon_requests(c)

        return analysis

    def _analyze_javascript(self) -> Dict[str, Any]:
        """Analyze JavaScript-based tracking"""
        conn = sqlite3.connect(self.databases['javascript'])
        c = conn.cursor()

        analysis = {
            'fingerprinting_attempts': [],
            'suspicious_functions': [],
            'event_listeners': [],
            'data_access_patterns': []
        }

        # Analyze fingerprinting attempts
        c.execute('''
            SELECT script_url, function_name, arguments, timestamp
            FROM js_activities
            WHERE function_name IN (''' + ','.join(['?']*len(self.tracking_patterns['suspicious_apis'])) + ')',
            self.tracking_patterns['suspicious_apis']
        )

        for row in c.fetchall():
            activity = {
                'script': row[0],
                'function': row[1],
                'args': row[2],
                'timestamp': row[3]
            }
            analysis['fingerprinting_attempts'].append(activity)

        return analysis

    def _analyze_cross_domain_tracking(self) -> Dict[str, Any]:
        """Analyze cross-domain tracking patterns"""
        graph = nx.DiGraph()

        # Analyze network connections
        conn = sqlite3.connect(self.databases['network'])
        c = conn.cursor()

        c.execute('''
            SELECT domain, url, headers
            FROM requests
            WHERE third_party = 1
        ''')

        for row in c.fetchall():
            source_domain = row[0]
            target_domain = urlparse(row[1]).netloc
            headers = json.loads(row[2])

            if source_domain and target_domain:
                graph.add_edge(source_domain, target_domain)

        # Analyze tracking flow
        analysis = {
            'tracking_graph': self._serialize_graph(graph),
            'central_trackers': self._identify_central_trackers(graph),
            'tracking_chains': self._identify_tracking_chains(graph)
        }

        return analysis

    def _detect_fingerprinting(self) -> Dict[str, Any]:
        """Detect various fingerprinting techniques"""
        fingerprinting = {
            'canvas_fingerprinting': [],
            'audio_fingerprinting': [],
            'font_fingerprinting': [],
            'behavioral_fingerprinting': []
        }

        # Analyze JavaScript calls
        conn = sqlite3.connect(self.databases['javascript'])
        c = conn.cursor()

        # Canvas fingerprinting
        c.execute('''
            SELECT script_url, timestamp, arguments
            FROM js_activities
            WHERE function_name IN ('getImageData', 'toDataURL')
        ''')

        for row in c.fetchall():
            fingerprinting['canvas_fingerprinting'].append({
                'script': row[0],
                'timestamp': row[1],
                'details': row[2]
            })

        return fingerprinting

    def _assess_privacy_risks(self) -> Dict[str, Any]:
        """Assess privacy risks based on observed tracking behavior"""
        risks = {
            'high_risk': [],
            'medium_risk': [],
            'low_risk': [],
            'risk_score': 0
        }

        # Calculate risk score based on various factors
        risk_score = 0

        # Check for high-risk tracking methods
        if self._has_persistent_fingerprinting():
            risks['high_risk'].append({
                'type': 'persistent_fingerprinting',
                'description': 'Persistent device fingerprinting detected',
                'impact': 'High',
                'mitigation': 'Use anti-fingerprinting tools'
            })
            risk_score += 30

        # Add more risk assessments...

        risks['risk_score'] = min(risk_score, 100)  # Cap at 100
        return risks

    def _generate_recommendations(self) -> List[Dict[str, str]]:
        """Generate privacy recommendations based on analysis"""
        recommendations = []

        # Analyze tracking methods and generate specific recommendations
        if self._has_extensive_tracking():
            recommendations.append({
                'priority': 'High',
                'description': 'Implement comprehensive cookie cleanup',
                'details': 'Regular deletion of tracking cookies recommended',
                'implementation': 'Use browser privacy settings or privacy-focused extensions'
            })

        return recommendations

    def generate_report(self, format='html') -> str:
        """Generate a formatted report of the analysis"""
        analysis = self.analyze_tracking_behavior()

        if format == 'html':
            return self._generate_html_report(analysis)
        elif format == 'json':
            return json.dumps(analysis, indent=2)
        else:
            raise ValueError(f"Unsupported format: {format}")

    def _generate_html_report(self, analysis: Dict[str, Any]) -> str:
        """Generate HTML report from analysis results"""
        html_template = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Web Tracking Analysis Report</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; }
                .section { margin: 20px 0; padding: 10px; border: 1px solid #ccc; }
                .high-risk { color: #d9534f; }
                .medium-risk { color: #f0ad4e; }
                .low-risk { color: #5bc0de; }
            </style>
        </head>
        <body>
            <h1>Web Tracking Analysis Report</h1>
            <div class="section">
                <h2>Summary</h2>
                <p>Total Trackers: {total_trackers}</p>
                <p>Risk Score: {risk_score}/100</p>
            </div>
            <!-- Add more sections -->
        </body>
        </html>
        """

        # Fill in template with analysis data
        return html_template.format(
            total_trackers=analysis['summary']['total_trackers'],
            risk_score=analysis['privacy_risks']['risk_score']
        )

    def visualize_tracking_network(self) -> None:
        """Visualize the tracking network using networkx and matplotlib"""
        analysis = self._analyze_cross_domain_tracking()
        graph = nx.node_link_graph(analysis['tracking_graph'])

        plt.figure(figsize=(12, 8))
        pos = nx.spring_layout(graph)

        # Draw the network
        nx.draw(graph, pos,
                node_color='lightblue',
                node_size=1000,
                with_labels=True,
                font_size=8,
                arrows=True)

        plt.title("Cross-Domain Tracking Network")
        plt.show()

    def export_data(self, format='csv', filepath=None) -> None:
        """Export analysis data in various formats"""
        analysis = self.analyze_tracking_behavior()

        if format == 'csv':
            df = pd.DataFrame(analysis['summary'])
            if filepath:
                df.to_csv(filepath)
            return df
        elif format == 'json':
            if filepath:
                with open(filepath, 'w') as f:
                    json.dump(analysis, f, indent=2)
            return analysis
