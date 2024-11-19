import sqlite3
from datetime import datetime
import json
from seleniumwire import webdriver
from selenium.webdriver.chrome.options import Options


class JavaScriptMonitor:
    def __init__(self, db_path="javascript_monitor.db"):
        self.db_path = db_path
        self.setup_database()
        self.setup_browser()

    def setup_database(self):
        """Initialize database for JavaScript activity tracking"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        c.execute('''
            CREATE TABLE IF NOT EXISTS js_activities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TIMESTAMP,
                script_url TEXT,
                function_name TEXT,
                arguments TEXT,
                stack_trace TEXT,
                accessed_data TEXT,
                is_suspicious INTEGER
            )
        ''')

        c.execute('''
            CREATE TABLE IF NOT EXISTS script_sources (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT,
                content TEXT,
                hash TEXT,
                first_seen TIMESTAMP,
                last_seen TIMESTAMP,
                classification TEXT
            )
        ''')

        conn.commit()
        conn.close()

    def setup_browser(self):
        """Initialize browser with JavaScript monitoring capabilities"""
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        self.driver = webdriver.Chrome(options=chrome_options)

    def inject_monitoring_code(self):
        """Inject JavaScript code to monitor API usage"""
        monitoring_code = """
        (function() {
            // Monitor DOM Storage Access
            const storageHandler = {
                get: function(target, prop) {
                    window.dispatchEvent(new CustomEvent('storageAccess', {
                        detail: {
                            type: 'get',
                            storage: target.constructor.name,
                            key: prop,
                            stack: new Error().stack
                        }
                    }));
                    return target[prop];
                },
                set: function(target, prop, value) {
                    window.dispatchEvent(new CustomEvent('storageAccess', {
                        detail: {
                            type: 'set',
                            storage: target.constructor.name,
                            key: prop,
                            value: value,
                            stack: new Error().stack
                        }
                    }));
                    target[prop] = value;
                    return true;
                }
            };

            // Proxy localStorage and sessionStorage
            window.localStorage = new Proxy(window.localStorage, storageHandler);
            window.sessionStorage = new Proxy(window.sessionStorage, storageHandler);

            // Monitor XMLHttpRequest
            const originalXHR = window.XMLHttpRequest;
            window.XMLHttpRequest = function() {
                const xhr = new originalXHR();
                const original = {
                    open: xhr.open,
                    send: xhr.send
                };

                xhr.open = function() {
                    window.dispatchEvent(new CustomEvent('xhrCall', {
                        detail: {
                            type: 'open',
                            arguments: arguments,
                            stack: new Error().stack
                        }
                    }));
                    return original.open.apply(xhr, arguments);
                };

                xhr.send = function() {
                    window.dispatchEvent(new CustomEvent('xhrCall', {
                        detail: {
                            type: 'send',
                            arguments: arguments,
                            stack: new Error().stack
                        }
                    }));
                    return original.send.apply(xhr, arguments);
                };

                return xhr;
            };

            // Monitor Fetch API
            const originalFetch = window.fetch;
            window.fetch = function() {
                window.dispatchEvent(new CustomEvent('fetchCall', {
                    detail: {
                        arguments: arguments,
                        stack: new Error().stack
                    }
                }));
                return originalFetch.apply(this, arguments);
            };

            // Monitor Canvas API for fingerprinting
            const originalGetImageData = CanvasRenderingContext2D.prototype.getImageData;
            CanvasRenderingContext2D.prototype.getImageData = function() {
                window.dispatchEvent(new CustomEvent('canvasCall', {
                    detail: {
                        method: 'getImageData',
                        arguments: arguments,
                        stack: new Error().stack
                    }
                }));
                return originalGetImageData.apply(this, arguments);
            };
        })();
        """
        self.driver.execute_script(monitoring_code)

    def monitor_script_execution(self, url):
        """Start monitoring JavaScript execution on a page"""
        try:
            self.driver.get(url)
            self.inject_monitoring_code()
            self._setup_event_listeners()
        except Exception as e:
            print(f"Error monitoring JavaScript execution: {str(e)}")

    def _setup_event_listeners(self):
        """Set up listeners for monitored JavaScript events"""
        js_code = """
        window.addEventListener('storageAccess', function(e) {
            // Handle storage access events
            console.log('Storage access:', JSON.stringify(e.detail));
        });

        window.addEventListener('xhrCall', function(e) {
            // Handle XHR calls
            console.log('XHR call:', JSON.stringify(e.detail));
        });

        window.addEventListener('fetchCall', function(e) {
            // Handle fetch calls
            console.log('Fetch call:', JSON.stringify(e.detail));
        });

        window.addEventListener('canvasCall', function(e) {
            // Handle canvas API calls
            console.log('Canvas call:', JSON.stringify(e.detail));
        });
        """
        self.driver.execute_script(js_code)

    def analyze_script_behavior(self):
        """Analyze collected JavaScript behavior data"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        # Analyze suspicious patterns
        c.execute('''
            SELECT
                script_url,
                COUNT(*) as activity_count,
                GROUP_CONCAT(DISTINCT function_name) as functions_used
            FROM js_activities
            WHERE is_suspicious = 1
            GROUP BY script_url
            ORDER BY activity_count DESC
        ''')

        suspicious_activities = c.fetchall()

        # Analyze script sources
        c.execute('''
            SELECT url, classification, COUNT(*) as occurrence_count
            FROM script_sources
            GROUP BY url, classification
        ''')

        script_analysis = c.fetchall()

        conn.close()

        return {
            'suspicious_activities': suspicious_activities,
            'script_analysis': script_analysis
        }

    def cleanup(self):
        """Clean up resources"""
        if self.driver:
            self.driver.quit()
