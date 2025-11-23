from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from zoneinfo import ZoneInfo
import logging

# Importamos a função que faz o trabalho pesado (criaremos ela no passo 2)
from app.services.product_updater import update_all_products

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()

async def update_prices_job():
    """Tarefa agendada: roda às 03:00 e 15:00."""
    logger.info("--- Iniciando Atualização Agendada (03:00 / 15:00) ---")
    try:
        await update_all_products()
        logger.info("--- Atualização Agendada Concluída ---")
    except Exception as e:
        logger.error(f"--- Erro na Atualização Agendada: {e} ---")

def start_scheduler():
    """Configura e inicia o agendador."""
    # Roda às 3h e às 15h (Horário de Brasília)
    trigger = CronTrigger(
        hour='3,15', 
        minute=0, 
        timezone=ZoneInfo("America/Sao_Paulo")
    )
    
    scheduler.add_job(update_prices_job, trigger=trigger)
    scheduler.start()
    logger.info("Agendador iniciado: Cron configurado para 03:00 e 15:00.")