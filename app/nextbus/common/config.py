
flask_cache_config = {'CACHE_TYPE': 'redis',
                      'CACHE_REDIS_HOST': 'redis-1',
                      'CACHE_REDIS_PORT': 6379,
                      'CACHE_REDIS_PASSWORD': None,
                      'CACHE_REDIS_DB': 0}

APP_CONFIG = {'flask_cache_config': flask_cache_config,
              'flask_debug': True,
              'flask_host': "0.0.0.0",
              'flask_port': 8080,}

