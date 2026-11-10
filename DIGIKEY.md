# DigiKey order list

Import `digikey_list.csv` into a DigiKey list (Quantity, Part Number = MPN).
Matching by MPN lets DigiKey offer cut tape for prototype quantities.
35 lines, 63 parts per board; the quantities are per board.

Notes:
- Every line was checked on DigiKey on 2026-11-09 for a 5-board run: all
  Active, all sold in quantity 1 (cut tape; J2, J3 and J4 as Bulk), all with
  stock for 5 boards. The lowest margins were RC0603FR-0733RL (4993),
  GRM21BZ71C106ME15L (1432) and CL10B223KC8WPNC (3330).
- SC1511-A4 is the RP2354A (A4 stepping) 500-piece reel; SC1511(13)-A4 is the 3400-piece reel.
- L1 must be the polarity-marked AOTA-B201610S3R3-101-T; a generic 3.3u has no marked
  orientation, and the RP2350 regulator is sensitive to it.
- U5 is TMC5241ATU+T, which DigiKey sells as cut tape (2314 in stock,
  $12.79 each at 1, $10.05 at 10). TMC5241ATU+ is the same part in trays.
- C11 and C12 are 4.7u (GRM188R61E475KE11D), as in `tsch/mcu.tsch` and
  RP2350 data sheet 6.3.8.
- Eight parts had no DigiKey stock in any packaging on 2026-11-09 and were
  replaced by same-package, same-rating parts:
  - Yageo RC0603FR-07 10k, 330R, 100R and 100k: the same RC0603FR resistor
    with reel code -13 (10k, 330R) or -10 (100R, 100k). RC0603FR-13100KL
    had only 2 in stock.
  - C21, C22: GRM188R72A104KA35D -> GCJ188R72A104KA01D (Murata soft
    termination, 100n 100V X7R 10%).
  - C23: CL10B105KA8NNNC -> CL10B105KA8VPNC (1u 25V X7R 10%).
  - C24: GRM188R72A223KAC4D -> Samsung CL10B223KC8WPNC (22n 100V X7R 10%).
  - C2: CL21B106KOQNNNE -> Murata GRM21BZ71C106ME15L, 20% instead of 10%
    (no 10% 10u 16V X7R 0805 was in stock; GRM21BZ71C106KE15L had none).
    C2 is the AP2112K output capacitor, where 20% is fine.
- Parts rejected earlier as obsolete or Not For New Designs, not to be
  picked again: GRM188R71E105KA12D, GRM188R71H104KA93D, GRM21BR61A106KE19L,
  Murata GRM32ER72A225KA35L, TDK C3225X7R2A225M230AB.
- C19 and C35 (Rubycon 63SGV100M10X10.5, 10 x 10.5 mm) match the
  CP_Elec_10x10.5 footprint; the 50 V Nichicon part was too low for 48 V.
