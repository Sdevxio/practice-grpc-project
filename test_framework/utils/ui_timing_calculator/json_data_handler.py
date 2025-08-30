import json
import os
from datetime import datetime
from typing import Dict, Any, Optional


class JsonDataHandler:
    """Generic helper class for saving test data to JSON files."""

    def __init__(self, base_output_dir: str = "artifacts"):
        """Initialize with base artifacts directory for JSON files."""
        self.base_output_dir = base_output_dir
        os.makedirs(self.base_output_dir, exist_ok=True)

    def save_test_data(self,
                       data: Dict[str, Any],
                       filename_prefix: str = "test_data",
                       include_timestamp: bool = True,
                       custom_filename: Optional[str] = None,
                       subfolder: str = "general") -> str:
        """Save test data to JSON file with flexible naming.

        Args:
            data: Dictionary containing test data to save
            filename_prefix: Prefix for the filename
            include_timestamp: Whether to include timestamp in filename
            custom_filename: Use custom filename instead of generated one
            subfolder: Subfolder within artifacts directory

        Returns:
            Path to saved JSON file
        """
        # Create directory structure
        output_dir = f"{self.base_output_dir}/{subfolder}"
        os.makedirs(output_dir, exist_ok=True)

        # Add metadata if not present
        if "test_run_timestamp" not in data:
            data["test_run_timestamp"] = datetime.now().isoformat()

        # Generate filename
        if custom_filename:
            filename = f"{output_dir}/{custom_filename}"
        else:
            if include_timestamp:
                timestamp_str = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"{output_dir}/{filename_prefix}_{timestamp_str}.json"
            else:
                filename = f"{output_dir}/{filename_prefix}.json"

        # Ensure .json extension
        if not filename.endswith('.json'):
            filename += '.json'

        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)

        return filename

    def save_performance_data(self,
                              data: Dict[str, Any],
                              test_name: str = "performance_test",
                              subcategory: Optional[str] = None) -> str:
        """Save performance test data to artifacts/performance directory.

        Args:
            data: Performance test data to save
            test_name: Name of the performance test
            subcategory: Optional subcategory (e.g., 'ui_timing', 'load_test')

        Returns:
            Path to saved JSON file
        """
        # Create performance directory structure
        if subcategory:
            output_dir = f"{self.base_output_dir}/performance/{subcategory}"
        else:
            output_dir = f"{self.base_output_dir}/performance"

        os.makedirs(output_dir, exist_ok=True)

        # Add metadata
        if "test_run_timestamp" not in data:
            data["test_run_timestamp"] = datetime.now().isoformat()
        data["category"] = "performance"
        if subcategory:
            data["subcategory"] = subcategory

        # Generate filename with timestamp
        timestamp_str = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{output_dir}/{test_name}_{timestamp_str}.json"

        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)

        return filename

    def append_to_summary_file(self,
                               data: Dict[str, Any],
                               summary_filename: str = "test_summary.json",
                               subfolder: str = "general") -> str:
        """Append test data to a summary JSON file containing multiple test results.

        Args:
            data: Test data to append
            summary_filename: Name of the summary file
            subfolder: Subfolder within artifacts directory

        Returns:
            Path to summary JSON file
        """
        output_dir = f"{self.base_output_dir}/{subfolder}"
        os.makedirs(output_dir, exist_ok=True)
        summary_path = f"{output_dir}/{summary_filename}"

        # Load existing data or create new list
        if os.path.exists(summary_path):
            with open(summary_path, 'r') as f:
                summary_data = json.load(f)
        else:
            summary_data = {"test_results": []}

        # Add new test data
        if "test_results" not in summary_data:
            summary_data["test_results"] = []

        summary_data["test_results"].append(data)
        summary_data["last_updated"] = datetime.now().isoformat()

        with open(summary_path, 'w') as f:
            json.dump(summary_data, f, indent=2)

        return summary_path

    def save_with_categories(self,
                             data: Dict[str, Any],
                             category: str,
                             subcategory: Optional[str] = None) -> str:
        """Save test data with organized directory structure under artifacts.

        Args:
            data: Test data to save
            category: Main category (e.g., 'performance', 'authentication')
            subcategory: Optional subcategory for further organization

        Returns:
            Path to saved JSON file
        """
        # Create category-based directory structure under artifacts
        if subcategory:
            category_dir = f"{self.base_output_dir}/{category}/{subcategory}"
        else:
            category_dir = f"{self.base_output_dir}/{category}"

        os.makedirs(category_dir, exist_ok=True)

        # Generate filename with timestamp
        timestamp_str = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{category_dir}/{category}_{timestamp_str}.json"

        # Add metadata
        if "test_run_timestamp" not in data:
            data["test_run_timestamp"] = datetime.now().isoformat()
        data["category"] = category
        if subcategory:
            data["subcategory"] = subcategory

        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)

        return filename
