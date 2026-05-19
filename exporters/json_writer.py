import json 
from datetime import datetime

def datetime_handler(obj):
    """
    AWS return date as Python datetime object, when we try json.dump on this is fails,
    'TypeError: Object of type datetime is not JSON serializable'
    datetime_handle convert the datetime into a string, and string is valid JSON.
    """
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f"Type {type(obj)} is not serializable")

def export_to_json(data, filepath):
    """
    export_to_json, export the data to filepath, it works as:
    -> if no data, print there is no data to export, return False, and stop the export for that file.
    -> then we use try/except block is we have data.
    -> in try block we manage how and where to store data.
    -> in except block we handle error, if try operation fails, due to disk full, wrong permissions, folder doesn't exist, 
    """
    if data is None:
        print(f"No data to export to {filepath}")
        return False
    try: 
        with open(filepath, "w") as f:
            json.dump(data, f, indent=4, default=datetime_handler)
        print(f"Saved -> {filepath}")
        return True
    except OSError as e:
        print(f"Failed to write {filepath} : {e}")
        return False
              