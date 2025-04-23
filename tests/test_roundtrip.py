#!/usr/bin/env python3
# tests/test_roundtrip.py
import pathlib
import tempfile
import xml.etree.ElementTree as ET
import yaml

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from patcher import load_xml, apply_patch, validate_patch

def test_key_application():
    """Test that all keys in YAML are applied to the XML"""
    # Create a simple test template
    template_str = """<?xml version="1.0" encoding="utf-8"?>
    <Strategy>
        <BuildTradingOptions>
            <Params></Params>
        </BuildTradingOptions>
        <BuildMode>
            <generationType>genetic-evolution</generationType>
            <PopulationSize>100</PopulationSize>
            <MaxGenerations>25</MaxGenerations>
            <Islands>2</Islands>
        </BuildMode>
        <SLPTOptions>
            <MinSLInPips>10</MinSLInPips>
            <MaxSLInPips>50</MaxSLInPips>
        </SLPTOptions>
        <Symbol>EURUSD_M15</Symbol>
        <Data>
            <From>2020-01-01</From>
            <To>2024-12-31</To>
        </Data>
        <BacktestSettings>
            <TestPrecision>15</TestPrecision>
            <Spread>1</Spread>
            <Slippage>0</Slippage>
        </BacktestSettings>
    </Strategy>
    """
    
    # Create a test config
    config = {
        "trading_options": {
            "MaxTradesPerDay": 6,
            "DontTradeOnWeekends": True
        },
        "build_mode": {
            "PopulationSize": 200,
            "MaxGenerations": 50,
            "Islands": 4
        },
        "slpt": {
            "MinSLInPips": 5,
            "MaxSLInPips": 25
        },
        "data_setup": {
            "symbol": "EURUSD",
            "timeframe": "M15",
            "date_from": "2020-04-17",
            "date_to": "2025-04-18",
            "spread": 2,
            "slippage": 1
        }
    }
    
    # Write the template to a temp file
    with tempfile.NamedTemporaryFile(suffix=".xml", delete=False) as f:
        f.write(template_str.encode('utf-8'))
        template_path = pathlib.Path(f.name)
    
    try:
        # Load the template
        tree = load_xml(template_path)
        
        # Apply the patch
        apply_patch(tree, config)
        
        # Write to a new temp file
        with tempfile.NamedTemporaryFile(suffix=".xml", delete=False) as f:
            output_path = pathlib.Path(f.name)
            tree.write(output_path, encoding="utf-8", xml_declaration=True)
        
        try:
            # Validate the patched file
            patched_tree = load_xml(output_path)
            success, message = validate_patch(patched_tree, config)
            
            # Check that validation passed
            assert success, f"Validation failed: {message}"
            
            # Check specific values
            root = patched_tree.getroot()
            
            # Check trading options
            params = root.find(".//BuildTradingOptions/Params")
            max_trades_param = params.find("./Param[@key='MaxTradesPerDay']")
            assert max_trades_param is not None
            assert max_trades_param.text == "6"
            
            # Check build mode
            build_mode = root.find(".//BuildMode")
            assert build_mode.find("./PopulationSize").text == "200"
            assert build_mode.find("./MaxGenerations").text == "50"
            assert build_mode.find("./Islands").text == "4"
            
            # Check SL/PT
            slpt = root.find(".//SLPTOptions")
            assert slpt.find("./MinSLInPips").text == "5"
            assert slpt.find("./MaxSLInPips").text == "25"
            
            # Check symbol and data setup
            symbol_node = root.find(".//Symbol")
            assert symbol_node.text == "EURUSD_M15"
            
            data_node = root.find(".//Data")
            assert data_node.find("./From").text == "2020-04-17"
            assert data_node.find("./To").text == "2025-04-18"
            
            backtest = root.find(".//BacktestSettings")
            assert backtest.find("./Spread").text == "2"
            assert backtest.find("./Slippage").text == "1"
            
        finally:
            # Clean up the output file
            output_path.unlink(missing_ok=True)
    finally:
        # Clean up the template file
        template_path.unlink(missing_ok=True)

if __name__ == "__main__":
    test_key_application()
    print("All tests passed!")