SELECT * FROM fingerprint

    (bit_count(fingerprint_s # :s)
            + :a * abs(fingerprint_r-:r))
    as distance


ORDER BY distance
LIMIT 20;
