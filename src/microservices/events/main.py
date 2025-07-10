import asyncio
import logging
import json
import logging.config
from datetime import datetime

import uvicorn
from aiokafka import AIOKafkaProducer, AIOKafkaConsumer
from fastapi import FastAPI

from src.core.config import settings, LOGGING_CONFIG

logging.config.dictConfig(LOGGING_CONFIG)

logger = logging.getLogger(__name__)

app = FastAPI()

KAFKA_BOOTSTRAP = settings.KAFKA_BROKERS
TOPICS = {
    'movie':   'events.movie',
    'user':    'events.user',
    'payment': 'events.payment',
}

async def publish(topic: str, payload: dict) -> None:
    producer = AIOKafkaProducer(
        bootstrap_servers=KAFKA_BOOTSTRAP,
        acks='all',
        linger_ms=5,
    )
    await producer.start()
    msg = json.dumps(
        {'ts': datetime.now().isoformat(timespec='seconds'), **payload},
    ).encode()
    await producer.send_and_wait(topic, msg)
    logger.info('Sent to %s %s', topic, payload)
    await producer.stop()


@app.get('/api/events/health', status_code=200)
async def health():
    return {'status': True}


@app.post('/api/events/movie', status_code=201)
async def movie():
    await publish(TOPICS['movie'], {'event': 'MOVIE'})
    return {'status': 'success'}


@app.post('/api/events/user', status_code=201)
async def user():
    await publish(TOPICS['user'], {'event': 'USER'})
    return {'status': 'success'}


@app.post('/api/events/payment', status_code=201)
async def payment():
    await publish(TOPICS['payment'], {'event': 'PAYMENT'})
    return {'status': 'success'}


async def consume(group_id: str, topic: str, tag: str):
    consumer = AIOKafkaConsumer(
        topic,
        bootstrap_servers=KAFKA_BOOTSTRAP,
        group_id=group_id,
        auto_offset_reset='earliest',
        enable_auto_commit=False,
    )
    await consumer.start()
    try:
        async for msg in consumer:
            payload = json.loads(msg.value)
            logger.info(f'{tag} {msg.topic} {msg.partition} {msg.offset} {payload}')
            await consumer.commit()
    finally:
        await consumer.stop()


async def movie_evenet_consumer():
    await consume('movie-workers', TOPICS['movie'], 'MOVIE')


async def user_evenet_consumer():
    await consume('user-workers', TOPICS['user'], 'USER')


async def payment_evenet_consumer():
    await consume('payment-workers', TOPICS['payment'], 'PAYMENT')


async def main():
    asyncio.create_task(movie_evenet_consumer())
    asyncio.create_task(user_evenet_consumer())
    asyncio.create_task(payment_evenet_consumer())

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
