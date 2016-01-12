import os, sys
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "lib"))

from cli.database import DatabaseCli
DatabaseCli().run()
