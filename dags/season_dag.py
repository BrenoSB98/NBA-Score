from __future__ import annotations

import os
import sys
import logging
import pendulum
from datetime import timedelta

from airflow.models.dag import DAG
from airflow.decorators import task

from app.tasks.season_task import run_seasons_task
from app.tasks.run_all_tasks import _get_dependencies, _close_dependencies

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@task.virtualenv(
    task_id="run_seasons_ingest",
    requirements=[f"-r {os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'requirements.txt'))}"],
    system_site_packages=False, 
)
def run_seasons_ingestion_wrapper_decorated():
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

    logger.info("Iniciando wrapper para ingestão de temporadas...")
    db_session, api_client = _get_dependencies()
    try:
        result = run_seasons_task(db=db_session, client=api_client)
        logger.info(f"Resultado da ingestão de temporadas: {result}")
        return result
    except Exception as e:
        logger.error(f"Erro ao executar a ingestão de temporadas: {e}")
        raise
    finally:
        _close_dependencies(db_session)

with DAG(
    dag_id="nba_ingest_seasons",
    start_date=pendulum.datetime(2025, 10, 27, tz="America/Sao_Paulo"),
    schedule=None,
    catchup=False,
    tags=["nba", "ingestion", "metadata"],
    default_args={
        "retries": 2,
        "retry_delay": timedelta(minutes=1),
        "owner": "data_team",
    },
) as dag:
    run_seasons_ingestion_wrapper_decorated()
