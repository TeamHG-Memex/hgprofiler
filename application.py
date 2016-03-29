import os, sys
sys.path.append(os.path.join(os.path.dirname(__file__), "lib"))

def run(environ, start_response):
    import app
    application = app.bootstrap()
    return application

