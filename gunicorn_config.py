bind = ':5000'
workers = 4 
worker_class = 'gevent'
errorlog = '/var/log/hgprofiler_gunicorn_error.log'
loglevel = 'info'
accesslog = '/var/log/hgprofiler_gunicorn_access.log'
