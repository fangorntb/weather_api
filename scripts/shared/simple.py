from datetime import date
from functools import wraps
from typing import Any, Dict, List


def get_date() -> str:
    return date.today().strftime('%m-%d-%y')


def empty_str(s: Any) -> str:
    return f"{s}" if s is not None else "*"


def stringify_return(func: callable) -> callable:
    @wraps(func)
    def _(*args, **kwargs) -> str:
        return str(func(*args, **kwargs))

    return _


def remove_none_from_dct(dct: Dict) -> Dict:
    return {key: value for key, value in dct.items() if value is not None}


def flatten_nested_objects(input_list: List[Dict[str, Any]], model_name: str) -> List[Dict]:
    def flatten_object(obj, level=1):
        flattened = {}
        sub_objects = {}

        for key, value in obj.items():
            if "__" in key:
                sub_model, sub_key = key.split("__", 1)
                sub_model += 's'
                if sub_model not in sub_objects:
                    sub_objects[f'{sub_model}'] = {}
                sub_objects[f'{sub_model}'][sub_key] = value
            else:
                flattened[key] = value

        for sub_model, sub_obj in sub_objects.items():
            if len(sub_obj) > 1:
                flattened[sub_model] = flatten_object(sub_obj, level + 1)
            else:
                flattened.update(sub_obj)

        return flattened

    result = []

    for item in input_list:
        flattened_item = flatten_object(item)
        result.append({model_name: flattened_item})

    return result


def flatten_nested_decorator(model_name):
    def __(func: callable):
        @wraps(func)
        async def _decorator(*args, **kwargs):
            return flatten_nested_objects(await func(*args, **kwargs), model_name)

        return _decorator

    return __


def all_is_none(*args):
    return all(v is None for v in args)


def delete_keys(dct: Dict, *keys) -> Dict:
    return {k: v for k, v in dct.items() if k not in keys}