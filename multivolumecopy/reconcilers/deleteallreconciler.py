"""
"""
import os
import logging
from multivolumecopy.reconcilers import reconciler


logger = logging.getLogger(__name__)


class DeleteAllReconciler(reconciler.Reconciler):
    """ Simplest possible reconciler. Deletes all files from dst.
    (everything will be recopied every time).
    """
    def __init__(self, source, options):
        super(DeleteAllReconciler, self).__init__(source, options)

    def reconcile(self, copyfiles, copied_indexes):
        # delete files
        for (root, dirnames, filenames) in os.walk(self.options.output):
            for filename in filenames:
                filepath = os.path.abspath('{}/{}'.format(root, filename))
                os.remove(filepath)

        # delete directories
        for (root, dirnames, filenames) in os.walk(self.options.output):
            for dirname in dirnames:
                dirpath = os.path.abspath('{}/{}'.format(root, dirname))
                os.rmdir(dirpath)

