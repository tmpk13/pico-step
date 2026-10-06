# DigiKey order list

Import `digikey_list.csv` into a DigiKey list (Quantity, Part Number = MPN).
Matching by MPN lets DigiKey offer cut tape for prototype quantities.
30 lines, 56 parts.

Notes:
- SC0914(13) is the RP2040 reel number; DigiKey also lists smaller packs of the same part.
- Stock was last checked for the ICs and connectors (BOM.md, 2026-10-02) and for
  the passives shared with the ESP32-C5 variant (2026-10-04). RC0603FR-0727RL,
  RC0603FR-071KL, RC0603FR-074K7L and CC0603JRNPO9BN150 were not searched.
- Only reel packaging was returned by the search for most passives; cut tape
  numbers use the same base number with `-1-ND` (Murata, Samsung) or `CT-ND` (Yageo).
- GRM188R71H104KA93D and GRM21BR61A106KE19L are obsolete; replaced by
  GCM188R71H104KA57D and CL21B106KOQNNNE.
- C19 (Nichicon UWT1H101MNL1GS) is a 10 mm can; check height and land pattern
  against the CP_Elec_10x10.5 footprint.
