from sandbox.oscar.apps.catalogue import (
    ServiceDetailView as OscarServiceDetailView)


class ParentServiceDetailView(OscarServiceDetailView):
    enforce_parent = True
    enforce_paths = False
