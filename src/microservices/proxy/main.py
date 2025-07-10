import asyncio
import logging
import logging.config
from typing import Optional

from fastapi import FastAPI, Request, HTTPException, Response
import aiohttp
import uvicorn

from src.core.config import settings, LOGGING_CONFIG

logging.config.dictConfig(LOGGING_CONFIG)
logger = logging.getLogger(__name__)

app = FastAPI()
requests_count: dict[str, int] = {
    'movies': 0, 'users': 0, 'payments': 0, 'subscriptions': 0,
}


def need_new_backend(counter_name: str, percent: int) -> bool:
    if not settings.GRADUAL_MIGRATION or percent <= 0:
        return False
    requests_count[counter_name] += 1
    chance = 100 // percent
    return requests_count[counter_name] % chance == 0


async def proxy(
    method: str,
    path: str,
    counter: str,
    new_backend: Optional[str] = None,
    migration_percent: Optional[int] = 0,
    json: Optional[dict] = None,
    ok_codes: tuple[int, ...] = (200,),
) -> Response:
    to_new = need_new_backend(counter, migration_percent)
    base_url = new_backend if to_new else settings.MONOLITH_URL
    url = f'{base_url}{path}'

    async with aiohttp.ClientSession() as session, session.request(
        method, url, json=json
    ) as resp:
        if resp.status not in ok_codes:
            raise HTTPException(resp.status, await resp.text())

        data = await resp.read()
        return Response(
            content=data,
            media_type=resp.headers.get('content-type'),
            status_code=resp.status,
            headers={k: v for k, v in resp.headers.items() if k.lower() not in {
                'content-length', 'transfer-encoding', 'connection'}
            },
        )


@app.get('/health')
async def health():
    return {'status': True}


@app.get('/api/movies')
async def movies(id: Optional[int] = None):
    url = '/api/movies'
    if id:
        url = url + f'?id={id}'
    return await proxy('GET', url,
                       new_backend=settings.MOVIES_SERVICE_URL,
                       migration_percent=settings.MOVIES_MIGRATION_PERCENT,
                       counter='movies')


@app.post('/api/movies', status_code=201)
async def create_movie(request: Request):
    payload = await request.json()
    return await proxy(
        'POST',
        '/api/movies',
        new_backend=settings.MOVIES_SERVICE_URL,
        migration_percent=settings.MOVIES_MIGRATION_PERCENT,
        counter='movies',
        json=payload,
        ok_codes=(200, 201),
    )


@app.get('/api/users')
async def users(id: Optional[int] = None):
    url = f'/api/users'
    if id:
        url = url + f'?id={id}'
    return await proxy('GET', url, counter='users')


@app.post('/api/users', status_code=201)
async def create_user(request: Request):
    payload = await request.json()
    return await proxy(
        'POST',
        '/api/users',
        counter='users',
        json=payload,
        ok_codes=(200, 201),
    )


@app.get('/api/payments')
async def payments(id: Optional[int] = None):
    url = '/api/payments'
    if id:
        url = url + f'?id={id}'
    return await proxy('GET', url, counter='payments')


@app.post('/api/payments', status_code=201)
async def create_payment(request: Request):
    payload = await request.json()
    return await proxy(
        'POST',
        '/api/payments',
        counter='payments',
        json=payload,
        ok_codes=(200, 201),
    )


@app.get('/api/subscriptions')
async def subscriptions(id: Optional[int] = None):
    url = '/api/subscriptions'
    if id:
        url = url + f'?id={id}'
    return await proxy('GET', url, counter='subscriptions')


@app.post('/api/subscriptions', status_code=201)
async def create_subscription(request: Request):
    payload = await request.json()
    return await proxy(
        'POST',
        '/api/subscriptions',
        counter='subscriptions',
        json=payload,
        ok_codes=(200, 201),
    )


async def main():
    config = uvicorn.Config(
        'main:app',
        host='0.0.0.0',
        port=settings.PORT,
        reload=True,
        log_config=None,
    )
    server = uvicorn.Server(config)
    await server.serve()


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info('Server stopped manually.')
    except Exception as e:
        logger.critical(f'Critical error in application: {e}', exc_info=True)
