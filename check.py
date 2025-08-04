import json
import sys

def get_changed_fields(before, after, path="", action=None):
    changes = []
    
    # Skip if either is None or empty
    if before is None or after is None:
        return changes
    
    # Both dicts: only process common keys that exist in both and are not null/empty
    if isinstance(before, dict) and isinstance(after, dict):
        for key in before.keys() & after.keys():
            before_val = before[key]
            after_val = after[key]
            
            # Skip if either value is None or empty
            if before_val is None or after_val is None:
                continue
            if before_val == "" or after_val == "":
                continue
            if before_val == [] or after_val == []:
                continue
            if before_val == {} or after_val == {}:
                continue
                
            new_path = f"{path}.{key}" if path else key
            changes += get_changed_fields(before_val, after_val, new_path, action)
            
    # Both lists: only process if both lists have content
    elif isinstance(before, list) and isinstance(after, list):
        if len(before) == 0 or len(after) == 0:
            return changes
            
        min_len = min(len(before), len(after))
        for i in range(min_len):
            before_item = before[i]
            after_item = after[i]
            
            # Skip if either item is None or empty
            if before_item is None or after_item is None:
                continue
                
            changes += get_changed_fields(before_item, after_item, f"{path}[{i}]", action)
            
    # Leaf: values differ and both are not null/empty
    else:
        if before != after and before is not None and after is not None:
            if before != "" and after != "":
                changes.append({
                    "key": path,
                    "before": before,
                    "after": after,
                    "action": action or "update"
                })
    return changes

def format_value(value):
    """Format values for simple display"""
    if value is None:
        return "null"
    elif isinstance(value, str):
        return f'"{value}"'
    elif isinstance(value, bool):
        return str(value)
    elif isinstance(value, (int, float)):
        return str(value)
    elif isinstance(value, list):
        if len(value) == 0:
            return "[]"
        elif len(value) == 1 and isinstance(value[0], dict):
            # For single-item lists like metadata_options, credit_specification
            return format_dict_simple(value[0])
        else:
            return f"[{len(value)} items]"
    elif isinstance(value, dict):
        return format_dict_simple(value)
    else:
        return str(value)

def format_dict_simple(d):
    """Format dict as simple key=value pairs"""
    if not d:
        return "{}"
    
    items = []
    for k, v in d.items():
        if isinstance(v, dict):
            # For nested dicts, show first few key names
            nested_keys = list(v.keys())[:2]
            if len(v) > 2:
                items.append(f"{k}={{{', '.join(nested_keys)}, ...}}")
            else:
                items.append(f"{k}={{{', '.join(nested_keys)}}}")
        elif isinstance(v, list):
            if len(v) == 0:
                items.append(f"{k}=[]")
            elif len(v) == 1:
                items.append(f"{k}=[{format_single_value(v[0])}]")
            else:
                items.append(f"{k}=[{len(v)} items]")
        else:
            items.append(f"{k}={format_single_value(v)}")
    
    # Show all items, no truncation
    return "{" + ", ".join(items) + "}"

def format_single_value(value):
    """Format a single value without quotes for dict display"""
    if value is None:
        return "null"
    elif isinstance(value, str):
        return value  # No quotes for cleaner display in dicts
    elif isinstance(value, bool):
        return str(value).lower()
    else:
        return str(value)

def get_action_icon(action):
    """Get icon for action type"""
    icons = {
        "create": "➕",
        "update": "🔄",
        "delete": "❌", 
        "replace": "🔀"
    }
    return icons.get(action, "📝")

