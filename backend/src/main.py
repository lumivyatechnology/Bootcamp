import argparse

from run import main as run_server
from run_cli import run as run_cli
from config.settings import settings
import logging

logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(description="Run analytics agent")
    parser.add_argument(
        "-m", "--mode",
        choices=["server", "cli"],
        default="server",
        help="Execution mode: 'server' or 'cli' (default: server)"
    )
    args = parser.parse_args()

    if args.mode == "server":
        run_server()
    elif args.mode == "cli":
        import asyncio
        asyncio.run(run_cli())


if __name__ == "__main__":

    logger.info("Starting | Running Application")
    if settings.RUN_ETL:
        from scraper.data_ingestion.etl import run_etl
        logger.info("Running ETL")
        run_etl(data_file="samsung_phones_specs.csv")

    main()
