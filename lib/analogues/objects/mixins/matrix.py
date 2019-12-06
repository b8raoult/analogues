class FieldMatrix:

    def __init__(self):
        self.ONCE = True
        self.UPDATE_DISTANCES = False
        self._distance_matrix = None
        self._distance_matrix_path = None
        self._distance_table = None
        self._training_matrix = None

    @property
    def distance_matrix(self):

        if self._training_matrix is not None:
            if self.ONCE:
                print("WARNING: Using training matrix as distance matrix")
                self.ONCE = False
            return self._training_matrix

        if self._distance_matrix is None:

            size = L2_DATES
            path = self.distance_path()
            if os.path.exists(path):
                if self.UPDATE_DISTANCES:
                    mode = 'r+'
                else:
                    mode = 'r'
            else:
                mode = 'w+'

            self._distance_matrix_path = path
            self._distance_matrix = np.memmap(path,
                                              dtype=np.float64,
                                              mode=mode,
                                              shape=(size, size))
            if mode == 'w+':
                self._distance_matrix[:] = np.inf

            count = (self._distance_matrix < np.inf).sum()
            print(path, 'Values {:,} out of {:,}'.format(count, self._distance_matrix.size))

        return self._distance_matrix
