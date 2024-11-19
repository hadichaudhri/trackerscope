import sqlite3
import json
import argparse
from pathlib import Path
from typing import List, Dict


class BlockingRulesManager:
    def __init__(self, rules_db="blocker_rules.db"):
        self.rules_db = rules_db
        self.ensure_database()

    def ensure_database(self):
        """Ensure database exists with correct schema"""
        conn = sqlite3.connect(self.rules_db)
        c = conn.cursor()

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

        conn.commit()
        conn.close()

    def add_default_rules(self):
        """Add default blocking rules"""
        default_rules = [
            # URL rules
            {
                'type': 'url',
                'pattern': r'(analytics|tracking|beacon|telemetry)',
                'action': 'block',
                'description': 'Block common tracking endpoints',
                'priority': 1
            },
            # Cookie rules
            {
                'type': 'cookie',
                'pattern': r'(_ga|_gid|fbp|_fbp)',
                'action': 'block',
                'description': 'Block common tracking cookies',
                'priority': 1
            },
            # Storage rules
            {
                'type': 'storage',
                'pattern': r'(fingerprint|canvas|device)',
                'action': 'block',
                'description': 'Block fingerprinting storage',
                'priority': 2
            },
            # Script rules
            {
                'type': 'script',
                'pattern': r'(navigator\.userAgent|canvas\.toDataURL)',
                'action': 'modify',
                'description': 'Modify fingerprinting scripts',
                'priority': 2
            }
        ]

        conn = sqlite3.connect(self.rules_db)
        c = conn.cursor()

        for rule in default_rules:
            c.execute('''
                INSERT INTO blocking_rules
                (rule_type, pattern, action, description, priority)
                VALUES (?, ?, ?, ?, ?)
            ''', (rule['type'], rule['pattern'], rule['action'],
                  rule['description'], rule['priority']))

        conn.commit()
        conn.close()

    def import_rules(self, rules_file: str):
        """Import rules from JSON file"""
        with open(rules_file, 'r') as f:
            rules = json.load(f)

        conn = sqlite3.connect(self.rules_db)
        c = conn.cursor()

        for rule in rules:
            c.execute('''
                INSERT INTO blocking_rules
                (rule_type, pattern, action, description, priority)
                VALUES (?, ?, ?, ?, ?)
            ''', (rule['type'], rule['pattern'], rule['action'],
                  rule['description'], rule.get('priority',
