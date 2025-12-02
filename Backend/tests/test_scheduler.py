import pytest
import asyncio
from unittest.mock import patch, MagicMock, ANY
from datetime import datetime
from zoneinfo import ZoneInfo
from apscheduler.triggers.cron import CronTrigger

import app.core.scheduler as scheduler_module


@pytest.fixture(autouse=True)
def clean_scheduler():
    """Limpa o scheduler antes e depois de cada teste."""
    if scheduler_module.scheduler.running:
        scheduler_module.scheduler.shutdown()
    scheduler_module.scheduler.remove_all_jobs()
    yield
    if scheduler_module.scheduler.running:
        scheduler_module.scheduler.shutdown()

def test_start_scheduler_configures_job_correctly():
    """Testa se o job é adicionado com todos os parâmetros corretos."""
    mock_scheduler = MagicMock()
    mock_scheduler.running = False

    with patch.object(scheduler_module, "scheduler", mock_scheduler):
        with patch.object(scheduler_module, "update_prices_job"):
            scheduler_module.start_scheduler()

            # 1. add_job foi chamado
            mock_scheduler.add_job.assert_called_once()

            # 2. Pega argumentos da chamada
            args, kwargs = mock_scheduler.add_job.call_args

            # Função correta
            assert args[0] is scheduler_module.update_prices_job

            # Trigger
            trigger = kwargs["trigger"]
            assert isinstance(trigger, CronTrigger)

            # Verifica os campos do CronTrigger
            hour_field = next(f for f in trigger.fields if f.name == "hour")
            minute_field = next(f for f in trigger.fields if f.name == "minute")

            assert str(hour_field) in ["3,15", "{3,15}"]   # pode variar por versão
            assert str(minute_field) == "0"

            # Timezone é atributo direto, NÃO está em fields
            assert trigger.timezone == ZoneInfo("America/Sao_Paulo")

            # Parâmetros nomeados
            assert kwargs["misfire_grace_time"] == 3600
            assert kwargs["id"] == "price_update_job"
            assert kwargs["replace_existing"] is True

            # Scheduler iniciado
            mock_scheduler.start.assert_called_once()


def test_start_scheduler_is_idempotent():
    """Chamar start_scheduler() várias vezes não cria jobs duplicados."""
    mock_scheduler = MagicMock()
    mock_scheduler.running = False

    with patch.object(scheduler_module, "scheduler", mock_scheduler):
        with patch.object(scheduler_module, "update_prices_job"):
            scheduler_module.start_scheduler()
            scheduler_module.start_scheduler()

            assert mock_scheduler.add_job.call_count == 2
            assert mock_scheduler.start.call_count == 2  # tenta iniciar de novo (normal)


def test_update_prices_job_success_and_error_cases():
    """Testa log, chamada da função e tratamento de erro."""
    with patch.object(scheduler_module, "update_all_products") as mock_updater:
        with patch.object(scheduler_module.logger, "info") as mock_info:
            with patch.object(scheduler_module.logger, "error") as mock_error:

                # === CASO 1: Sucesso ===
                mock_updater.return_value = None  # Simula await sem erro

                asyncio.run(scheduler_module.update_prices_job())

                # Verifica logs com ANY (aceita o timestamp dinâmico)
                mock_info.assert_any_call(ANY)  # início
                mock_info.assert_any_call("--- Atualização Agendada Concluída com Sucesso ---")

                # Verifica se chamou a função
                mock_updater.assert_called_once()

                # Sem erro
                mock_error.assert_not_called()

                # Reset para próximo caso
                mock_info.reset_mock()
                mock_error.reset_mock()
                mock_updater.reset_mock()

                # === CASO 2: Erro na atualização ===
                mock_updater.side_effect = Exception("Erro de rede")

                asyncio.run(scheduler_module.update_prices_job())

                mock_info.assert_any_call(ANY)  # início com timestamp
                mock_error.assert_called_once_with(
                    "--- Erro CRÍTICO na Atualização Agendada: Erro de rede ---"
                )
                mock_updater.assert_called_once()