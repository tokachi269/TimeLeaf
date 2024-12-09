import sys
import os
import logging

# プロジェクトのパスを追加
sys.path.insert(0, os.path.dirname(__file__))
logging.basicConfig(stream = sys.stderr)

from main import app as application