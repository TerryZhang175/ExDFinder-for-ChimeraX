# Tool implementation for ExDFinder

from chimerax.core.tools import ToolInstance
from chimerax.ui.gui import MainToolWindow
from Qt.QtWidgets import (
    QWidget, QPushButton, QLabel,
    QFileDialog, QVBoxLayout, QHBoxLayout, QComboBox, QColorDialog
)
from Qt.QtGui import QColor # Import QColor
from Qt.QtCore import Qt # Keep Qt import if needed for other UI elements
import os
import csv 

class ExDFinderTool(ToolInstance):
    """Tool to highlight residues based on CSV input and specific criteria."""
    
    # Let ChimeraX know about this tool
    SESSION_ENDURING = False
    SESSION_SAVE = False
    help = "help:user/tools/exdfinder.html"
    
    def __init__(self, session, tool_name):
        # 'session' is the current ChimeraX session
        # 'tool_name' is the name of the tool
        super().__init__(session, tool_name)
        
        # Initialize attributes
        self.residue_indices_from_csv = set()  # Stores residue indices loaded from the CSV file
        self.current_model = None  # Currently selected model
        self.background_color = QColor("silver") # Default background color
        self.highlight_color = QColor("blue") # Default highlight color
        
        # Create and display the UI
        self.tool_window = MainToolWindow(self)
        self._build_ui()
        self.tool_window.manage(None) # Manages the tool window (e.g. non-blocking)
    
    def _build_ui(self):
        # Create the main layout
        layout = QVBoxLayout()
        main_widget = QWidget()
        main_widget.setLayout(layout)
        
        # File loading section
        file_section = QWidget()
        file_layout = QHBoxLayout()
        file_section.setLayout(file_layout)
        
        self.load_button = QPushButton("Load CSV File")
        self.load_button.clicked.connect(self._load_file)
        self.file_label = QLabel("No file selected")
        
        file_layout.addWidget(self.load_button)
        file_layout.addWidget(self.file_label)
        layout.addWidget(file_section)
        
        # Model selection section
        model_section = QWidget()
        model_layout = QHBoxLayout()
        model_section.setLayout(model_layout)
        
        self.model_label = QLabel("Select Model:")
        self.model_selector = QComboBox()
        self.model_selector.currentIndexChanged.connect(self._model_changed)
        self.refresh_models_button = QPushButton("Refresh Models")
        self.refresh_models_button.clicked.connect(self._refresh_models)
        
        model_layout.addWidget(self.model_label)
        model_layout.addWidget(self.model_selector)
        model_layout.addWidget(self.refresh_models_button)
        layout.addWidget(model_section)

        # Color selection section
        color_section = QWidget()
        color_layout = QHBoxLayout()
        color_section.setLayout(color_layout)

        self.bg_color_button = QPushButton("Background Color")
        self.bg_color_button.clicked.connect(self._pick_background_color)
        self.bg_color_swatch = QLabel()
        self.bg_color_swatch.setFixedSize(20, 20) # Small square
        self.bg_color_swatch.setStyleSheet(f"background-color: {self.background_color.name()}; border: 1px solid black;")
        
        self.hl_color_button = QPushButton("Highlight Color")
        self.hl_color_button.clicked.connect(self._pick_highlight_color)
        self.hl_color_swatch = QLabel()
        self.hl_color_swatch.setFixedSize(20, 20) # Small square
        self.hl_color_swatch.setStyleSheet(f"background-color: {self.highlight_color.name()}; border: 1px solid black;")

        color_layout.addWidget(self.bg_color_button)
        color_layout.addWidget(self.bg_color_swatch)
        color_layout.addStretch() # Add some space
        color_layout.addWidget(self.hl_color_button)
        color_layout.addWidget(self.hl_color_swatch)
        layout.addWidget(color_section)

        # Mode selection section (Monomer/Dimer)
        mode_selection_section = QWidget()
        mode_selection_layout = QHBoxLayout()
        mode_selection_section.setLayout(mode_selection_layout)

        self.mode_label = QLabel("Processing Mode:")
        self.mode_selector = QComboBox()
        self.mode_selector.addItems(["Monomer", "Dimer"])
        self.mode_selector.setCurrentText("Monomer") # Default to Monomer

        mode_selection_layout.addWidget(self.mode_label)
        mode_selection_layout.addWidget(self.mode_selector)
        layout.addWidget(mode_selection_section)
        
        # Action button section
        button_section = QWidget()
        button_layout = QHBoxLayout()
        button_section.setLayout(button_layout)
        
        self.highlight_button = QPushButton("Highlight Residues")
        self.highlight_button.clicked.connect(self._highlight_residues)
        
        button_layout.addWidget(self.highlight_button)
        layout.addWidget(button_section)
        
        self.tool_window.ui_area.setLayout(layout)
        
        # Initialize UI state
        self._refresh_models()

    def _pick_background_color(self):
        """Open a color dialog to choose the background color."""
        color = QColorDialog.getColor(self.background_color, self.tool_window.ui_area, "Select Background Color")
        if color.isValid():
            self.background_color = color
            self.bg_color_swatch.setStyleSheet(f"background-color: {self.background_color.name()}; border: 1px solid black;")

    def _pick_highlight_color(self):
        """Open a color dialog to choose the highlight color."""
        color = QColorDialog.getColor(self.highlight_color, self.tool_window.ui_area, "Select Highlight Color")
        if color.isValid():
            self.highlight_color = color
            self.hl_color_swatch.setStyleSheet(f"background-color: {self.highlight_color.name()}; border: 1px solid black;")
    
    def _refresh_models(self):
        """Refresh the list of available models in the dropdown."""
        current_selection_data = None
        if self.model_selector.currentIndex() >= 0:
            current_selection_data = self.model_selector.currentData()

        self.model_selector.clear()
        from chimerax.atomic import AtomicStructure
        # Get all atomic structure models from the session
        atomic_models = [m for m in self.session.models if isinstance(m, AtomicStructure)]
        
        if not atomic_models:
            self.model_selector.addItem("No models found")
            self.model_selector.setEnabled(False)
            self.current_model = None
            return
        
        self.model_selector.setEnabled(True)
        new_current_index = -1
        for i, model in enumerate(atomic_models):
            self.model_selector.addItem(f"{model.id_string}: {model.name}", model)
            if current_selection_data == model: # Try to reselect the previously selected model
                new_current_index = i
        
        if new_current_index != -1:
            self.model_selector.setCurrentIndex(new_current_index)
            self.current_model = current_selection_data
        elif atomic_models: # Default to the first model if no previous selection or it's gone
            self.model_selector.setCurrentIndex(0)
            self.current_model = atomic_models[0]
        else: 
            self.current_model = None # Should not be reached if atomic_models is populated
    
    def _model_changed(self, index):
        """Handle changes in the selected model from the dropdown."""
        if index >= 0:
            self.current_model = self.model_selector.itemData(index)
        else:
            self.current_model = None # No model selected
    
    def _load_file(self):
        """Load and parse the CSV file to extract residue indices."""
        filepath, _ = QFileDialog.getOpenFileName(
            self.tool_window.ui_area,
            "Select CSV File",
            "", # Start in the default directory
            "CSV files (*.csv);;All files (*.*)" 
        )
        
        if not filepath:
            return # User cancelled the dialog
        
        self.file_label.setText(os.path.basename(filepath))
        self.residue_indices_from_csv.clear() # Clear data from any previously loaded file
        
        try:
            with open(filepath, 'r', newline='') as f: 
                reader = csv.DictReader(f)
                # Check for required column headers
                if 'Matched' not in reader.fieldnames or 'Residue Index' not in reader.fieldnames:
                    self.session.logger.error("CSV file must contain 'Matched' and 'Residue Index' columns.")
                    self.file_label.setText("Error: Missing columns")
                    return

                for row in reader:
                    try:
                        matched_val_str = row.get('Matched', '0') # Default to '0' if missing
                        residue_idx_str = row.get('Residue Index', '')
                        
                        # Ensure values are not None or empty before trying to convert
                        if not matched_val_str or not residue_idx_str:
                            self.session.logger.warning(f"Skipping row due to missing Matched or Residue Index value: {row}")
                            continue
                            
                        matched_val = float(matched_val_str)
                        residue_idx = int(residue_idx_str)
                        
                        if matched_val >= 1 and residue_idx != -1:
                            self.residue_indices_from_csv.add(residue_idx)
                    except ValueError:
                        # Log a warning if a row has an invalid number format
                        self.session.logger.warning(f"Skipping row due to invalid number format: {row}")
                        continue 
            
            if not self.residue_indices_from_csv:
                self.session.logger.warning("No valid residue indices found in the file based on the specified criteria.")
            else:
                self.session.logger.info(f"Loaded {len(self.residue_indices_from_csv)} residue indices from CSV file.")
        
        except Exception as e:
            self.session.logger.error(f"Error reading CSV file: {str(e)}")
            self.file_label.setText("Error loading file")

    def _highlight_residues(self):
        """Highlights residues in the target chain(s) that are NOT in the CSV-derived list."""
        if not self.current_model:
            self.session.logger.error("No model selected. Please select a model first.")
            return

        if not self.current_model.chains:
            self.session.logger.error(f"Model {self.current_model.id_string} has no chains.")
            return

        from chimerax.core.commands import run
        
        # Apply background color to the entire model
        model_spec_id = f"#{self.current_model.id_string}"
        bg_color_hex = self.background_color.name() # Get color as #RRGGBB
        try:
            self.session.logger.info(f"Applying background color {bg_color_hex} to model {model_spec_id}")
            run(self.session, f"color {model_spec_id} {bg_color_hex}")
        except Exception as e:
            self.session.logger.error(f"Error applying background color: {str(e)}")
            return # Optionally stop if background coloring fails

        operating_chains = []
        selected_mode = self.mode_selector.currentText()

        if selected_mode == "Monomer":
            target_chain_id = "A"
            monomer_chain = None
            for chain in self.current_model.chains:
                if chain.chain_id == target_chain_id:
                    monomer_chain = chain
                    break
            if not monomer_chain and self.current_model.chains:
                monomer_chain = self.current_model.chains[0]
                self.session.logger.info(f"Chain 'A' not found, defaulting to first chain: {monomer_chain.chain_id}")
            
            if monomer_chain:
                operating_chains.append(monomer_chain)
            else:
                self.session.logger.error(f"No suitable chain found for Monomer mode in model {self.current_model.id_string}.")
                return
        
        elif selected_mode == "Dimer":
            chain_a = None
            chain_b = None
            for chain in self.current_model.chains:
                if chain.chain_id == 'A':
                    chain_a = chain
                elif chain.chain_id == 'B':
                    chain_b = chain
            
            if chain_a and chain_b:
                operating_chains.extend([chain_a, chain_b])
            elif len(self.current_model.chains) >= 2:
                operating_chains.extend([self.current_model.chains[0], self.current_model.chains[1]])
                self.session.logger.warning(f"Chains 'A' and 'B' not both found. Defaulting to first two chains: "
                                            f"{operating_chains[0].chain_id}, {operating_chains[1].chain_id} for Dimer mode.")
            else:
                self.session.logger.error(f"Not enough chains for Dimer mode in model {self.current_model.id_string}. Need at least 2.")
                return
        
        if not operating_chains:
            self.session.logger.info("No chains selected for highlighting based on current mode.")
            return

        # Determine the set of residue numbers to highlight based on a reference chain's residues
        # The CSV indices are those *not* to highlight.
        reference_chain_for_numbering = operating_chains[0] 
        all_residues_in_reference_chain = {res.number for res in reference_chain_for_numbering.residues if res.number is not None}
        
        # These are the residue *numbers* that should be highlighted on the sequence
        residue_numbers_to_highlight_on_sequence = all_residues_in_reference_chain - self.residue_indices_from_csv
        
        if not residue_numbers_to_highlight_on_sequence:
            self.session.logger.info("No residues to highlight. All residues in the reference chain are in the CSV list or the chain is empty.")
            return

        hl_color_hex = self.highlight_color.name()
        full_selection_specs_for_coloring = []
        total_highlighted_residue_count = 0
        
        for chain in operating_chains:
            # Filter residue_numbers_to_highlight_on_sequence to those actually existing in the current chain
            actual_residues_in_this_chain = {res.number for res in chain.residues if res.number is not None}
            valid_residues_for_this_chain_to_highlight = residue_numbers_to_highlight_on_sequence.intersection(actual_residues_in_this_chain)

            if valid_residues_for_this_chain_to_highlight:
                sel_string_parts = [str(res_num) for res_num in sorted(list(valid_residues_for_this_chain_to_highlight))]
                residue_list_str = ",".join(sel_string_parts)
                spec = f"{model_spec_id}/{chain.chain_id}:{residue_list_str}"
                full_selection_specs_for_coloring.append(spec)
                total_highlighted_residue_count += len(valid_residues_for_this_chain_to_highlight)

        if not full_selection_specs_for_coloring:
            self.session.logger.info("Residues to highlight based on CSV were not found in the target chain(s) or selected chains are empty.")
            return

        final_selection_string = " ".join(full_selection_specs_for_coloring)
        try:
            self.session.logger.info(f"Executing ChimeraX command: color {final_selection_string} {hl_color_hex}")
            run(self.session, f"color {final_selection_string} {hl_color_hex}")
            self.session.logger.info(f"Successfully highlighted {total_highlighted_residue_count} residues across {len(operating_chains)} chain(s) in {hl_color_hex}.")
        except Exception as e:
            self.session.logger.error(f"Error occurred while highlighting residues: {str(e)}")

    def delete(self):
        """Called when the tool window is closed."""
        # Perform any necessary cleanup here, like unregistering event handlers if any were set up.
        super().delete() 