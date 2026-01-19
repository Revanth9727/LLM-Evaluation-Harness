"""
Configuration loading and management.
"""
import os
import re
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
from dotenv import load_dotenv


def expand_env_vars(value: Any) -> Any:
    """
    Recursively expand environment variables in config values.
    Supports ${VAR_NAME} syntax.
    """
    if isinstance(value, str):
        # Replace ${VAR} with environment variable value
        pattern = r'\$\{([^}]+)\}'

        def replace_var(match):
            var_name = match.group(1)
            env_value = os.getenv(var_name)
            if env_value is None:
                raise ValueError(f"Environment variable {var_name} is not set")
            return env_value

        return re.sub(pattern, replace_var, value)
    elif isinstance(value, dict):
        return {k: expand_env_vars(v) for k, v in value.items()}
    elif isinstance(value, list):
        return [expand_env_vars(item) for item in value]
    else:
        return value


def load_config(config_path: str) -> Dict[str, Any]:
    """
    Load and parse a YAML config file.
    Expands environment variables in the config.

    Args:
        config_path: Path to YAML config file

    Returns:
        Parsed config dictionary with env vars expanded
    """
    # Load .env file if present
    load_dotenv()

    # Load YAML
    config_file = Path(config_path)
    if not config_file.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    with open(config_file, 'r') as f:
        config = yaml.safe_load(f)

    # Expand environment variables
    config = expand_env_vars(config)

    return config


def validate_run_config(config: Dict[str, Any]) -> None:
    """
    Validate that a run config has required fields.

    Args:
        config: Config dictionary to validate

    Raises:
        ValueError: If required fields are missing
    """
    required_fields = ['run_name', 'dataset_path', 'candidates']
    for field in required_fields:
        if field not in config:
            raise ValueError(f"Required config field missing: {field}")

    # Validate candidates
    if 'A' not in config['candidates'] or 'B' not in config['candidates']:
        raise ValueError("Config must define both candidates.A and candidates.B")

    for candidate in ['A', 'B']:
        cand_config = config['candidates'][candidate]
        if 'provider' not in cand_config or 'model' not in cand_config:
            raise ValueError(f"Candidate {candidate} must have 'provider' and 'model'")
