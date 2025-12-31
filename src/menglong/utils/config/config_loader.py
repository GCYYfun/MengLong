import os
import sys
from pathlib import Path
from typing import Optional, Union

import tomllib
from menglong.utils.config.config_type import Config

CONFIG_FILENAMES = [
    ".configs.toml",
    ".configs.template.toml", # For dev/fallback
]

def load_config(config_path: Optional[Union[str, Path]] = None) -> Config:
    """Load configuration from a file or default locations"""
    
    path_to_read = None
    
    if config_path:
        path = Path(config_path)
        if path.exists():
            path_to_read = path
    else:
        # Search order:
        # 1. Env var MENGLONG_CONFIG
        # 2. CWD
        # 3. Home dir
        
        env_path = os.getenv("MENGLONG_CONFIG")
        if env_path and Path(env_path).exists():
            path_to_read = Path(env_path)
        else:
            # Build search directories list:
            # 1. Entry script directory (sys.argv[0]) and its parents - represents the consuming project root
            # 2. CWD and its parents - fallback for interactive sessions
            search_dirs = []
            
            # Add entry script path (the project using MengLong as SDK)
            if sys.argv and sys.argv[0]:
                entry_script = Path(sys.argv[0]).resolve().parent
                search_dirs += [entry_script] + list(entry_script.parents)
            
            # Add CWD path
            cwd = Path.cwd()
            search_dirs += [cwd] + list(cwd.parents)
            
            # Deduplicate while preserving order
            search_dirs = list(dict.fromkeys(search_dirs))
            
            for d in search_dirs:
                for fname in CONFIG_FILENAMES:
                    p = d / fname
                    if p.exists():
                        path_to_read = p
                        break
                if path_to_read:
                    break
            
            if not path_to_read:
                # Fallback to Home dir
                home = Path.home()
                for fname in CONFIG_FILENAMES:
                    p = home / fname
                    if p.exists():
                        path_to_read = p
                        break
    
    if not path_to_read:
        # Return empty default config if no file found
        return Config()

    try:
        with open(path_to_read, "rb") as f:
            data = tomllib.load(f)
        return Config(**data)
    except Exception as e:
        print(f"Warning: Failed to load config from {path_to_read}: {e}")
        return Config()
