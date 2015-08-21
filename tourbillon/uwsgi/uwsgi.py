import asyncio
import json
import logging


logger = logging.getLogger(__name__)


@asyncio.coroutine
def get_uwsgi_stats(agent):
    yield from agent.run_event.wait()
    config = agent.pluginconfig['uwsgi']
    logger.info('starting "get_uwsgi_stats" task for "%s"', config['hostname'])
    try:
        logger.debug('try to create the database...')
        yield from agent.async_create_database('uwsgi')
        yield from agent.async_create_retention_policy('uwsgi_rp',
                                                       '365d',
                                                       '1',
                                                       'uwsgi')
        logger.info('database "%s" created successfully', 'uwsgi')
    except:
        pass
    workers_stats = None
    uwsgi_host = config['hostname']
    uwsgi_port = config['port']
    while agent.run_event.is_set():
        yield from asyncio.sleep(config['frequency'])
        logger.debug('open connection to uwsgi stats server')
        reader, writer = yield from asyncio.open_connection(uwsgi_host,
                                                            uwsgi_port)
        data = yield from reader.read()
        d = json.loads(data.decode('utf-8'))
        if workers_stats is None:
            logger.debug('first run, no previous statistics in memory')
            workers_stats = dict()
            for worker in d['workers']:
                workers_stats[worker['id']] = worker
            logger.debug('current statistcs: %s', workers_stats)
            continue
        ref_worker = d['workers'][0]
        stored_last_spawn = workers_stats[ref_worker['id']]['last_spawn']
        received_last_spawn = ref_worker['last_spawn']
        if stored_last_spawn != received_last_spawn:
            logger.warn('a restart of the uwsgi server "%" has been detected',
                        uwsgi_host)
            workers_stats = dict()
            for worker in d['workers']:
                workers_stats[worker['id']] = worker
            continue
        points = []
        for worker in d['workers']:
            logger.debug('process worker data...')
            stored_wk_data = workers_stats[worker['id']]
            requests = worker['requests'] - stored_wk_data['requests']
            exceptions = worker['exceptions'] - stored_wk_data['exceptions']
            tx = worker['tx'] - stored_wk_data['tx']
            points.append({
                'measurement': 'uwsgi_stats',
                'tags': {
                    'host': config['hostname'],
                    'worker': worker['id']
                },
                'fields': {
                    'requests': requests,
                    'exceptions': exceptions,
                    'tx': tx,
                    'rss': worker['rss'],
                    'vsz': worker['vsz'],
                    'avg_rt': worker['avg_rt'],
                    'wid': worker['id'],
                    'status': worker['status']
                }
            })
            workers_stats[worker['id']] = worker
        yield from agent.async_push(points, 'uwsgi')
    logger.info('get_uwsgi_stats terminated')
