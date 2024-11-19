import sqlite3
from datetime import datetime
import json
from seleniumwire import webdriver
from selenium.webdriver.chrome.options import Options


class StorageMonitor:
    def __init__(self, db_path="storage_monitor.db"):
        self.db_path = db_path
        self.setup_database()
        self.setup_browser()

    def setup_database(self):
        """Initialize SQLite database for storage tracking"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        # Table for LocalStorage monitoring
        c.execute('''
            CREATE TABLE IF NOT EXISTS local_storage (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                domain TEXT,
                key TEXT,
                value TEXT,
                timestamp TIMESTAMP,
                action TEXT
            )
        ''')

        # Table for SessionStorage monitoring
        c.execute('''
            CREATE TABLE IF NOT EXISTS session_storage (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                domain TEXT,
                key TEXT,
                value TEXT,
                timestamp TIMESTAMP,
                action TEXT
            )
        ''')

        # Table for ETag tracking
        c.execute('''
            CREATE TABLE IF NOT EXISTS etags (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT,
                etag TEXT,
                timestamp TIMESTAMP,
                response_headers TEXT
            )
        ''')

        conn.commit()
        conn.close()

    def setup_browser(self):
        """Initialize browser with storage monitoring capabilities"""
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        self.driver = webdriver.Chrome(options=chrome_options)

    def monitor_local_storage(self, url):
        """Monitor LocalStorage activities"""
        try:
            self.driver.get(url)
            js_code = """
            (function() {
                let originalSetItem = Storage.prototype.setItem;
                let originalGetItem = Storage.prototype.getItem;
                let originalRemoveItem = Storage.prototype.removeItem;

                Storage.prototype.setItem = function(key, value) {
                    window.dispatchEvent(new CustomEvent('storageModified', {
                        detail: {
                            type: 'localStorage',
                            action: 'set',
                            key: key,
                            value: value
                        }
                    }));
                    originalSetItem.call(this, key, value);
                };

                // Add similar monitoring for getItem and removeItem
            })();
            """
            self.driver.execute_script(js_code)

            # Set up event listener for storage events
            self._setup_storage_listener()

        except Exception as e:
            print(f"Error monitoring localStorage for {url}: {str(e)}")

    def monitor_etags(self):
        """Monitor ETag headers in responses"""
        def response_interceptor(request, response):
            if response and 'etag' in response.headers:
                self._store_etag(
                    request.url,
                    response.headers['etag'],
                    json.dumps(dict(response.headers))
                )

        self.driver.response_interceptor = response_interceptor

    def _store_etag(self, url, etag, headers):
        """Store ETag information in database"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        c.execute('''
            INSERT INTO etags (url, etag, timestamp, response_headers)
            VALUES (?, ?, ?, ?)
        ''', (url, etag, datetime.now(), headers))

        conn.commit()
        conn.close()

    def detect_fingerprinting(self):
        """Detect potential fingerprinting attempts"""
        js_code = """
        (function() {
            // Monitor Canvas API usage
            let originalGetImageData = CanvasRenderingContext2D.prototype.getImageData;
            CanvasRenderingContext2D.prototype.getImageData = function() {
                window.dispatchEvent(new CustomEvent('fingerprintAttempt', {
                    detail: {
                        type: 'canvas',
                        method: 'getImageData'
                    }
                }));
                return originalGetImageData.apply(this, arguments);
            };

            // Monitor WebGL API usage
            // Add similar monitoring for WebGL contexts
        })();
        """
        self.driver.execute_script(js_code)

    def analyze_storage_patterns(self):
        """Analyze storage usage patterns to detect tracking behavior"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        # Analyze LocalStorage patterns
        c.execute('''
            SELECT domain, key, COUNT(*) as changes
            FROM local_storage
            GROUP BY domain, key
            HAVING changes > 1
            ORDER BY changes DESC
        ''')

        frequent_changes = c.fetchall()

        # Analyze ETag patterns
        c.execute('''
            SELECT url, COUNT(DISTINCT etag) as unique_etags
            FROM etags
            GROUP BY url
            HAVING unique_etags > 1
        ''')

        suspicious_etags = c.fetchall()

        conn.close()

        return {
            'frequent_storage_changes': frequent_changes,
            'suspicious_etag_patterns': suspicious_etags
        }

    def cleanup(self):
        """Clean up resources"""
        if self.driver:
            self.driver.quit()
