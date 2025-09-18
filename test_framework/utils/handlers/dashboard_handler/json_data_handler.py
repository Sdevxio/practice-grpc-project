import json
import os
from typing import Dict, Any


class JsonDataHandler:
    """Helper class for saving test data to JSON files."""

    def __init__(self, base_output_dir: str = "artifacts"):
        """Initialize with base artifacts directory for JSON files."""
        self.base_output_dir = base_output_dir
        os.makedirs(self.base_output_dir, exist_ok=True)

    def append_to_summary_file(self, data: Dict[str, Any], summary_filename: str = "performance_history.json",
                               subfolder: str = "performance") -> str:
        """Append a record to a summary JSON file (list of dicts)."""
        summary_dir = os.path.join(self.base_output_dir, subfolder)
        os.makedirs(summary_dir, exist_ok=True)
        summary_path = os.path.join(summary_dir, summary_filename)
        # Load existing data
        if os.path.exists(summary_path):
            with open(summary_path, 'r') as f:
                try:
                    existing = json.load(f)
                    if isinstance(existing, dict) and "test_results" in existing:
                        records = existing["test_results"]
                    elif isinstance(existing, list):
                        records = existing
                    else:
                        records = []
                except Exception:
                    records = []
        else:
            records = []
        records.append(data)
        # Save as a list (for compatibility)
        with open(summary_path, 'w') as f:
            json.dump(records, f, indent=2)
        return summary_path