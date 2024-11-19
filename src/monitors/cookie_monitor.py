import sqlite3
from datetime import datetime
import json
from urllib.parse import urlparse
from seleniumwire import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options


class CookieMonitor:
    def __init__(self, db_path="cookie_monitor.db"):
        self.db_path = db_path
        self.setup_database()
        self.setup_browser()

    def setup_database(self):
        """Initialize SQLite database for cookie tracking"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('''
            CREATE TABLE IF NOT EXISTS cookies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                domain TEXT,
                name TEXT,
                value TEXT,
                path TEXT,
                expires TIMESTAMP,
                secure INTEGER,
                http_only INTEGER,
                same_site TEXT,
                source_url TEXT,
                creation_time TIMESTAMP,
                last_accessed TIMESTAMP,
                is_session INTEGER,
                is_deleted INTEGER DEFAULT 0
            )
        ''')
        conn.commit()
        conn.close()

    def setup_browser(self):
        """Initialize Selenium WebDriver with wire for request interception"""
        chrome_options = Options()
        chrome_options.add_argument('--headless')  # Run in headless mode
        self.driver = webdriver.Chrome(options=chrome_options)

    def start_monitoring(self, url):
        """Start monitoring cookies for a given URL"""
        try:
            self.driver.get(url)
            self._capture_initial_cookies()
            self._setup_cookie_listeners()
        except Exception as e:
            print(f"Error monitoring URL {url}: {str(e)}")

    def _capture_initial_cookies(self):
        """Capture all existing cookies when monitoring starts"""
        cookies = self.driver.get_cookies()
        for cookie in cookies:
            self._store_cookie(cookie)

    def _setup_cookie_listeners(self):
        """Setup JavaScript listeners for cookie changes"""
        js_code = """
        (function() {
            let originalSetter = Object.getOwnPropertyDescriptor(Document.prototype, 'cookie').set;
            let originalGetter = Object.getOwnPropertyDescriptor(Document.prototype, 'cookie').get;

            Object.defineProperty(document, 'cookie', {
                set: function(val) {
                    window.dispatchEvent(new CustomEvent('cookieChanged', {
                        detail: { value: val, type: 'set' }
                    }));
                    return originalSetter.call(document, val);
                },
                get: function() {
                    let value = originalGetter.call(document);
                    window.dispatchEvent(new CustomEvent('cookieRead', {
                        detail: { value: value, type: 'get' }
                    }));
                    return value;
                }
            });
        })();
        """
        self.driver.execute_script(js_code)

    def _store_cookie(self, cookie_data):
        """Store cookie data in SQLite database"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        c.execute('''
            INSERT INTO cookies (
                domain, name, value, path, expires, secure,
                http_only, source_url, creation_time, is_session
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            cookie_data.get('domain'),
            cookie_data.get('name'),
            cookie_data.get('value'),
            cookie_data.get('path'),
            cookie_data.get('expiry'),
            cookie_data.get('secure', False),
            cookie_data.get('httpOnly', False),
            self.driver.current_url,
            datetime.now(),
            cookie_data.get('expiry') is None
        ))

        conn.commit()
        conn.close()

    def detect_respawning(self, cookie_name):
        """Detect if a cookie is being respawned after deletion"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        c.execute('''
            SELECT COUNT(*) FROM cookies
            WHERE name = ? AND is_deleted = 1
            AND creation_time > (
                SELECT creation_time FROM cookies
                WHERE name = ? AND is_deleted = 1
                ORDER BY creation_time DESC LIMIT 1
            )
        ''', (cookie_name, cookie_name))

        respawn_count = c.fetchone()[0]
        conn.close()
        return respawn_count > 0

    def generate_report(self):
        """Generate a report of cookie activity"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        report = {
            'total_cookies': 0,
            'respawned_cookies': 0,
            'third_party_cookies': 0,
            'secure_cookies': 0,
            'session_cookies': 0
        }

        c.execute('SELECT COUNT(*) FROM cookies')
        report['total_cookies'] = c.fetchone()[0]

        # Add more detailed reporting queries here

        conn.close()
        return report

    def cleanup(self):
        """Clean up resources"""
        if self.driver:
            self.driver.quit()
