from flask import Flask, request, make_response, render_template_string, jsonify
import uuid
import os
import json


class TrackingTestSites:
    def __init__(self, port_start=8000):
        self.port_start = port_start
        self.apps = {}
        self.setup_sites()

    def setup_sites(self):
        """Create different test sites with various tracking implementations"""
        # Main test site
        self.create_main_site()
        # Third-party tracking site
        self.create_third_party_site()
        # Analytics site
        self.create_analytics_site()

    def create_main_site(self):
        app = Flask('main_site')

        @app.route('/')
        def main_home():
            return render_template_string('''
                <!DOCTYPE html>
                <html>
                <head>
                    <title>Test Site - Main</title>
                    <script src="http://localhost:{{third_party_port}}/tracker.js"></script>
                    <script src="http://localhost:{{analytics_port}}/analytics.js"></script>
                </head>
                <body>
                    <h1>Test Site</h1>
                    <div id="content">
                        <p>This is a test page with various tracking implementations.</p>
                        <button onclick="simulateUserAction()">Simulate User Action</button>
                    </div>

                    <script>
                        // First-party cookie implementation
                        function setCookie(name, value, days) {
                            let expires = "";
                            if (days) {
                                const date = new Date();
                                date.setTime(date.getTime() + (days * 24 * 60 * 60 * 1000));
                                expires = "; expires=" + date.toUTCString();
                            }
                            document.cookie = name + "=" + value + expires + "; path=/";
                        }

                        // Set initial first-party cookie
                        if (!document.cookie.includes('visitor_id')) {
                            setCookie('visitor_id', 'fp_' + Math.random().toString(36).substr(2, 9), 30);
                        }

                        // Local Storage implementation
                        function setupLocalStorage() {
                            if (!localStorage.getItem('user_profile')) {
                                localStorage.setItem('user_profile', JSON.stringify({
                                    id: 'ls_' + Math.random().toString(36).substr(2, 9),
                                    firstVisit: new Date().toISOString(),
                                    visits: 1
                                }));
                            } else {
                                let profile = JSON.parse(localStorage.getItem('user_profile'));
                                profile.visits += 1;
                                localStorage.setItem('user_profile', JSON.stringify(profile));
                            }
                        }

                        // Canvas fingerprinting implementation
                        function generateCanvasFingerprint() {
                            const canvas = document.createElement('canvas');
                            const ctx = canvas.getContext('2d');
                            ctx.textBaseline = "top";
                            ctx.font = "14px 'Arial'";
                            ctx.textBaseline = "alphabetic";
                            ctx.fillStyle = "#f60";
                            ctx.fillRect(125,1,62,20);
                            ctx.fillStyle = "#069";
                            ctx.fillText("Hello, world!", 2, 15);
                            ctx.fillStyle = "rgba(102, 204, 0, 0.7)";
                            ctx.fillText("Hello, world!", 4, 17);

                            return canvas.toDataURL();
                        }

                        // Monitor and simulate user behavior
                        function simulateUserAction() {
                            // Update local storage
                            let profile = JSON.parse(localStorage.getItem('user_profile'));
                            profile.lastAction = new Date().toISOString();
                            localStorage.setItem('user_profile', JSON.stringify(profile));

                            // Send data to analytics
                            fetch('http://localhost:{{analytics_port}}/event', {
                                method: 'POST',
                                headers: {
                                    'Content-Type': 'application/json',
                                },
                                body: JSON.stringify({
                                    event: 'button_click',
                                    timestamp: new Date().toISOString(),
                                    fingerprint: generateCanvasFingerprint()
                                })
                            });
                        }

                        // Initialize tracking
                        setupLocalStorage();
                    </script>
                </body>
                </html>
            ''', third_party_port=self.port_start + 1, analytics_port=self.port_start + 2)

        self.apps['main'] = app

    def create_third_party_site(self):
        app = Flask('third_party_site')

        @app.route('/tracker.js')
        def tracker_js():
            return '''
                // Third-party tracking implementation
                (function() {
                    function generateTrackingId() {
                        return 'tp_' + Math.random().toString(36).substr(2, 9);
                    }

                    function setThirdPartyCookie() {
                        document.cookie = "tp_tracker=" + generateTrackingId() + "; path=/; max-age=31536000";
                    }

                    // Cookie syncing implementation
                    function syncCookies() {
                        const img = new Image();
                        img.src = 'http://localhost:''' + str(self.port_start + 1) + '''/sync?' +
                                'first_party_id=' + encodeURIComponent(document.cookie) +
                                '&referrer=' + encodeURIComponent(document.referrer);
                    }

                    // Initialize tracking
                    setThirdPartyCookie();
                    syncCookies();

                    // Set up respawning mechanism
                    window.addEventListener('storage', function(e) {
                        if (e.key === 'tp_tracker_backup') {
                            setThirdPartyCookie();
                        }
                    });

                    // Backup tracking ID to localStorage
                    localStorage.setItem('tp_tracker_backup', document.cookie);
                })();
            '''

        @app.route('/sync')
        def sync():
            # Simulate cookie syncing
            response = make_response('pixel.gif')
            response.headers['Content-Type'] = 'image/gif'
            # Store the mapping between first-party and third-party IDs
            return response

        self.apps['third_party'] = app

    def create_analytics_site(self):
        app = Flask('analytics_site')
        stored_data = []

        @app.route('/analytics.js')
        def analytics_js():
            return '''
                // Analytics implementation
                (function() {
                    function collectBrowserData() {
                        return {
                            userAgent: navigator.userAgent,
                            language: navigator.language,
                            screenResolution: window.screen.width + 'x' + window.screen.height,
                            timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
                            plugins: Array.from(navigator.plugins).map(p => p.name)
                        };
                    }

                    function generateFingerprint() {
                        const browserData = collectBrowserData();
                        return btoa(JSON.stringify(browserData));
                    }

                    // Initialize analytics
                    const analyticsId = generateFingerprint();
                    localStorage.setItem('analytics_id', analyticsId);

                    // Send initial pageview
                    fetch('http://localhost:''' + str(self.port_start + 2) + '''/event', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({
                            type: 'pageview',
                            fingerprint: analyticsId,
                            url: window.location.href,
                            timestamp: new Date().toISOString(),
                            browserData: collectBrowserData()
                        })
                    });
                })();
            '''

        @app.route('/event', methods=['POST'])
        def track_event():
            # Store analytics data
            data = request.get_json()
            stored_data.append(data)
            return jsonify({'status': 'success'})

        self.apps['analytics'] = app

    def run(self):
        """Run all test sites on different ports"""
        from threading import Thread

        def run_app(app, port):
            app.run(port=port)

        threads = []
        for i, (name, app) in enumerate(self.apps.items()):
            port = self.port_start + i
            thread = Thread(target=run_app, args=(app, port))
            thread.daemon = True
            thread.start()
            threads.append(thread)
            print(f"Started {name} site on port {port}")
