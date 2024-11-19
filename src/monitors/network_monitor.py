import sqlite3
from datetime import datetime
import json
from urllib.parse import urlparse, parse_qs
from seleniumwire import webdriver
from selenium.webdriver.chrome.options import Options


class NetworkMonitor:
    def __init__(self, db_path="network_monitor.db"):
        self.db_path = db_path
        self.setup_database()
        self.setup_browser()

    def setup_database(self):
        """Initialize database for network request tracking"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        c.execute('''
            CREATE TABLE IF NOT EXISTS requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT,
                method TEXT,
                headers TEXT,
                query_params TEXT,
                post_data TEXT,
                timestamp TIMESTAMP,
                response_status INTEGER,
                response_headers TEXT,
                domain TEXT,
                third_party INTEGER,
                contains_tracking_data INTEGER
            )
        ''')

        conn.commit()
        conn.close()

    def setup_browser(self):
        """Initialize browser with request interception"""
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        self.driver = webdriver.Chrome(options=chrome_options)

    def start_monitoring(self, base_url):
        """Start monitoring network requests"""
        self.base_domain = urlparse(base_url).netloc

        def request_interceptor(request):
            """Intercept and analyze outgoing requests"""
            try:
                url_parts = urlparse(request.url)
                is_third_party = url_parts.netloc != self.base_domain

                # Store request data
                self._store_request(
                    url=request.url,
                    method=request.method,
                    headers=dict(request.headers),
                    query_params=parse_qs(url_parts.query),
                    post_data=request.body,
                    domain=url_parts.netloc,
                    is_third_party=is_third_party
                )

                # Check for tracking indicators
                if self._contains_tracking_data(request):
                    self._log_tracking_attempt(request)

            except Exception as e:
                print(f"Error intercepting request: {str(e)}")

        self.driver.request_interceptor = request_interceptor

    def _store_request(self, **kwargs):
        """Store request information in database"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        c.execute('''
            INSERT INTO requests (
                url, method, headers, query_params, post_data,
                timestamp, domain, third_party, contains_tracking_data
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            kwargs['url'],
            kwargs['method'],
            json.dumps(kwargs['headers']),
            json.dumps(kwargs['query_params']),
            kwargs.get('post_data'),
            datetime.now(),
            kwargs['domain'],
            kwargs['is_third_party'],
            self._contains_tracking_data(kwargs)
        ))

        conn.commit()
        conn.close()

    def _contains_tracking_data(self, request_data):
        """Check if request contains potential tracking data"""
        tracking_indicators = [
            'id', 'uid', 'guid', 'uuid', 'tracking',
            'analytics', 'visitor', 'client_id'
        ]

        # Check URL parameters
        url_parts = urlparse(request_data['url'])
        params = parse_qs(url_parts.query)

        for param in params:
            if any(indicator in param.lower() for indicator in tracking_indicators):
                return True

        # Check headers
        headers = request_data['headers']
        for header, value in headers.items():
            if any(indicator in header.lower() for indicator in tracking_indicators):
                return True

        return False

    def analyze_cross_domain_patterns(self):
        """Analyze patterns in cross-domain communications"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        # Analyze third-party request patterns
        c.execute('''
            SELECT
                domain,
                COUNT(*) as request_count,
                COUNT(DISTINCT url) as unique_urls,
                SUM(contains_tracking_data) as tracking_requests
            FROM requests
            WHERE third_party = 1
            GROUP BY domain
            ORDER BY request_count DESC
        ''')

        domain_patterns = c.fetchall()

        # Analyze data sharing patterns
        c.execute('''
            SELECT
                r1.domain as source_domain,
                r2.domain as destination_domain,
                COUNT(*) as connection_count
            FROM requests r1
            JOIN requests r2 ON r1.id < r2.id
                AND ABS(JULIANDAY(r2.timestamp) - JULIANDAY(r1.timestamp)) < 1/24.0
            WHERE r1.third_party = 1 AND r2.third_party = 1
            GROUP BY r1.domain, r2.domain
            HAVING connection_count > 1
        ''')

        data_sharing_patterns = c.fetchall()

        conn.close()

        return {
            'domain_patterns': domain_patterns,
            'data_sharing_patterns': data_sharing_patterns
        }

    def detect_cookie_leakage(self):
        """Detect potential cookie data being leaked in requests"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        # Get all cookies from cookie database (assuming it exists)
        c.execute('''
            ATTACH DATABASE 'cookie_monitor.db' AS cookies;

            SELECT DISTINCT r.url, r.domain, r.query_params, c.value
            FROM requests r
            JOIN cookies.cookies c
            WHERE r.query_params LIKE '%' || c.value || '%'
            AND r.third_party = 1
        ''')

        leaked_cookies = c.fetchall()
        conn.close()

        return leaked_cookies

    def generate_report(self):
        """Generate a comprehensive report of network activity"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        report = {
            'total_requests': 0,
            'third_party_requests': 0,
            'tracking_requests': 0,
            'domains_contacted': set(),
            'suspicious_patterns': []
        }

        # Get basic statistics
        c.execute('''
            SELECT
                COUNT(*) as total,
                SUM(third_party) as third_party,
                SUM(contains_tracking_data) as tracking,
                COUNT(DISTINCT domain) as domains
            FROM requests
        ''')

        stats = c.fetchone()
        report.update({
            'total_requests': stats[0],
            'third_party_requests': stats[1],
            'tracking_requests': stats[2],
            'unique_domains': stats[3]
        })

        # Get suspicious patterns
        c.execute('''
            SELECT domain, COUNT(*) as count
            FROM requests
            WHERE contains_tracking_data = 1
            GROUP BY domain
            ORDER BY count DESC
            LIMIT 10
        ''')

        report['top_tracking_domains'] = c.fetchall()

        conn.close()
        return report

    def cleanup(self):
        """Clean up resources"""
        if self.driver:
            self.driver.quit()
