# see pyctdev/__init__ imports for explanation of this file
import os
import sys
sys.path.insert(1,os.path.join(os.path.dirname(__file__),"tox-pep-518.zip"))
import tox

if __name__ == "__main__":
    tox.cmdline()
