#!/usr/bin/env python3
# patcher.py
import argparse
import yaml
import difflib
import xml.etree.ElementTree as ET
import pathlib
import datetime
import sys
import tempfile
from typing import Dict, Any

def load_xml(path: pathlib.Path) -> ET.ElementTree:
    """
    Load XML with preserved whitespace and comments
    
    Args:
        path: Path to XML file
        
    Returns:
        ET.ElementTree object
    """
    parser = ET.XMLParser(target=ET.TreeBuilder(insert_comments=True))
    try:
        tree = ET.parse(path, parser=parser)
    except UnicodeDecodeError:
        # Try with cp1252 encoding (Windows default)
        with open(path, 'r', encoding='cp1252') as f:
            content = f.read()
        tree = ET.ElementTree(ET.fromstring(content, parser=parser))
    return tree

def upsert_param(params_node, key, value, class_name="Generic"):
    """
    Update or insert a parameter in a Params node
    
    Args:
        params_node: XML node containing parameters
        key: Parameter key to update
        value: New value for the parameter
        class_name: Class attribute for the parameter
    """
    # Look for existing parameter with this key
    param = params_node.find(f"./Param[@key='{key}']")
    
    if param is not None:
        # Update existing parameter
        param.text = str(value)
    else:
        # Create new parameter
        param = ET.SubElement(params_node, "Param")
        param.set("key", key)
        param.set("class", class_name)
        param.text = str(value)

def apply_patch(tree: ET.ElementTree, cfg: dict):
    """
    Apply patches from config to the XML tree
    
    Args:
        tree: ElementTree to patch
        cfg: Configuration dictionary with patch values
    """
    root = tree.getroot()
    
    # Patch trading options
    if "trading_options" in cfg:
        params = root.find(".//BuildTradingOptions/Params")
        if params is not None:
            for k, v in cfg["trading_options"].items():
                upsert_param(params, k, v)
    
    # Patch build mode options
    if "build_mode" in cfg:
        build_mode = root.find(".//BuildMode")
        if build_mode is not None:
            for k, v in cfg["build_mode"].items():
                elem = build_mode.find(f"./{k}")
                if elem is not None:
                    elem.text = str(v)
                else:
                    # Create the element if it doesn't exist
                    new_elem = ET.SubElement(build_mode, k)
                    new_elem.text = str(v)
    
    # Patch SL/PT options
    if "slpt" in cfg:
        slpt = root.find(".//SLPTOptions")
        if slpt is not None:
            for k, v in cfg["slpt"].items():
                elem = slpt.find(f"./{k}")
                if elem is not None:
                    elem.text = str(v)
                else:
                    # Create the element if it doesn't exist
                    new_elem = ET.SubElement(slpt, k)
                    new_elem.text = str(v)
    
    # Patch filter conditions
    if "conditions" in cfg:
        conditions = root.find(".//FilterParams/Conditions")
        if conditions is not None:
            for condition_key, v in cfg["conditions"].items():
                # Parse the condition key which should be in the format:
                # ColumnName_SampleType where SampleType is either IS or OOS
                parts = condition_key.split('_')
                if len(parts) < 2:
                    continue
                    
                column_name = '_'.join(parts[:-1])
                sample_type = parts[-1]  # IS or OOS
                
                # Find the right condition by column name and sample type
                for condition in conditions.findall("./Condition"):
                    col_value = condition.find("./Left-Side/Column-Value")
                    if col_value is not None:
                        if col_value.get("column") == column_name:
                            # Check sample type (10=IS, 20=OOS)
                            sample_attr = col_value.get("sampleType")
                            if (sample_type == "IS" and sample_attr == "10") or \
                               (sample_type == "OOS" and sample_attr == "20"):
                                # Update the condition value
                                numeric_val = condition.find("./Right-Side/Numeric-Value")
                                if numeric_val is not None:
                                    numeric_val.set("value", str(v))
                                    condition.set("use", "true")

