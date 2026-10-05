# DigiKey order list

Import `digikey_list.csv` into a DigiKey list (Quantity, Part Number = MPN).
Matching by MPN lets DigiKey offer cut tape for prototype quantities.
41 lines, 67 parts (C33_rf and C34_rf are DNP and not ordered). Sourced 2026-10-04.

Notes:
- FL1_rf (LFD182G45DCHD481) is reel-only at DigiKey, MOQ 4000. Prototypes need another source.
- Only reel packaging was returned by the search for most passives; cut tape
  numbers use the same base number with `-1-ND` (Murata, Samsung) or `CT-ND` (Yageo).
- Order extra 0201 parts (C4, C5, C13, C14, C29_rf..C32_rf, L1, L3_rf, L4_rf, R18_rf). They are
  easy to lose and the RF values are starting points to be tuned.
- GRM188R71H104KA93D and GRM21BR61A106KE19L are obsolete; replaced by
  GCM188R71H104KA57D and CL21B106KOQNNNE.
- C19 (Nichicon UWT1H101MNL1GS) is a 10 mm can; check height and land pattern
  against the CP_Elec_10x10.5 footprint.
- Existing BOM.md values (stock, price) cover the ICs and connectors only.
