# See http://www.inference.phy.cam.ac.uk/bayesys/test/hilbert.c


def make_bits(no_bits, dimensions, n):
    bits = [0] * dimensions
    i = dimensions - 1
    while i >= 0:
        for j in range(0, no_bits):
            bits[i] |= (n & 1) << j
            n >>= 1
        i -= 1
    return bits


class HilbertCoordinates(object):

    def __init__(self, no_bits, bits):
        self.no_bits = no_bits
        self.bits = bits

    def __repr__(self):
        return "C[" + ",".join([str(b) for b in self.bits]) + "]"


class HilbertNumber(object):

    def __init__(self, no_bits, bits):
        self.no_bits = no_bits
        self.bits = bits

    @property
    def number(self):
        n = self.no_bits
        value = 0
        for b in self.bits:
            value <<= n
            value |= b

        return value

    def __repr__(self):
        return repr(self.number)

    def __sub__(self, other):
        return self.number - other.number


class HilbertCurve(object):

    def __init__(self, dimensions, no_bits):
        self.dimensions_ = dimensions
        self.no_bits = no_bits

    def number_to_coordinates(self, line):
        if self.dimensions_ <= 1:
            return HilbertCoordinates(line)

        return HilbertCoordinates(self.no_bits, self.transpose_to_axes(self.line_to_transpose(line.bits)))

    def coordinates_to_number(self, coord):
        if self.dimensions_ <= 1:
            return HilbertNumber(coord)

        return HilbertNumber(self.no_bits, self.transpose_to_line(self.axes_to_transpose(coord.bits)))

    def line_to_transpose(self, line):

        n = self.dimensions_
        X = [0] * n

        M = 1 << (self.no_bits - 1)

        q = 0
        p = M
        for i in range(0, n):
            j = M
            while j > 0:
                if (line[i] & j) != 0:
                    X[q] |= p

                q += 1
                if q == n:
                    q = 0
                    p >>= 1

                j >>= 1

        return X

    def transpose_to_line(self, X):
        n = self.dimensions_
        line = [0] * n

        M = 1 << (self.no_bits - 1)
        q = 0
        p = M
        for i in range(0, n):
            j = M
            while j > 0:
                if (X[q] & p) != 0:
                    line[i] |= j

                q += 1
                if q == n:
                    q = 0
                    p >>= 1
                j >>= 1

        return line

    def transpose_to_axes(self, X):
        n = self.dimensions_

        # Gray decode by H ^ (H/2)
        t = X[n - 1] >> 1

        i = n - 1
        while i > 0:
            X[i] ^= X[i - 1]
            i -= 1

        X[0] ^= t

        # Undo excess work
        M = 2 << (self.no_bits - 1)
        Q = 2
        while Q != M:
            P = Q - 1
            i = n - 1
            while i > 0:
                if ((X[i] & Q) != 0):
                    X[0] ^= P  # invert
                else:
                    t = (X[0] ^ X[i]) & P
                    X[0] ^= t
                    X[i] ^= t
                # exchange

                i -= 1

            if ((X[0] & Q) != 0):
                X[0] ^= P  # invert

            Q <<= 1

        return X

    def axes_to_transpose(self, axis):
        n = self.dimensions_
        X = [a for a in axis]

        # Inverse undo
        Q = 1 << (self.no_bits - 1)
        while Q > 1:
            P = Q - 1
            if (X[0] & Q) != 0:
                X[0] ^= P  # invert
            for i in range(1, n):
                if (X[i] & Q) != 0:
                    X[0] ^= P  # invert
                else:
                    t = (X[0] ^ X[i]) & P
                    X[0] ^= t
                    X[i] ^= t
                # exchange

            Q >>= 1

        # Gray encode (inverse of decode)
        for i in range(1, n):
            X[i] ^= X[i - 1]

        t = X[n - 1]
        i = 1
        b = self.no_bits
        while i < b:
            X[n - 1] ^= X[n - 1] >> i
            i <<= 1

        t ^= X[n - 1]
        i = n - 2
        while i >= 0:
            X[i] ^= t
            i -= 1

        return X

    def new_number(self, n):
        return HilbertNumber(self.no_bits, make_bits(self.no_bits, self.dimensions_, n))

    def new_coordinates(self, *args):
        return HilbertCoordinates(self.no_bits, args)


def distance(a, b, no_bits, ascale, aoffset, bscale, boffset):
    print ascale, aoffset
    a = ((a-aoffset) * ascale).flatten()
    a = a.astype(int)
    b = ((b-boffset) * bscale).flatten()
    b = b.astype(int)

    c = HilbertCurve(len(a), no_bits)
    na = c.coordinates_to_number(HilbertCoordinates(no_bits, a))
    nb = c.coordinates_to_number(HilbertCoordinates(no_bits, b))

    return abs(na - nb)


if __name__ == "__main__":

    curve = HilbertCurve(2, 4)

    for i in range(0, 256):
        number1 = curve.new_number(i)
        coord = curve.number_to_coordinates(number1)
        number2 = curve.coordinates_to_number(coord)
        print i, number1, coord, number2

    for i in range(0, 16):
        for j in range(0, 16):
            coord = curve.new_coordinates(i, j)
            number = curve.coordinates_to_number(coord)
            print coord, number

        # for (int i = 0; i < 16; i++) {
        #     for (int j = 0; j < 16; j++) {
        #         HilbertCoordinates coord = curve.newCoordinates(i, j);
        #         System.out.println(coord);
        #         HilbertNumber bar = curve.coordinatesToNumber(coord);
        #         System.out.println(curve.numberToCoordinates(bar));
        #     }
        # }
