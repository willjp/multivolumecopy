from multivolumecopy.resolvers import jobfileresolver


class Verifier(object):
    def __init__(self, options):
        self.options = options

    def verify_files(self, device_start_index, last_copied_index):
        """ Find all jobfile paths missing within provided range.
        """
        resolver = jobfileresolver.JobFileResolver(self.options.jobfile, self.options)
        copyfiles = resolver.get_copyfiles(device_start_index)
        #for copyfile in copyfiles[:last_copied_index]:
        #    if all([lambda: os.path.isfile(copyfile.dst),
        #            lambda: os.path.g

    def verify_avail_bytes(self, output, device_padding=None):
        """ Return the estimated free space (excluding backup, and constrainted to backup directory).
        """
        pass


