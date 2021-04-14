import os, sys, unittest

loader = unittest.TestLoader()
start_dir = os.path.dirname(os.path.realpath(__file__))
suite = loader.discover(start_dir=start_dir, pattern='*_test.py')
runner = unittest.TextTestRunner()

ret = not runner.run(suite).wasSuccessful()
sys.exit(ret)
