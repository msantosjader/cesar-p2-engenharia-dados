from copy import deepcopy
from unittest.mock import Mock, patch

import pytest

import main
from src.ibge import TABELAS_PNAD_PROJETO
from src.pipeline import PipelineConfig, extract_project, run_project


def test_legacy_project_mode_extracts_all_tables_and_closes():
    loader, extractor = Mock(), Mock()
    extractor.get_pnad.return_value = [{"id": "sample"}]
    with (
        patch.object(main, "CLI") as cli,
        patch.object(main, "Load", return_value=loader),
        patch.object(main, "Extract", return_value=extractor),
    ):
        cli.return_value.run.return_value = "pnad-projeto"
        main.run_pipeline()
    assert extractor.get_pnad.call_count == 7
    assert all(
        call.args[0].startswith("https://")
        for call in extractor.get_pnad.call_args_list
    )
    assert loader.save_to_mongodb.call_count == 7
    loader.close.assert_called_once()


def test_legacy_activity_keeps_destination():
    loader, extractor = Mock(), Mock()
    with (
        patch.object(main, "CLI") as cli,
        patch.object(main, "Load", return_value=loader),
        patch.object(main, "Extract", return_value=extractor),
    ):
        cli.return_value.run.return_value = "https://example.invalid"
        main.run_pipeline()
    loader.save_to_mongodb.assert_called_once_with(
        db_name="ibge_database",
        collection_name="pnad_extractions",
        data=extractor.get_pnad.return_value,
    )
    loader.close.assert_called_once()


def test_extract_validates_every_table_before_writing(documents):
    extractor = Mock()

    def payload(url, **kwargs):
        table = int(url.split("/agregados/")[1].split("/")[0])
        spec = TABELAS_PNAD_PROJETO[table]
        variables = []
        for variable_id in spec["variaveis"].split("|"):
            variable = deepcopy(documents[0]["payload"][0])
            variable["id"] = variable_id
            for result in variable["resultados"]:
                result["series"][0]["serie"] = {
                    p: "1" for p in spec["periodos"].split("|")
                }
            variables.append(variable)
        return variables

    extractor.get_pnad.side_effect = payload
    result = extract_project("test-run", extractor)
    assert {int(d["tabela"]) for d in result} == set(TABELAS_PNAD_PROJETO)
    extractor.get_pnad.side_effect = None
    extractor.get_pnad.return_value = []
    with pytest.raises(ValueError):
        extract_project("test-run", extractor)


def test_partial_http_200_payload_rejected(documents):
    from src.pipeline import validate_project_response

    with pytest.raises(ValueError, match="variáveis"):
        validate_project_response(documents[0], TABELAS_PNAD_PROJETO[9468])


def test_invalid_extraction_never_reaches_bronze():
    config = PipelineConfig("test", "bronze", "public", "silver")
    with (
        patch("src.pipeline.preflight"),
        patch("src.pipeline.extract_project", side_effect=ValueError("incompleta")),
        patch("src.pipeline.write_bronze") as write,
        pytest.raises(ValueError),
    ):
        run_project(config)
    write.assert_not_called()


def test_legacy_collection_cannot_be_used_as_new_bronze():
    with pytest.raises(ValueError, match="separada"):
        PipelineConfig("ibge_database", "pnad_extractions", "public", "silver")


def test_mongo_constructor_failure_does_not_log_credentials():
    import traceback

    from pymongo.errors import ConfigurationError

    from src.pipeline import with_bronze

    with (
        patch(
            "src.pipeline.Mongo", side_effect=ConfigurationError("secret-test-password")
        ),
        pytest.raises(RuntimeError) as error,
    ):
        with_bronze(
            PipelineConfig("test", "bronze", "public", "silver"), lambda store: None
        )
    assert "secret-test-password" not in "".join(
        traceback.format_exception(error.value)
    )


def test_postgres_failure_does_not_log_credentials(monkeypatch):
    import traceback

    from sqlalchemy.exc import OperationalError

    from src.pipeline import load_silver

    monkeypatch.setenv("DATABASE_URL", "postgresql://user:secret-test-password@host/db")
    with (
        patch(
            "src.pipeline.postgres_engine",
            side_effect=OperationalError("SQL", {}, Exception("secret-test-password")),
        ),
        pytest.raises(RuntimeError) as error,
    ):
        load_silver(PipelineConfig("test", "bronze", "public", "silver"), None)
    assert "secret-test-password" not in "".join(
        traceback.format_exception(error.value)
    )
