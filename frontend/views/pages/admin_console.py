# Streamlit page entry for the admin console - every module lives in ../admin_dashboard.py.
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import admin_dashboard

admin_dashboard.render()
