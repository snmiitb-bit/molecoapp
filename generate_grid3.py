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

# Initialize Indigo structural libraries
indigo = Indigo()
renderer = IndigoRenderer(indigo)

# --- Global Image Rendering Settings ---
indigo.setOption("render-background-color", "1.0, 1.0, 1.0") # Pure White Canvas
indigo.setOption("render-coloring", "true")                    # Colored atoms (O=Red, N=Blue, etc.)
indigo.setOption("render-comment-position", "bottom")         # Text lines positioned beneath bonds
indigo.setOption("render-comment-alignment", "center")        # Centered text fields
indigo.setOption("render-comment-font-size", 13)              # Clean structural text size
indigo.setOption("render-comment-offset", 8)                  # Balanced layout spacing margin

def clean_cas_string(cas_string):
    return cas_string.strip()

def resolve_cas_via_cir(cas_rn):
    """
    Primary API Layer: Pings the NCI Chemical Identifier Resolver.
    Excellent for mapping specialized/industrial registry codes like 25601-41-6 and 872-05-9.
    """
    try:
        safe_cas = urllib.parse.quote(cas_rn)
        # Requesting canonical SMILES format
        url = f"https://nih.gov{safe_cas}/smiles"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=6) as response:
            if response.status == 200:
                smiles = response.read().decode().strip()
                if smiles and "gandalf" not in smiles.lower(): # Filter edge-case errors
                    return smiles
    except Exception:
        return None
    return None

def fetch_name_from_pubchem(smiles_str, default_cas):
    """
    Pulls a clean IUPAC/Common text title from PubChem using a confirmed SMILES pattern.
    """
    try:
        safe_smiles = urllib.parse.quote(smiles_str)
        url = f"https://nih.gov{safe_smiles}/property/Title/JSON"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode())
            title = data["PropertyTable"]["Properties"][0].get("Title")
            if title:
                return title
    except Exception:
        return f"Compound {default_cas}"
    return f"Compound {default_cas}"

def resolve_cas_via_pubchem_backup(cas_rn):
    """
    Secondary Backup Layer: Tries PubChem Substance cross-referencing folders if needed.
    """
    try:
        safe_cas = urllib.parse.quote(cas_rn)
        substance_url = f"https://nih.gov{safe_cas}/cids/JSON"
        req = urllib.request.Request(substance_url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode())
            cid = data["InformationList"]["Information"]["CompoundID"]
            
        prop_url = f"https://nih.gov{cid}/property/Title,IsomericSMILES/JSON"
        req_prop = urllib.request.Request(prop_url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req_prop, timeout=5) as resp:
            prop_data = json.loads(resp.read().decode())
            properties = prop_data["PropertyTable"]["Properties"]
            return properties.get("Title"), properties.get("IsomericSMILES")
    except Exception:
        return None, None

def sanitize_filename(name):
    return re.sub(r'[\\/*?:"<>| ]', '_', name)

# --- Interactive Terminal Core Loop ---
print("==========================================================")
print("     Universal CAS Chemical Vector Resolution Engine      ")
print("==========================================================")
print("-> Handles structural synthesis for specialty & niche compounds.")
print("-> Separate distinct CAS inputs using commas (,).")
print("-> Enter 'exit' or 'quit' to terminate the script process.\n")

while True:
    print("How would you like to output the structural files?")
    print(" Separate isolated images for each CAS number")
    print(" A single unified matrix grid chart")
    
    output_choice = input("Select format option (1 or 2): ").strip()
    if output_choice.lower() in ['exit', 'quit']: sys.exit()
    if output_choice not in ['1', '2']:
        print("\n[ERROR] Invalid menu choice. Select option 1 or 2.\n" + "-"*60)
        continue

    user_input = input("\nEnter CAS registry number(s): ").strip()
    if user_input.lower() in ['exit', 'quit', '']: sys.exit()
        
    cas_list = [clean_cas_string(item) for item in user_input.split(",") if item.strip()]
    print(f"\nAnalyzing {len(cas_list)} registry pointers across distributed databases...")
    print("-" * 65)
    
    file_to_open = None

    # ====================================================
    # LAYOUT OPTION 1: SEPARATE CHANNELS
    # ====================================================
    if output_choice == '1':  
        for cas in cas_list:
            print(f"Resolving Structure for CAS: {cas}...")
            
            # Step A: Attempt primary translation using the NCI Resolver
            smiles_string = resolve_cas_via_cir(cas)
            final_name = None
            
            if smiles_string:
                final_name = fetch_name_from_pubchem(smiles_string, cas)
            else:
                # Step B: Trigger Secondary PubChem Substance Fallback Routing
                final_name, smiles_string = resolve_cas_via_pubchem_backup(cas)

            mol = None
            if smiles_string:
                try:
                    mol = indigo.loadMolecule(smiles_string)
                    mol.layout()
                except Exception: mol = None

            if mol and smiles_string:
                indigo.setOption("render-comment", f"CAS: {cas}\nName: {final_name}\nSMILES: {smiles_string}")
                filename = f"{sanitize_filename(cas)}.png"
                indigo.setOption("render-output-format", "png")
                renderer.renderToFile(mol, filename)
                print(f"[SUCCESS] Saved standalone file -> {filename}\n")
                file_to_open = filename
            else:
                print(f"[ERROR] Registry record unreachable for CAS signature: '{cas}'\n")
                
    # ====================================================
    # LAYOUT OPTION 2: MULTI-COLUMN MATRIX
    # ====================================================
    elif output_choice == '2':  
        molecule_array = indigo.createArray()
        valid_count = 0
        indigo.setOption("render-grid-title-property", "grid-comment")
        indigo.setOption("render-grid-title-offset", "10")
        indigo.setOption("render-grid-margins", "20, 20")
        
        for cas in cas_list:
            print(f"Resolving Structure for CAS: {cas}...")
            
            smiles_string = resolve_cas_via_cir(cas)
            final_name = None
            
            if smiles_string:
                final_name = fetch_name_from_pubchem(smiles_string, cas)
            else:
                final_name, smiles_string = resolve_cas_via_pubchem_backup(cas)

            mol = None
            if smiles_string:
                try:
                    mol = indigo.loadMolecule(smiles_string)
                    mol.layout()
                except Exception: mol = None

            if mol and smiles_string:
                mol.setProperty("grid-comment", f"CAS: {cas}\nName: {final_name}\nSMILES: {smiles_string}")
                molecule_array.arrayAdd(mol)
                valid_count += 1
                print(f"[SUCCESS] Staged for matrix: '{final_name}'\n")
            else:
                print(f"[ERROR] Registry record unreachable for CAS signature: '{cas}'\n")
                
        if valid_count > 0:
            filename = "cas_resolved_chemical_grid.png"
            indigo.setOption("render-output-format", "png")
            columns = 3 if valid_count >= 3 else valid_count
            renderer.renderGridToFile(molecule_array, None, columns, filename)
            print(f"[GRID COMPLETE] Dynamic layout vector drawn to: {filename}")
            file_to_open = filename

    print("-" * 65)
    if file_to_open and os.path.exists(file_to_open):
        os.system(f"explorer {file_to_open}")
    print("\n" + "="*58 + "\n")
