# ExDFinder - ChimeraX Plugin

ExDFinder is a plugin for UCSF ChimeraX designed to highlight regions within a target peptide or protein sequence that lack supporting fragment ion evidence in ExDViewer's analysis results.

## Features

*   **Residue Highlighting:** Identifies and highlights residues in a selected molecular model.
*   **CSV Input:** Support the exported csv from ExDViewer. 
*   **Customizable Colors:** Allows users to select custom colors for the background and highlighted residues.
*   **Processing Modes:** Supports "Monomer" and "Dimer" modes for processing and highlighting.

## Installation

1.  Clone the repository:
    ```bash
    git clone https://github.com/TerryZhang175/ExDFinder-for-ChimeraX.git
    ```
2.  Open ChimeraX.
3.  In the ChimeraX command line, enter the following command, replacing `"/path/to/ExDFinder-for-ChimeraX"` with the actual path to the cloned directory:
    ```
    devel install "/path/to/ExDFinder-for-ChimeraX"
    ```
4.  Restart ChimeraX if prompted.
