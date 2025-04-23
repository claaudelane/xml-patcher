This directory contains pytest sanity checks for the XML patcher.

The test_roundtrip.py file validates:
- Structural parity (no extra/missing tags)
- All YAML keys are correctly applied
- Re-parsing the generated file after writing succeeds