# singleton.py
import json
import os

def load_json(path):
    with open(path, "r") as f:
        return json.load(f)

class Config:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            base_dir = os.path.dirname(__file__)
            config_path = os.path.join(base_dir, "..", "data", "config.json")
            config_data = load_json(os.path.abspath(config_path))
            cls._instance.log_level = config_data.get("log_level")
            cls._instance.data_path = config_data.get("data_path")
            cls._instance.report_path = config_data.get("report_path")
            cls._instance.default_strategy = config_data.get("default_strategy")
        return cls._instance
    
if __name__ == "__main__":
    config1 = Config()
    config2 = Config()
    assert config1 is config2
    print(f"Config 1 and 2 are the same instance")