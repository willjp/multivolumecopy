"""
"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
import os
import logging
from multivolumecopy.reconcilers import reconciler


logger = logging.getLogger(__name__)


class DeleteAllReconciler(reconciler.Reconciler):
    """ Simplest possible reconciler. Deletes all files from dst.
    (everything will be recopied every time).
    """
    def __init__(self, copyfiles, options):
        """ Constructor.

        Args:
            source (resolver.Resolver):
                CopySource object, determines files to be copied.

            options (copyoptions.CopyOptions):
                Options to use while performing copy
        """
        super(DeleteAllReconciler, self).__init__(copyfiles, options)

    def calculate(self, copyfiles, copied_indexes):
        filepaths = []
        for (root, _, filenames) in os.walk(self.options.output):
            for filename in filenames:
                filepath = os.path.abspath('{}/{}'.format(root, filename))
                filepaths.append(filepath)
        return set(filepaths)

