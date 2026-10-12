-- READ-ONLY source: prod_edw.dimension.dg5_customer_scd1
-- Customer 6-level hierarchy for multi-select + disaggregation grouping.
-- Output grain = mkedg5. Case variants exist in mkedg0 (normalize when grouping).
SELECT
  mkedg0, mkedg1, mkedg2, mkedg3, mkedg4, mkedg5, customer
FROM prod_edw.dimension.dg5_customer_scd1
ORDER BY mkedg0, mkedg1, mkedg2, mkedg3, mkedg4, mkedg5
