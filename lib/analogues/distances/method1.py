
"""

hamming() + alpha * abs(ref1 - ref2)


"""
from .method import Method


class Method1(Method):

    bounds = (0, 1)

    def __init__(self, f):
        super().__init__(f)

    def fingerprint_distance(self, r1, s1, r2, s2, alpha):
        s = self.hamming(s1, s2)
        r = self.absdiff(r1, r2)
        return (1 - alpha) * (1 - alpha) * s + alpha * alpha * r

    def sql_text(self, table, limit, order):
        return """

        SELECT valid_date,
               (hamming_distance(fingerprint_s, :fingerprint_s) / 16.0) * (1.0 - ({alpha})) * (1.0 - ({alpha}))
           + abs((fingerprint_r-{offset})/{scale} - (:fingerprint_r-{offset})/{scale}) * {alpha} * {alpha}
        AS distance

        FROM     {table}
        WHERE    fingerprint_r IS NOT NULL
        AND      fingerprint_s IS NOT NULL
        AND      file_id       IS NOT NULL
        ORDER BY distance      {order}
        LIMIT    {limit}

        """.format(table=table,
                   alpha=self.alpha,
                   offset=self.offset,
                   scale=self.scale,
                   limit=limit,
                   order=order)
