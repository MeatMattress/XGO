import time
from xgolib import XGO
from xgoedu import XGOEDU
xgo=XGO("xgolite")
XGO_edu = XGOEDU()
xgo.move_x(15)
time.sleep(5)
xgo.move_x(0)