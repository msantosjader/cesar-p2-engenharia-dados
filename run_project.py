"""Entrada opt-in da nova ETL. main.py mantém os modos anteriores."""

import argparse
import logging

from src.pipeline import PipelineConfig, run_project
from src.postgres import ddl


def parser():
    result = argparse.ArgumentParser(description="PNAD anual: Bronze → Silver")
    result.add_argument("--backend", choices=["pandas", "spark"], default="pandas")
    result.add_argument("--run-id")
    result.add_argument("--max-rows", type=int, default=100000)
    result.add_argument(
        "--allow-external-writes",
        action="store_true",
        help="Confirma autorização para gravar nos destinos configurados",
    )
    result.add_argument(
        "--print-ddl", action="store_true", help="Somente imprime DDL; não conecta"
    )
    result.add_argument("--schema", default="public")
    result.add_argument("--table", default="pnad_silver")
    return result


if __name__ == "__main__":
    args = parser().parse_args()
    if args.print_ddl:
        print(ddl(args.table, args.schema))
    elif not args.allow_external_writes:
        parser().error(
            "Revise os destinos e autorize as escritas com --allow-external-writes"
        )
    else:
        logging.basicConfig(level=logging.INFO)
        print(
            run_project(
                PipelineConfig.from_env(), args.backend, args.run_id, args.max_rows
            )
        )
