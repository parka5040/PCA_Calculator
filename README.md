# PCA_Calculator
PCA calculator for running and visualizing 2 or 3D PCA results.

To run:
- Ensure that Python 3.12.4 is installed and on the PATH
- Make sure that pip is installed if you want the batch file to automatically install dependencies
- If you don't want to install dependencies automatically, run: pca_run.bat -s or pca_run.bat --skip-install
- It will display the GUI

To use:
- Load in numerical data (the iris dataset is what was used to test it)
- Select the column headers to include in PCA analysis
- Drag and drop the column you want to use as a label for visualization (optional)
- Either click Run PCA for just the PC values and variance calcluations or run Visualize PCA to open the non-interactive 2D plot or the interactive 3D plot