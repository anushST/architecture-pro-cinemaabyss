import asyncio
import logging
import uvicorn
from fastapi import FastAPI

from src.core.config import settings

logger = logging.getLogger(__name__)

app = FastAPI()


async def main():

    config = uvicorn.Config('main:app', host='0.0.0.0',
                            port=settings.PORT, reload=True, log_config=None)
    server = uvicorn.Server(config)
    await server.serve()


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info('Server stopped manually.')
    except Exception as e:
        logger.critical(f'Critical error in application: {e}', exc_info=True)
