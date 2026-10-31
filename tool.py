"""Offline analysis; consumes normalized JSON, never connects to infrastructure."""
import argparse
import ipaddress
import json
import math
from pathlib import Path
import sys


def positive(value):
    if value <= 0:
        raise ValueError('Expected a positive value')
    return value


def integer_positive(value):
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError('Expected a positive integer')
    return positive(value)


def validate(value, schema, path='input'):
    """Validate required fields and primitive types; allow extra keys."""
    if isinstance(schema, dict):
        if not isinstance(value, dict): raise ValueError(path + ': expected object')
        for key, child in schema.items():
            if key not in value: raise ValueError(path + ': missing ' + key)
            validate(value[key], child, path + '.' + key)
    elif isinstance(schema, list):
        if not isinstance(value, list): raise ValueError(path + ': expected list')
        if schema:
            for index, item in enumerate(value): validate(item, schema[0], path + '[' + str(index) + ']')
    elif isinstance(schema, bool):
        if not isinstance(value, bool): raise ValueError(path + ': expected boolean')
    elif isinstance(schema, (int, float)):
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
            raise ValueError(path + ': expected finite number')
        if isinstance(schema, int) and not isinstance(value, int): raise ValueError(path + ': expected integer')
        if schema >= 0 and value < 0: raise ValueError(path + ': expected nonnegative number')
    elif not isinstance(value, str):
        raise ValueError(path + ': expected string')


def analyze(data):
    validate(data, SCHEMA)
    return _analyze(data)


def main():
    parser = argparse.ArgumentParser(description=DESCRIPTION)
    parser.add_argument('input', type=Path, help='Normalized JSON file; see examples/sample.json')
    args = parser.parse_args()
    try:
        with args.input.open(encoding='utf-8-sig') as stream:
            data = json.load(stream)
        print(json.dumps(analyze(data), indent=2, sort_keys=True, allow_nan=False))
    except (OSError, ValueError, TypeError, KeyError) as error:
        print('Input error: ' + str(error), file=sys.stderr)
        return 2
    return 0


SCHEMA = {'max_elapsed_minutes': 60, 'imports': [{'name': 'ubuntu-base', 'phase': 'Succeeded', 'elapsed_minutes': 12}]}
DESCRIPTION = 'Find failed imports and imports beyond a local elapsed-time budget.'

def _analyze(data):
    issues = []
    for item in data['imports']:
        if item['phase'] in ('Failed', 'Error'): issues.append(item['name'] + ': failed import')
        elif item['phase'] != 'Succeeded' and item['elapsed_minutes'] > data['max_elapsed_minutes']:
            issues.append(item['name'] + ': import exceeds time budget')
    return {'issues':issues, 'healthy':not issues}

if __name__ == '__main__':
    raise SystemExit(main())