def generate_diff(original_path, new_path):
    """
    Generate a unified diff between two files
    
    Args:
        original_path: Path to the original file
        new_path: Path to the new file
        
    Returns:
        String containing the unified diff
    """
    try:
        with open(original_path, 'r', encoding='utf-8') as f:
            original_lines = f.readlines()
    except UnicodeDecodeError:
        with open(original_path, 'r', encoding='cp1252') as f:
            original_lines = f.readlines()
    
    with open(new_path, 'r', encoding='utf-8') as f:
        new_lines = f.readlines()
    
    diff = difflib.unified_diff(
        original_lines, 
        new_lines,
        fromfile=f'a/{original_path.name}',
        tofile=f'b/{new_path.name}',
        n=3
    )
    
    return ''.join(diff)

def format_diff_for_display(diff_content):
    """
    Format diff content for better readability in the terminal
    
    Args:
        diff_content: Raw diff content
        
    Returns:
        Formatted diff content for display
    """
    # Split the diff into lines
    lines = diff_content.splitlines()
    formatted_lines = []
    
    for line in lines:
        if not line:
            formatted_lines.append(line)
            continue
            
        if line.startswith('+++') or line.startswith('---'):
            # File headers - make them stand out
            formatted_lines.append(f"\033[1;36m{line}\033[0m")  # Cyan, bold
        elif line.startswith('@@'):
            # Line information - make it distinct
            formatted_lines.append(f"\033[1;34m{line}\033[0m")  # Blue, bold
        elif line.startswith('+'):
            # Added lines - green
            # For XML, indent the tags for better readability
            formatted_lines.append(f"\033[32m{line}\033[0m")    # Green
        elif line.startswith('-'):
            # Removed lines - red
            formatted_lines.append(f"\033[31m{line}\033[0m")    # Red
        else:
            # Context lines - normal color
            formatted_lines.append(line)
            
    return '\n'.join(formatted_lines)

def validate_patch(tree: ET.ElementTree, cfg: dict):
    """
    Validate that the patched XML contains the expected values
    
    Args:
        tree: Patched XML ElementTree
        cfg: Configuration dictionary with expected values
        
    Returns:
        Tuple of (success, error_message)
    """
    # Validate BuildTradingOptions
    if "trading_options" in cfg:
        params = tree.find(".//BuildTradingOptions/Params")
        if params is not None:
            for k, expected in cfg["trading_options"].items():
                elem = next((p for p in params if p.get("key")==k), None)
                if elem is None or elem.text != str(expected):
                    actual = elem.text if elem is not None else "NOT FOUND"
                    return False, f"Validation failed for trading_options.{k}: expected '{expected}', got '{actual}'"
    
    # Validate BuildMode
    if "build_mode" in cfg:
        build_mode = tree.find(".//BuildMode")
        if build_mode is not None:
            for k, expected in cfg["build_mode"].items():
                child = build_mode.find(f"./{k}")
                if child is None or child.text != str(expected):
                    actual = child.text if child is not None else "NOT FOUND"
                    return False, f"Validation failed for build_mode.{k}: expected '{expected}', got '{actual}'"
    
    # Validate SL/PT
    if "slpt" in cfg:
        slpt = tree.find(".//SLPTOptions")
        if slpt is not None:
            for k, expected in cfg["slpt"].items():
                child = slpt.find(f"./{k}")
                # Since we now create missing elements, this should always exist
                # But we'll keep the check for robustness
                if child is None or child.text != str(expected):
                    actual = child.text if child is not None else "NOT FOUND"
                    return False, f"Validation failed for slpt.{k}: expected '{expected}', got '{actual}'"
    
    return True, "Validation successful"

def summarize_changes(cfg):
    """
    Create a human-readable summary of changes to be applied
    
    Args:
        cfg: Configuration dictionary with patch values
        
    Returns:
        String containing a summary of changes
    """
    summary = []
    
    # Trading options
    if "trading_options" in cfg:
        summary.append("Trading Options:")
        for k, v in cfg["trading_options"].items():
            summary.append(f"  • {k} = {v}")
    
    # Build mode options
    if "build_mode" in cfg:
        summary.append("\nBuild Mode:")
        for k, v in cfg["build_mode"].items():
            summary.append(f"  • {k} = {v}")
    
    # SL/PT options
    if "slpt" in cfg:
        summary.append("\nSL/PT Options:")
        for k, v in cfg["slpt"].items():
            summary.append(f"  • {k} = {v}")
    
    # Filter conditions
    if "conditions" in cfg:
        summary.append("\nFilter Conditions:")
        for condition_key, v in cfg["conditions"].items():
            summary.append(f"  • {condition_key} = {v}")
    
    return '\n'.join(summary)

