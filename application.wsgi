import os, sys
sys.path.append(os.path.join(os.path.dirname(__file__), "lib"))

import app
application = app.bootstrap()
