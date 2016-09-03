
REDIS_CONFIG = {'redis_host': 'redis1',
                'redis_port': 6379,
                'redis_pass': None}

flask_cache_config = {'CACHE_TYPE': 'redis',
                      'CACHE_REDIS_HOST': REDIS_CONFIG['redis_host'],
                      'CACHE_REDIS_PORT': REDIS_CONFIG['redis_port'],
                      'CACHE_REDIS_PASSWORD': REDIS_CONFIG['redis_pass'],
                      'CACHE_REDIS_DB': 0}

APP_CONFIG = {'flask_cache_config': flask_cache_config,
              'flask_debug': True,
              'flask_host': "0.0.0.0",
              'flask_port': 8080}