def main(args):
    # Load template
    template_path = pathlib.Path(args.template)
    if not template_path.exists():
        print(f"Error: Template file {args.template} not found", file=sys.stderr)
        return 1
    
    # Load YAML config
    cfg_path = pathlib.Path(args.cfg)
    if not cfg_path.exists():
        print(f"Error: Config file {args.cfg} not found", file=sys.stderr)
        return 1
    
    try:
        cfg = yaml.safe_load(open(cfg_path))
    except yaml.YAMLError as e:
        print(f"Error parsing YAML file: {e}", file=sys.stderr)
        return 1
    
    # Parse XML
    try:
        template = load_xml(template_path)
    except ET.ParseError as e:
        print(f"Error parsing XML template: {e}", file=sys.stderr)
        return 1
    
    # Apply patches
    apply_patch(template, cfg)
    
    # Determine output path
    if args.out:
        out_path = pathlib.Path(args.out)
    else:
        timestamp = datetime.datetime.now().strftime("%Y-%m-%dT%H-%M")
        out_path = pathlib.Path(f"out/Mean-Reversal_{timestamp}.xml")
    
    # For dry-run mode, create a temporary file for diff
    if args.dry_run:
        temp_dir = pathlib.Path(tempfile.gettempdir())
        temp_out = temp_dir / "temp_patched.xml"
        template.write(temp_out, encoding="utf-8", xml_declaration=True)
        
        # Generate diff
        diff_content = generate_diff(template_path, temp_out)
        
        # Print summary of changes
        print("\n=== 📋 Summary of Changes ===\n")
        print(summarize_changes(cfg))
        
        # Print the diff with formatting
        print("\n=== 📄 Diff Preview (Dry Run) ===\n")
        try:
            print(format_diff_for_display(diff_content))
        except Exception:
            # Fallback to plain diff if formatting fails
            print(diff_content)
        
        # Remove temp file
        temp_out.unlink()
        
        if args.validate:
            # Validate using the XML tree in memory
            success, message = validate_patch(template, cfg)
            if success:
                print(f"\n✅ {message}")
            else:
                print(f"\n❌ {message}", file=sys.stderr)
                return 1
        
        return 0
    
    # Ensure output directory exists
    out_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Write patched file
    template.write(out_path, encoding="utf-8", xml_declaration=True)
    print(f"✅ Patched file written to {out_path}")
    
    # Generate diff file
    diff_path = out_path.with_suffix(".diff")
    diff_content = generate_diff(template_path, out_path)
    
    with open(diff_path, 'w', encoding='utf-8') as f:
        f.write(diff_content)
    
    print(f"✅ Diff file written to {diff_path}")
    
    # Validate if requested
    if args.validate:
        # Re-parse the output file to ensure it's valid
        try:
            patched = load_xml(out_path)
            success, message = validate_patch(patched, cfg)
            if success:
                print(f"✅ {message}")
            else:
                print(f"❌ {message}", file=sys.stderr)
                return 1
        except ET.ParseError as e:
            print(f"Error validating patched XML: {e}", file=sys.stderr)
            return 1
    
    return 0

if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Patch SQX XML templates with values from YAML config")
    ap.add_argument("--template", required=True, help="Path to the XML template file")
    ap.add_argument("--cfg", required=True, help="Path to the YAML configuration file")
    ap.add_argument("--out", help="Output path for the patched XML file")
    ap.add_argument("--validate", action="store_true", help="Validate the output file after patching")
    ap.add_argument("--dry-run", action="store_true", help="Print diff without writing files")
    
    sys.exit(main(ap.parse_args()))