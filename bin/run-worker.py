import os, sys
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "lib"))

from cli.run_worker import RunWorkerCli
RunWorkerCli().run()
