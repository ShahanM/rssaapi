from .admin.main import api as admin_api
from .demo.main import api as demo_api
from .study.main import api as study_api

admin_api = admin_api
demo_api = demo_api
study_api = study_api
__all__ = ['admin_api', 'demo_api', 'study_api']
