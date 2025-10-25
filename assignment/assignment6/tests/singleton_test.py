from src.singleton import Config

def test_singleton_shared_instance():
    c1 = Config()
    c2 = Config()
    assert c1 is c2  

def test_singleton_loads_config_fields(monkeypatch, tmp_path):
    config_path = tmp_path / "config.json"
    config_path.write_text('{"log_level": "INFO", "data_path": "data/", "report_path": "reports/", "default_strategy": "mean_reversion"}')

    monkeypatch.chdir(tmp_path)  
    c = Config()
    assert c.log_level == "INFO"
    assert c.data_path == "data/"
    assert c.report_path == "reports/"
    assert c.default_strategy == "mean_reversion"
