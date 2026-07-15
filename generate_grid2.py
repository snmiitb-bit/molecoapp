#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os
import urllib.request
import urllib.parse
import json
import re
from indigo import Indigo
from indigo.renderer import IndigoRenderer

# Initialize Indigo and IndigoRenderer
indigo = Indigo()
renderer = IndigoRenderer(indigo)

# --- Global Visual Configuration ---
indigo.setOption("render-background-color", "1.0, 1.0, 1.0") # White background
indigo.setOption("render-coloring", "true")                    # Enable atom colors
indigo.setOption("render-comment-position", "bottom")         # Text goes underneath structure
indigo.setOption("render-comment-alignment", "center")        # Centered labels
indigo.setOption("render-comment-font-size", 14)              # Clear font scale
indigo.setOption("render-comment-offset", 8)                  # Text padding spacing

def get_smiles_via_opsin(name):
    """Fallback method using OPSIN web API for tricky/common names"""
    try:
        safe_url = f"https://cam.ac.uk{urllib.parse.quote(name)}.json"
        with urllib.request.urlopen(safe_url, timeout=5) as response:
            if response.status == 200:
                return json.loads(response.read().decode()).get("smiles")
    except Exception: 
        return None
    return None

def sanitize_filename(name):
    """Removes invalid OS file characters from chemical names for safe saving"""
    return re.sub(r'[\\/*?:"<>| ]', '_', name)

# --- Command Line Tool Interface ---
print("==========================================================")
print("     Advanced Chemical Structure Image Generator          ")
print("==========================================================")
print("-> Type 'exit' or 'quit' at any prompt to terminate.\n")

while True:
    # STEP 1: Ask how the output should be structured
    print("How would you like to output the results?")
    print(" [1] Separate images for each chemical name")
    print(" [2] A single combined grid image containing all structures")
    
    try:
        output_choice = input("Enter choice (1 or 2): ").strip()
    except (KeyboardInterrupt, EOFError):
        print("\nExiting program. Goodbye!")
        sys.exit()
        
    if output_choice.lower() in ['exit', 'quit']:
        print("Exiting program. Goodbye!")
        sys.exit()
        
    if output_choice not in ['1', '2']:
        print("\n[ERROR] Invalid selection. Please enter 1 or 2.\n")
        print("-" * 60)
        continue

    # STEP 2: Ask for the chemical inputs
    try:
        user_input = input("\nEnter chemical names (separated by commas): ").strip()
    except (KeyboardInterrupt, EOFError):
        print("\nExiting program. Goodbye!")
        sys.exit()
        
    if user_input.lower() in ['exit', 'quit', '']: 
        print("Exiting program. Goodbye!")
        sys.exit()
        
    chemical_names = [name.strip() for name in user_input.split(",") if name.strip()]
    print(f"\nProcessing {len(chemical_names)} compounds...")
    print("-" * 60)
    
    file_to_open = None

    # ====================================================
    # OPTION 1: SEPARATE IMAGES PER MOLECULE
    # ====================================================
    if output_choice == '1':
        for name in chemical_names:
            mol, smiles_string = None, None
            try:
                mol = indigo.nameToStructure(name)
                mol.layout()
                smiles_string = mol.smiles()
            except Exception:
                smiles_string = get_smiles_via_opsin(name)
                if smiles_string:
                    try:
                        mol = indigo.loadMolecule(smiles_string)
                        mol.layout()
                    except Exception: mol = None

            if mol and smiles_string:
                indigo.setOption("render-comment", f"Name: {name}\nSMILES: {smiles_string}")
                filename = f"{sanitize_filename(name)}.png"
                indigo.setOption("render-output-format", "png")
                renderer.renderToFile(mol, filename)
                print(f"[SUCCESS] Saved individual file: {filename}")
                file_to_open = filename
            else:
                print(f"[ERROR] Could not interpret: '{name}'")
        
    # ====================================================
    # OPTION 2: COMBINED GRID LAYOUT MATRIX
    # ====================================================
    elif output_choice == '2':
        molecule_array = indigo.createArray()
        valid_count = 0
        
        # Grid settings require mapping text as metadata
        indigo.setOption("render-grid-title-property", "grid-comment")
        indigo.setOption("render-grid-title-offset", "10")
        indigo.setOption("render-grid-margins", "20, 20")
        
        for name in chemical_names:
            mol, smiles_string = None, None
            try:
                mol = indigo.nameToStructure(name)
                mol.layout()
                smiles_string = mol.smiles()
            except Exception:
                smiles_string = get_smiles_via_opsin(name)
                if smiles_string:
                    try:
                        mol = indigo.loadMolecule(smiles_string)
                        mol.layout()
                    except Exception: mol = None

            if mol and smiles_string:
                # Store the custom label details inside the grid object metadata
                mol.setProperty("grid-comment", f"Name: {name}\nSMILES: {smiles_string}")
                molecule_array.arrayAdd(mol)
                print(f"[SUCCESS] Queued for grid: '{name}'")
                valid_count += 1
            else:
                print(f"[ERROR] Skipping invalid name: '{name}'")
                
        if valid_count > 0:
            filename = "combined_chemical_grid.png"
            indigo.setOption("render-output-format", "png")
            
            # Dynamically calculate number of columns (3 maximum)
            columns = 3 if valid_count >= 3 else valid_count
            renderer.renderGridToFile(molecule_array, None, columns, filename)
            
            print(f"\n[GRID COMPLETE] Saved all valid structures into: {filename}")
            file_to_open = filename
        else:
            print("\n[ERROR] No valid molecules were interpreted. Grid generation aborted.")

    print("-" * 60)
    
    # Automatically open the generated file using the Windows file viewer
    if file_to_open and os.path.exists(file_to_open):
        print(f"Opening generated output file ({file_to_open})...")
        os.system(f"explorer {file_to_open}")
    print("\n" + "="*60 + "\n")
