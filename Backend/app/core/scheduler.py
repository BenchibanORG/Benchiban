from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from zoneinfo import ZoneInfo
from datetime import datetime
import logging

# Importamos a função que faz o trabalho pesado
from app.services.product_updater import update_all_products

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()

async def update_prices_job():
    """Tarefa agendada: roda às 03:00 e 15:00."""
    now = datetime.now(ZoneInfo("America/Sao_Paulo"))
    logger.info(f"--- Iniciando Atualização Agendada: {now} ---")
    try:
        await update_all_products()
        logger.info("--- Atualização Agendada Concluída com Sucesso ---")
    except Exception as e:
        logger.error(f"--- Erro CRÍTICO na Atualização Agendada: {e} ---")

def start_scheduler():
    """Configura e inicia o agendador."""
    # Definição do Fuso Horário
    tz = ZoneInfo("America/Sao_Paulo")
    
    #Tempo de tolerância
    trigger = CronTrigger(
        hour='3,15', 
        minute=0, 
        timezone=tz
    )
    
    # Adicionamos misfire_grace_time
    scheduler.add_job(
        update_prices_job, 
        trigger=trigger, 
        misfire_grace_time=3600, # <--- LINHA NOVA IMPORTANTE
        id="price_update_job",
        replace_existing=True
    )
    
    scheduler.start()
    
    # Log informativo para debug
    next_run = trigger.get_next_fire_time(None, datetime.now(tz))
    logger.info(f"Agendador iniciado. Próxima execução prevista para: {next_run} (Horário de Brasília)")