def highlight_changes(resource_changes):
    """LLM-friendly function to show changes clearly"""
    if not resource_changes:
        print("STATUS: No resource changes detected.")
        return
    
    for rc in resource_changes:
        actions = rc["change"]["actions"]
        address = rc["address"]
        before = rc["change"].get("before")
        after = rc["change"].get("after")
        
        if actions != ["no-op"]:
            print(f"\nRESOURCE: {address}")
            print(f"ACTION: {', '.join(actions)}")
            print("=" * 50)
            
            # Handle different action types differently
            if actions == ["create"] and before is None and after is not None:
                print("OPERATION: Creating new resource")
                show_create_changes_llm(after)
                
            elif actions == ["delete"] and before is not None and after is None:
                print("OPERATION: Deleting existing resource")
                show_resource_config_llm(before)
                
            elif (("update" in actions or "replace" in actions or ("delete" in actions and "create" in actions)) 
                  and before is not None and after is not None):
                # For updates/replaces, show actual changes
                if "delete" in actions and "create" in actions:
                    operation = "Replacing resource (delete + create)"
                    primary_action = "replace"
                elif "replace" in actions:
                    operation = "Replacing resource"
                    primary_action = "replace"
                else:
                    operation = "Updating resource"
                    primary_action = "update"
                    
                print(f"OPERATION: {operation}")
                
                diffs = get_changed_fields(before, after, action=primary_action)
                
                if diffs:
                    print("\nCHANGES:")
                    for diff in diffs:
                        key = diff['key']
                        before_val = format_value_llm(diff['before'])
                        after_val = format_value_llm(diff['after'])
                        
                        # Handle special cases for better display
                        if diff['before'] is None:
                            print(f"  FIELD: {key}")
                            print(f"    FROM: not_set")
                            print(f"    TO: {after_val}")
                        elif diff['after'] is None:
                            print(f"  FIELD: {key}")
                            print(f"    FROM: {before_val}")
                            print(f"    TO: removed")
                        else:
                            print(f"  FIELD: {key}")
                            print(f"    FROM: {before_val}")
                            print(f"    TO: {after_val}")
                else:
                    print("CHANGES: No field-level changes detected")
            else:
                print(f"OPERATION: Unsupported action combination")
                print(f"  before_exists: {before is not None}")
                print(f"  after_exists: {after is not None}")
            
            print("=" * 50)

def get_actual_aws_defaults():
    """Get the actual AWS defaults for EC2 instances"""
    return {
        # EC2 Instance defaults
        'monitoring': False,
        'get_password_data': False,
        'source_dest_check': True,
        'user_data_replace_on_change': False,
        'hibernation': None,
        'user_data': None,
        'volume_tags': None,
        'timeouts': None,
        'launch_template': [],
        'tags': {},
        'tags_all': {},
        
        # Metadata options defaults
        'metadata_options': [{
            'http_endpoint': 'enabled',
            'http_tokens': 'optional',  # This is the key difference!
            'http_protocol_ipv6': 'disabled'
        }],
        
        # Credit specification defaults
        'credit_specification': [{'cpu_credits': 'standard'}],
        
        # Root block device defaults
        'root_block_device': [{
            'volume_type': 'gp2',
            'volume_size': 8,
            'iops': None,  # Only for gp3/io1/io2
            'throughput': None,  # Only for gp3
            'delete_on_termination': True,
            'tags': None
        }]
    }

def show_create_changes_llm(config):
    """Show what values are being set for a new resource, comparing against actual AWS defaults"""
    
    aws_defaults = get_actual_aws_defaults()
    
    print("\nCONFIGURATION_CHANGES:")
    
    # Compare each field in the 'after' config against AWS defaults
    for field, new_value in config.items():
        if field in ['timeouts', 'tags_all']:  # Skip redundant fields
            continue
            
        aws_default = aws_defaults.get(field, "aws_default_not_specified")
        
        # Only show if the value differs from AWS default
        if new_value != aws_default:
            print(f"  FIELD: {field}")
            print(f"    FROM: {format_aws_default_llm(field, aws_default)}")
            print(f"    TO: {format_value_llm(new_value)}")

def format_aws_default_llm(field, default_value):
    """Format AWS default values for LLM"""
    if default_value == "aws_default_not_specified":
        return "aws_default_unknown"
    elif default_value is None:
        return "aws_default_null"
    elif isinstance(default_value, bool):
        return f"aws_default_boolean_{str(default_value).lower()}"
    elif isinstance(default_value, str):
        return f"aws_default_string_{default_value}"
    elif isinstance(default_value, (int, float)):
        return f"aws_default_number_{default_value}"
    elif isinstance(default_value, list):
        if len(default_value) == 0:
            return "aws_default_empty_list"
        elif len(default_value) == 1 and isinstance(default_value[0], dict):
            return format_dict_llm(default_value[0], prefix="aws_default_")
        else:
            return f"aws_default_list_with_{len(default_value)}_items"
    elif isinstance(default_value, dict):
        if not default_value:
            return "aws_default_empty_object"
        else:
            return format_dict_llm(default_value, prefix="aws_default_")
    else:
        return f"aws_default_value_{str(default_value)}"

