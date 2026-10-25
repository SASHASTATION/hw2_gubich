"""Run submission checks and retain the real command output and dbt results."""
import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('csv', type=Path)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    artifacts = root / 'artifacts'
    artifacts.mkdir(exist_ok=True)
    dbt = root / 'dbt'
    csv_path = os.path.relpath(args.csv.resolve(), root)
    checks = [
        ('dbt_build', ['dbt', 'build', '--profiles-dir', '.'], dbt),
        ('dbt_test', ['dbt', 'test', '--profiles-dir', '.'], dbt),
        ('sqlfluff', ['sqlfluff', 'lint', 'models', 'tests'], dbt),
        ('dbt_docs', ['dbt', 'docs', 'generate', '--profiles-dir', '.'], dbt),
        ('csv_reference', [sys.executable, 'scripts/verify_results.py', csv_path], root),
    ]
    for name, command, cwd in checks:
        result = subprocess.run(command, cwd=cwd, text=True, stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT)
        output = re.sub(r'\x1b\[[0-9;]*m', '', result.stdout)
        display_command = ['python' if part == sys.executable else part for part in command]
        (artifacts / f'{name}.log').write_text('$ ' + ' '.join(display_command) + '\n' + output)
        print(f'{name}: exit={result.returncode}', flush=True)
        if result.returncode:
            print(output)
            raise SystemExit(result.returncode)
        if name in ('dbt_build', 'dbt_test'):
            shutil.copyfile(dbt / 'target/run_results.json', artifacts / f'{name}_results.json')
    results = json.loads((artifacts / 'dbt_test_results.json').read_text())
    print(f"All checks passed; dbt test: {len(results['results'])} tests")


if __name__ == '__main__':
    main()
