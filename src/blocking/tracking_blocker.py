import sqlite3
from datetime import datetime
import json
from urllib.parse import urlparse, parse_qs
from typing import Dict, List, Any, Optional
from seleniumwire import webdriver
from selenium.webdriver.chrome.options import Options
import re
import hashlib
from pathlib import Path


class TrackingBlocker:
    def __init__(self, rules_db="blocker_rules.db", logs_db="blocker_logs.db"):
        self.rules_db = rules_db
        self.logs_db = logs_db
        self.setup_databases()
        self.load_rules()
        self.setup_browser()

    def setup_databases(self):
        """Initialize databases for rules and logging"""
        # Rules database
        conn = sqlite3.connect(self.rules_db)
        c = conn.cursor()

        # Rules table
        c.execute('''
            CREATE TABLE IF NOT EXISTS blocking_rules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                rule_type TEXT,
                pattern TEXT,
                action TEXT,
                description TEXT,
                priority INTEGER,
                enabled INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Rule categories table
        c.execute('''
            CREATE TABLE IF NOT EXISTS rule_categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category TEXT,
                rule_id INTEGER,
                FOREIGN KEY (rule_id) REFERENCES blocking_rules (id)
            )
        ''')

        # Logs database
        conn_logs = sqlite3.connect(self.logs_db)
        c_logs = conn_logs.cursor()

        c_logs.execute('''
            CREATE TABLE IF NOT EXISTS blocking_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                rule_id INTEGER,
                action TEXT,
                request_url TEXT,
                request_type TEXT,
                blocked_data TEXT,
                domain TEXT
            )
        ''')

        conn.commit()
        conn.close()
        conn_logs.commit()
        conn_logs.close()

    def load_rules(self):
        """Load blocking rules from database"""
        self.rules = {
            'url': [],
            'cookie': [],
            'storage': [],
            'script': [],
            'fingerprint': []
        }

        conn = sqlite3.connect(self.rules_db)
        c = conn.cursor()

        c.execute(
            'SELECT * FROM blocking_rules WHERE enabled = 1 ORDER BY priority')

        for rule in c.fetchall():
            rule_dict = {
                'id': rule[0],
                'pattern': rule[2],
                'action': rule[3],
                'description': rule[4],
                'priority': rule[5]
            }
            self.rules[rule[1]].append(rule_dict)

        conn.close()

    def setup_browser(self):
        """Initialize browser with blocking capabilities"""
        chrome_options = Options()
        chrome_options.add_argument('--headless')

        # Custom selenium-wire options for request interception
        seleniumwire_options = {
            'disable_encoding': True  # Handle response bodies without encoding
        }

        self.driver = webdriver.Chrome(
            options=chrome_options,
            seleniumwire_options=seleniumwire_options
        )

        # Set up request/response interceptors
        self.driver.request_interceptor = self._intercept_request
        self.driver.response_interceptor = self._intercept_response

    def add_rule(self, rule_type: str, pattern: str, action: str,
                 description: str, priority: int = 1) -> int:
        """Add a new blocking rule"""
        conn = sqlite3.connect(self.rules_db)
        c = conn.cursor()

        c.execute('''
            INSERT INTO blocking_rules
            (rule_type, pattern, action, description, priority)
            VALUES (?, ?, ?, ?, ?)
        ''', (rule_type, pattern, action, description, priority))

        rule_id = c.lastrowid
        conn.commit()
        conn.close()

        # Reload rules
        self.load_rules()

        return rule_id

    def _intercept_request(self, request):
        """Intercept and possibly block outgoing requests"""
        # Check URL rules
        for rule in self.rules['url']:
            if re.search(rule['pattern'], request.url):
                if rule['action'] == 'block':
                    self._log_blocking(rule['id'], 'block', request.url, 'url')
                    request.abort()
                    return
                elif rule['action'] == 'modify':
                    self._modify_request(request, rule)

        # Check for fingerprinting attempts
        if self._detect_fingerprinting(request):
            self._log_blocking(None, 'block', request.url, 'fingerprint')
            request.abort()
            return

    def _intercept_response(self, request, response):
        """Intercept and modify responses"""
        if response:
            # Check for tracking scripts
            for rule in self.rules['script']:
                if re.search(rule['pattern'], response.body.decode('utf-8', 'ignore')):
                    if rule['action'] == 'block':
                        response.body = b''  # Empty response
                    elif rule['action'] == 'modify':
                        response.body = self._modify_script(
                            response.body, rule)

                    self._log_blocking(
                        rule['id'], rule['action'], request.url, 'script')

    def _modify_request(self, request, rule: Dict[str, Any]):
        """Modify request according to rule"""
        # Strip tracking parameters
        if 'strip_params' in rule['pattern']:
            url_parts = list(urlparse(request.url))
            query = parse_qs(url_parts[4], keep_blank_values=True)

            # Remove tracking parameters
            tracking_params = [
                'utm_source', 'utm_medium', 'utm_campaign',
                'fbclid', 'gclid', '_ga', 'ref'
            ]

            for param in tracking_params:
                query.pop(param, None)

            url_parts[4] = '&'.join(f"{k}={v[0]}" for k, v in query.items())
            request.url = urlparse.urlunparse(url_parts)

    def _modify_script(self, script_body: bytes, rule: Dict[str, Any]) -> bytes:
        """Modify script content according to rule"""
        script_text = script_body.decode('utf-8', 'ignore')

        # Replace fingerprinting functions
        if 'fingerprint' in rule['pattern']:
            replacements = {
                'canvas.toDataURL': 'function() { return ""; }',
                'navigator.userAgent': '"Mozilla/5.0"',
                'navigator.plugins': '[]',
                'navigator.vendorSub': '""'
            }

            for old, new in replacements.items():
                script_text = script_text.replace(old, new)

        return script_text.encode('utf-8')

    def _detect_fingerprinting(self, request) -> bool:
        """Detect potential fingerprinting attempts"""
        fingerprinting_patterns = [
            r'canvas\.toDataURL',
            r'navigator\.userAgent',
            r'navigator\.plugins',
            r'navigator\.platform',
            r'navigator\.language',
            r'screen\.width',
            r'screen\.height',
            r'window\.innerWidth',
            r'window\.innerHeight'
        ]

        request_body = request.body or b''
        request_text = request_body.decode('utf-8', 'ignore')

        return any(re.search(pattern, request_text) for pattern in fingerprinting_patterns)

    def _log_blocking(self, rule_id: Optional[int], action: str,
                      url: str, request_type: str):
        """Log blocking actions"""
        conn = sqlite3.connect(self.logs_db)
        c = conn.cursor()

        c.execute('''
            INSERT INTO blocking_logs
            (rule_id, action, request_url, request_type, domain)
            VALUES (?, ?, ?, ?, ?)
        ''', (rule_id, action, url, request_type, urlparse(url).netloc))

        conn.commit()
        conn.close()

    def inject_blocking_scripts(self):
        """Inject blocking scripts into the page"""
        blocking_script = """
        (function() {
            // Protect against fingerprinting
            const protectFingerprinting = {
                // Canvas protection
                protectCanvas: function() {
                    const origGetContext = HTMLCanvasElement.prototype.getContext;
                    HTMLCanvasElement.prototype.getContext = function(type) {
                        const context = origGetContext.apply(this, arguments);
                        if (type === '2d') {
                            const origGetImageData = context.getImageData;
                            context.getImageData = function() {
                                return origGetImageData.apply(this, [0,0,0,0]);
                            };
                        }
                        return context;
                    };
                },

                // Navigator protection
                protectNavigator: function() {
                    Object.defineProperty(navigator, 'userAgent', {
                        get: function() { return 'Mozilla/5.0'; }
                    });
                    Object.defineProperty(navigator, 'plugins', {
                        get: function() { return []; }
                    });
                },

                // Storage protection
                protectStorage: function() {
                    const origSetItem = Storage.prototype.setItem;
                    Storage.prototype.setItem = function(key, value) {
                        if (key.match(/(track|fingerprint|analytics)/i)) {
                            console.log('Blocked storage:', key);
                            return;
                        }
                        return origSetItem.apply(this, arguments);
                    };
                }
            };

            // Apply protections
            protectFingerprinting.protectCanvas();
            protectFingerprinting.protectNavigator();
            protectFingerprinting.protectStorage();

            // Block known tracking endpoints
            const originalFetch = window.fetch;
            window.fetch = function(url, options) {
                if (url.match(/(analytics|tracking|beacon)/i)) {
                    console.log('Blocked fetch:', url);
                    return Promise.reject('Blocked by tracking protection');
                }
                return originalFetch.apply(this, arguments);
            };

            // Block tracking cookies
            Object.defineProperty(document, 'cookie', {
                get: function() {
                    return '';
                },
                set: function(value) {
                    if (value.match(/(track|analytics|_ga|_gid)/i)) {
                        console.log('Blocked cookie:', value);
                        return '';
                    }
                    return value;
                }
            });
        })();
        """

        self.driver.execute_script(blocking_script)

    def generate_report(self) -> Dict[str, Any]:
        """Generate blocking report"""
        conn = sqlite3.connect(self.logs_db)
        c = conn.cursor()

        report = {
            'total_blocks': 0,
            'blocks_by_type': {},
            'top_blocked_domains': [],
            'blocking_rules': {
                'active': len([r for rt in self.rules.values() for r in rt]),
                'by_type': {rt: len(rules) for rt, rules in self.rules.items()}
            }
        }

        # Get blocking statistics
        c.execute('''
            SELECT request_type, COUNT(*) as count
            FROM blocking_logs
            GROUP BY request_type
        ''')
        report['blocks_by_type'] = dict(c.fetchall())

        # Get top blocked domains
        c.execute('''
            SELECT domain, COUNT(*) as count
            FROM blocking_logs
            GROUP BY domain
            ORDER BY count DESC
            LIMIT 10
        ''')
        report['top_blocked_domains'] = c.fetchall()

        # Calculate total blocks
        report['total_blocks'] = sum(report['blocks_by_type'].values())

        conn.close()
        return report

    def cleanup(self):
        """Clean up resources"""
        if self.driver:
            self.driver.quit()
