import os
os.environ['DJANGO_SETTINGS_MODULE'] = "gtfs.settings_production"

bind = 'localhost:9088'
daemon = True
user = 'nobody'
group = 'nogroup'

pidfile = './gunicorn.pid'

workers = 2
max_requests = 100

# worker_class = 'gevent'

# accesslog = '/var/log/gunicorn/access.log'
# errorlog = '/var/log/gunicorn/error.log'
