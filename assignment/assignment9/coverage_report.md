# Coverage Report

Generated with:
```bash
pytest --cov=src --cov-report=term-missing
```

## Results
```
================================================== test session starts ===================================================
platform darwin -- Python 3.12.7, pytest-7.4.4, pluggy-1.6.0
rootdir: /Users/kebo/Downloads/MS FinMath/Courses/Python/HW/FINM32500-Computing-for-Finance-in-Python/assignment/assignment9
plugins: mock-3.15.1, anyio-4.2.0, cov-7.0.0
collected 6 items                                                                                                        

tests/test_fix_parser.py ..                                                                                        [ 33%]
tests/test_logger.py .                                                                                             [ 50%]
tests/test_order.py .                                                                                              [ 66%]
tests/test_risk_engine.py ..                                                                                       [100%]

==================================================== warnings summary ====================================================
tests/test_logger.py::test_logger_singleton_and_save
tests/test_logger.py::test_logger_singleton_and_save
  /Users/kebo/Downloads/MS FinMath/Courses/Python/HW/FINM32500-Computing-for-Finance-in-Python/assignment/assignment9/tests/../src/logger.py:23: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
    'timestamp': datetime.utcnow().isoformat(),

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
===================================================== tests coverage =====================================================
____________________________________ coverage: platform darwin, python 3.12.7-final-0 ____________________________________

Name                 Stmts   Miss  Cover   Missing
--------------------------------------------------
src/fix_parser.py       29     10    66%   7, 9, 14, 25, 28-31, 36-37
src/logger.py           23      0   100%
src/main.py             25     25     0%   2-37
src/order.py            20      0   100%
src/risk_engine.py      28      4    86%   11-14, 25
--------------------------------------------------
TOTAL                  125     39    69%
============================================= 6 passed, 2 warnings in 0.05s ==============================================
```