def show_resource_config_llm(config):
    """Show resource configuration in LLM-friendly format"""
    important_fields = [
        'ami', 'instance_type', 'monitoring', 'tags',
        'metadata_options', 'credit_specification', 'root_block_device'
    ]
    
    print("\nCURRENT_CONFIGURATION:")
    
    for field in important_fields:
        if field in config and config[field] is not None:
            value = format_value_llm(config[field])
            print(f"  FIELD: {field}")
            print(f"    VALUE: {value}")
    
    # Show any other non-null fields
    other_fields = {k: v for k, v in config.items() 
                   if k not in important_fields and v is not None 
                   and k not in ['timeouts', 'tags_all']}
    
    if other_fields:
        for field, value in other_fields.items():
            formatted_value = format_value_llm(value)
            print(f"  FIELD: {field}")
            print(f"    VALUE: {formatted_value}")

def get_default_value_llm(field, defaults):
    """Get the default value for a field in LLM-friendly format with context"""
    if field in defaults:
        default_val = defaults[field]
        if default_val is None:
            return "aws_default_null"
        elif isinstance(default_val, bool):
            return f"aws_default_boolean_{str(default_val).lower()}"
        else:
            return f"aws_default_value_{str(default_val)}"
    else:
        # For fields we don't know the default, show detailed AWS defaults
        common_defaults = {
            'ami': 'required_field_no_default',
            'instance_type': 'required_field_no_default', 
            'tags': 'aws_default_empty_object',
            'metadata_options': 'aws_default_http_endpoint_enabled_http_tokens_optional',
            'credit_specification': 'aws_default_cpu_credits_standard',
            'root_block_device': 'aws_default_8gb_gp2_volume_delete_on_termination_true',
            'launch_template': 'aws_default_empty_list',
            'region': 'aws_provider_configured_region',
        }
        return common_defaults.get(field, "aws_default_not_specified")

def format_value_llm(value):
    """Format values for LLM consumption"""
    if value is None:
        return "null"
    elif isinstance(value, str):
        return f'string_{value}'
    elif isinstance(value, bool):
        return f'boolean_{str(value).lower()}'
    elif isinstance(value, (int, float)):
        return f'number_{value}'
    elif isinstance(value, list):
        if len(value) == 0:
            return "empty_list"
        elif len(value) == 1 and isinstance(value[0], dict):
            return format_dict_llm(value[0])
        else:
            return f"list_with_{len(value)}_items"
    elif isinstance(value, dict):
        return format_dict_llm(value)
    else:
        return f'value_{str(value)}'

def format_dict_llm(d, prefix=""):
    """Format dict for LLM consumption"""
    if not d:
        return f"{prefix}empty_object"
    
    items = []
    for k, v in d.items():
        if isinstance(v, dict):
            nested_keys = list(v.keys())
            items.append(f"{k}_contains_{len(nested_keys)}_keys")
        elif isinstance(v, list):
            if len(v) == 0:
                items.append(f"{k}_empty_list")
            else:
                items.append(f"{k}_list_with_{len(v)}_items")
        elif isinstance(v, str):
            items.append(f"{k}_string_{v}")
        elif isinstance(v, bool):
            items.append(f"{k}_boolean_{str(v).lower()}")
        elif isinstance(v, (int, float)):
            items.append(f"{k}_number_{v}")
        elif v is None:
            items.append(f"{k}_null")
        else:
            items.append(f"{k}_value_{v}")
    
    return f"{prefix}object_" + "_and_".join(items)

def main():
    """Main function with LLM-friendly output"""
    try:
        # Read plan.json from command line arg or default location
        plan_file = sys.argv[1] if len(sys.argv) > 1 else "plan.json"
        
        with open(plan_file, 'r') as f:
            data = json.load(f)
        
        print("TERRAFORM_PLAN_ANALYSIS_START")
        print("=" * 60)
        
        resource_changes = data.get("resource_changes", [])
        highlight_changes(resource_changes)
        
        # Summary
        total_changes = len([rc for rc in resource_changes if rc["change"]["actions"] != ["no-op"]])
        
        print("\nSUMMARY:")
        print(f"TOTAL_RESOURCES_AFFECTED: {total_changes}")
        if total_changes > 0:
            print("STATUS: changes_detected")
        else:
            print("STATUS: no_changes")
        
        print("=" * 60)
        print("TERRAFORM_PLAN_ANALYSIS_END")
        
    except FileNotFoundError:
        print(f"ERROR: plan_file_not_found_{plan_file}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"ERROR: invalid_json_{e}")
        sys.exit(1)
    except Exception as e:
        print(f"ERROR: unexpected_{e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
