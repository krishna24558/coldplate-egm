# Validation

**Dataset:** W. Qu and I. Mudawar (2002), *Experimental and numerical study of pressure drop and heat transfer in a single-phase micro-channel heat sink*, Int. J. Heat Mass Transfer 45, 2549–2565.
Free PDF: https://engineering.purdue.edu/mudawar/files/articles-all/2002/2002_1.pdf

Copper heat sink, 21 rectangular channels, 231 µm wide × 713 µm deep, deionized water.

## Steps

1. Read the paper's test-section and test-matrix sections. Fill `data/qu_mudawar_geometry.csv` with every dimension (channel width/depth, wall thickness, channel length, base thickness, heated area).
2. Record test conditions (inlet temperature, flow rate or Re, heat input).
3. Digitize measured pressure drop vs. Re and measured temperatures (or Nu / thermal resistance) from the figures with WebPlotDigitizer: https://automeris.io/WebPlotDigitizer
4. Save points to `data/qu_mudawar_dP.csv` and `data/qu_mudawar_thermal.csv` (note the figure number in each file).
5. In `validation.ipynb`, run the model at the same conditions, plot predicted vs. measured, report MAPE.

Every value you take from the paper: note the page, table or figure.
