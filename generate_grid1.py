#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
from indigo import Indigo
from indigo.renderer import IndigoRenderer

# Initialize Indigo and IndigoRenderer
indigo = Indigo()
renderer = IndigoRenderer(indigo)

# --- Set Indigo options ---
indigo.setOption("render-margins", 10, 10)
indigo.setOption("render-background-color", "1.0, 1.0, 1.0") # Ensure clean white background

# --- Draw a single molecule with Indigo Renderer ---
name = "3-ethyl-octane"
try:
    mol = indigo.nameToStructure(name)
    print(f"SMILES for {name}: {mol.smiles()}")

    # Write an Indigo molecular structure to a file (PNG)
    indigo.setOption("render-output-format", "png")
    mol.layout()
    renderer.renderToFile(obj=mol, filename="mol.png")
    print("-> Saved single molecule image as: mol.png")

    # Write an Indigo molecular structure to a file (SVG)
    indigo.setOption("render-output-format", "svg")
    mol.layout()
    renderer.renderToFile(obj=mol, filename="mol.svg")
    print("-> Saved single molecule vector as: mol.svg")
except Exception as e:
    print(f"[ERROR] Failed to parse single molecule '{name}': {e}")

# --- Generate molecule from CAS number, and get SMILES ---
cas_number = "50-78-2"
smiles_for_aspirin = "CC(=O)Oc1ccccc1C(=O)O" # Explicitly providing SMILES for Aspirin

try:
    mol_from_cas = indigo.loadMolecule(smiles_for_aspirin)
    iupac_name_placeholder = mol_from_cas.grossFormula() 
    smiles_output = mol_from_cas.smiles()

    print(f"\n--- CAS Number Processing ---")
    print(f"Input CAS number: {cas_number}")
    print(f"SMILES used for creation: {smiles_for_aspirin}")
    print(f"Generated SMILES: {smiles_output}")
    print(f"Gross Formula: {iupac_name_placeholder}")

    # Save the CAS molecule image
    indigo.setOption("render-output-format", "png")
    mol_from_cas.layout()
    renderer.renderToFile(obj=mol_from_cas, filename="aspirin.png")
    print("-> Saved CAS molecule image as: aspirin.png")
except Exception as e:
    print(f"[ERROR] Failed to process CAS info: {e}")

# --- Draw a grid of molecules with Indigo Renderer ---
names = [
    "cyclohexane",
    "1-methyl-cyclohexane",
    "1,2-dimethyl-cyclohexane",
    "1,3-dimethyl-cyclohexane",
    "1,4-dimethyl-cyclohexane",
    "1,2,3-trimethyl-cyclohexane",
]

print("\n--- Processing Grid of Molecules ---")
array = indigo.createArray()
for n in names:
    try:
        this_mol = indigo.nameToStructure(n)
        this_mol.layout()
        this_mol.setProperty("grid-comment", n)
        array.arrayAdd(this_mol)
        print(f"  Added to grid: {n}")
    except Exception as e:
        print(f"  [ERROR] Skipping '{n}': {e}")

# Set grid display layout options
indigo.setOption("render-grid-title-property", "grid-comment")
indigo.setOption("render-grid-title-offset", "15")
indigo.setOption("render-grid-margins", "20, 20") # Reduced margins slightly for cleaner image sizing

# Write a grid of Indigo molecules to an image file (PNG)
indigo.setOption("render-output-format", "png")
renderer.renderGridToFile(
    objects=array,
    refatoms=None,
    ncolumns=3,
    filename="structures.png",
)
print("-> Saved molecule grid image as: structures.png")

# Write a grid of Indigo molecules to an image file (SVG)
indigo.setOption("render-output-format", "svg")
renderer.renderGridToFile(
    objects=array,
    refatoms=None,
    ncolumns=3,
    filename="structures.svg",
)
print("-> Saved molecule grid vector as: structures.svg")

print("\n=============================================")
print(" Execution complete! Opening the grid image... ")
print("=============================================")

# Command prompt trigger to instantly pop up the finished image on your desktop
os.system("explorer structures.png")
