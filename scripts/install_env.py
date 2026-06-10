"""Cross-platform orchestration script to boot the RSSA backend infrastructure.

Ensures sibling repositories exist, builds the storage layer, streams the
migration logs, boots the API layer, and conditionally trains ML models.
"""

import argparse
import subprocess
import sys
import time
from pathlib import Path

import structlog
from horadric_lib.logging import configure_logging

logging_path = configure_logging('runtime/logs')
logger = structlog.getLogger('RSSA Platform Setup')

SCRIPT_DIR = Path(__file__).parent.resolve()
API_DIR = SCRIPT_DIR.parent
STORAGE_DIR = (API_DIR.parent / 'rssa-storage').resolve()
RECOMMENDER_DIR = (API_DIR.parent / 'rssa-recommender').resolve()


def run_command(cmd: list[str], cwd: Path, stream_output: bool = False):
    """Executes a shell command across platforms."""
    try:
        if stream_output:
            process = subprocess.Popen(
                cmd, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1
            )

            if process.stdout:
                for line in process.stdout:
                    print(line, end='')
                    sys.stdout.flush()

            process.wait()
            if process.returncode != 0:
                sys.exit(f'\n Command failed with exit code {process.returncode}. Halting setup.')
        else:
            subprocess.run(cmd, cwd=cwd, check=True, capture_output=True, text=True)
    except FileNotFoundError:
        sys.exit('\nDocker is not installed or not running. Please start Docker Desktop and try again.')
    except subprocess.CalledProcessError as e:
        sys.exit(f'\nCommand failed: {" ".join(cmd)}\nError: {e.stderr}')


def main():
    parser = argparse.ArgumentParser(description='Boot RSSA Infrastructure.')
    parser.add_argument(
        '--skip-model-training', action='store_true', help='Skip training the recommender models upon boot.'
    )
    args = parser.parse_args()

    logger.info('Validating Repository Structure')

    missing_repos = []
    if not STORAGE_DIR.exists():
        missing_repos.append('rssa-storage')
    if not RECOMMENDER_DIR.exists():
        missing_repos.append('rssa-recommender')

    if missing_repos:
        sys.exit(
            f'Missing sibling repositories: {", ".join(missing_repos)}.\n'
            f'Ensure all repositories are cloned into the same parent directory.'
        )
    logger.info('All sibling repositories found.')

    logger.info('Booting Storage Layer & Initializing Databases')
    run_command(
        ['docker', 'compose', 'up', '-d', '--build', '--force-recreate'],
        cwd=STORAGE_DIR,
        stream_output=True,
    )

    logger.info('Waiting for Migrator Container...')
    time.sleep(3)

    logger.info('Streaming Database Ingestion Logs')
    run_command(['docker', 'logs', '-f', 'rssa_migrator'], cwd=STORAGE_DIR, stream_output=True)

    inspect_cmd = ['docker', 'inspect', 'rssa_migrator', "--format='{{.State.ExitCode}}'"]
    result = subprocess.run(inspect_cmd, cwd=STORAGE_DIR, capture_output=True, text=True)
    exit_code = result.stdout.strip().replace("'", '')

    if exit_code != '0':
        sys.exit(f'\n Database migration failed (Exit Code {exit_code}). Please check the logs above.')
    logger.info('Database seeding complete.')

    logger.info('Booting API & Recommender Layers')
    run_command(['docker', 'compose', 'up', '-d', '--build', '-V'], cwd=API_DIR, stream_output=True)

    if not args.skip_model_training:
        logger.info('Training Recommender Models')
        time.sleep(2)

        run_command(
            ['docker', 'exec', 'rssa_recommender', 'uv', 'run', 'python', 'scripts/build_models.py'],
            cwd=API_DIR,
            stream_output=True,
        )
        logger.info('Model training complete.')
    else:
        logger.info('Skipping Model Training (--skip-model-training flag detected)')

    logger.info('Environment Ready!')
    logger.info('API is running', path='http://localhost:8000')
    logger.info('Postgres is running', path='localhost:5434')
    logger.info('Recommender Simulator is running', path='http://localhost:5000')


if __name__ == '__main__':
    main()
