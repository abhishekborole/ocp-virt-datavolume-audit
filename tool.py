"""Collect real CDI import progress and warning events for troubleshooting failed imports."""
import argparse
from decimal import Decimal
import json
import sys
import subprocess
from datetime import datetime, timezone
from oc_client import Client, VM, VMI, MIG, SNAP, quantity, age_hours, condition, require_name, stopped, escape, migration


def execute(client,args):
    events = client.items('events')
    return [{'name':dv['metadata']['name'], 'phase':dv.get('status',{}).get('phase'), 'progress':dv.get('status',{}).get('progress'),
             'conditions':dv.get('status',{}).get('conditions',[]), 'warnings':[{'reason':event.get('reason'), 'message':event.get('message')} for event in events if event.get('type') == 'Warning' and event.get('involvedObject',{}).get('uid') == dv['metadata']['uid']]} for dv in client.items('datavolumes.cdi.kubevirt.io')]


def main():
    parser = argparse.ArgumentParser(description='Collect real CDI import progress and warning events for troubleshooting failed imports.')
    parser.add_argument('--context',required=True,help='Explicit existing oc kubeconfig context')
    parser.add_argument('--namespace',required=True,help='Namespace for workload operations')
    parser.add_argument('--name',help='Exact workload/resource name where required')
    parser.add_argument('--apply',action='store_true',help='Execute the requested change; default is preview')

    args = parser.parse_args()
    try:
        result = execute(Client(args.context,args.namespace),args)
        print(json.dumps({'context':args.context,'namespace':args.namespace,'collected_at':datetime.now(timezone.utc).isoformat(),'result':result},indent=2))
    except (RuntimeError,ValueError,KeyError,OSError,TimeoutError,subprocess.SubprocessError) as error:
        print(str(error),file=sys.stderr)
        return 2
    return 0


if __name__ == '__main__': raise SystemExit(main())
