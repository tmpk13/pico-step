# DigiKey order list

Import `digikey_list.csv` into a DigiKey list (Quantity, Part Number = MPN).
Matching by MPN lets DigiKey offer cut tape for prototype quantities.
40 lines, 84 parts.

Notes:
- SC1511-A4 is the RP2354A (A4 stepping) 500-piece reel; SC1511(13)-A4 is the 3400-piece reel.
- L1 must be the polarity-marked AOTA-B201610S3R3-101-T; a generic 3.3u has no marked
  orientation, and the RP2350 regulator is sensitive to it.
- Stock was last checked for the ICs and connectors (BOM.md, 2026-10-02), for
  the passives shared with the ESP32-C5 variant (2026-10-04) and for the
  TMC5160 stage (2026-10-11). RC0603FR-0727RL, RC0603FR-071KL,
  RC0603FR-074K7L, RC0603FR-075K6L, RC0603FR-0747RL, RC0603FR-072R2L and
  CC0603JRNPO9BN150 were not searched.
- Only reel packaging was returned by the search for most passives; cut tape
  numbers use the same base number with `-1-ND` (Murata, Samsung) or `CT-ND` (Yageo).
- GRM188R71H104KA93D and GRM21BR61A106KE19L are obsolete; replaced by
  GCM188R71H104KA57D and CL21B106KOQNNNE.
- C19 and C35 (Rubycon 63SGV100M10X10.5, 10 x 10.5 mm) match the
  CP_Elec_10x10.5 footprint; the 50 V Nichicon part was too low for 48 V.
- The first 2.2u 100V 1210 choices (Murata GRM32ER72A225KA35L, TDK
  C3225X7R2A225M230AB) are Not For New Designs; KEMET C1210C225K1RACTU is
  active. CL21A106KAYNNNE (10u 25V 0805) had 63 in stock, so C25 is the
  1206 X7R GRM31CR71E106KA12L, which also keeps more capacitance at 12 V.
