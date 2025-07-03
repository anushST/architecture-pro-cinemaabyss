import asyncio
import logging
import uvicorn
from fastapi import FastAPI
from fastapi.responses import RedirectResponse

from src.core.config import settings, LOGGING_CONFIG

logging.config.dictConfig(LOGGING_CONFIG)
logger = logging.getLogger(__name__)

app = FastAPI()

requests_count = {
    'health': 0,
    'movies': 0,
    'users': 0
}




@app.get('/health')
async def health():
    requests_count['health'] += 1
    return RedirectResponse(url=settings.MONOLITH_URL + '/health')

@app.get('/api/movies')
async def movies():
    chance = int(100 / settings.MOVIES_MIGRATION_PERCENT)
    requests_count['movies'] += 1
    if requests_count['movies'] % chance == 0:
        return RedirectResponse(url=settings.MOVIES_SERVICE_URL + '/api/movies')
    else:
        return RedirectResponse(url=settings.MONOLITH_URL + '/api/movies')
    

@app.get('/api/users')
async def users():
    requests_count['users'] += 1
    return RedirectResponse(url=settings.MONOLITH_URL + '/api/users')

async def main():
    config = uvicorn.Config('main:app', host='0.0.0.0',
                            port=settings.PORT, reload=True,
                            log_config=None)
    server = uvicorn.Server(config)
    await server.serve()


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info('Server stopped manually.')
    except Exception as e:
        logger.critical(f'Critical error in application: {e}', exc_info=True)
