import json
from typing import Any


class ExtendedJSONEncoder(json.JSONEncoder):
    def default(self, obj: Any) -> str:
       return str(obj)
