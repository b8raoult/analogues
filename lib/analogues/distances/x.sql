SELECT valid_date,

(CASE WHEN hamming_distance(fingerprint_s, %(fingerprint_s)s) > 0
  THEN (hamming_distance(fingerprint_s, %(fingerprint_s)s) / 16.0 * (1.0 - 0.5))
  ELSE (abs( ( fingerprint_r-0.0)/0.0206432 -
             (%(fingerprint_r)s-0.0)/0.0206432)
           ) * 0.5
        )
  END)
                                                                             AS distance

                                                                                    FROM     fingerprint_tp_uk_era5

                                                                                          WHERE    fingerprint_r IS NOT NULL
                                                                                                 AND      fingerprint_s IS NOT NULL\n        AND      file_id       IS NOT NULL\n        ORDER BY distance      ASC\n        LIMIT    100\n\n
