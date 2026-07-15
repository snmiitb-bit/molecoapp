import sys
import urllib.request
import urllib.parse
import json
import re
from indigo import Indigo
from indigo.renderer import IndigoRenderer

# Initialize Indigo
indigo = Indigo()
renderer = IndigoRenderer(indigo)

# Setup rendering options (white background, labels at bottom)
indigo.setOption("render-background-color", "1.0, 1.0, 1.0")
indigo.setOption("render-comment-position", "bottom")
indigo.setOption("render-comment-alignment", "center")
indigo.setOption("render-comment-font-size", 14.0)

def get_smiles_via_opsin(name):
    """Fallback method using OPSIN web API"""
    try:
        with urllib.request.urlopen(f"https://cam.ac.uk{urllib.parse.quote(name)}.json") as response:
            if response.status == 200:
                return json.loads(response.read().decode()).get("smiles")
    except Exception: return None

def sanitize_filename(name):
    return re.sub(r'[\\/*?:"<>| ]', '_', name)

# --- Main Program ---
print("--- Multi-Chemical Image & SMILES Generator ---")
while True:
    user_input = input("\nEnter chemical names (comma-separated): ").strip()
    if user_input.lower() in ['exit', 'quit', '']: break
        
    chemical_names = [name.strip() for name in user_input.split(",") if name.strip()]
    
    for name in chemical_names:
        mol, smiles_string = None, None
        try:
            mol = indigo.nameToStructure(name)
            mol.layout()
            smiles_string = mol.smiles()
        except:
            smiles_string = get_smiles_via_opsin(name)
            if smiles_string:
                mol = indigo.loadMolecule(smiles_string)
                mol.layout()

        if mol and smiles_string:
            # Set label with Name and SMILES
            indigo.setOption("render-comment", f"Name: {name}\nSMILES: {smiles_string}")
            filename = f"{sanitize_filename(name)}.png"
            renderer.renderToFile(mol, filename)
            print(f"[SUCCESS] {name} -> {filename}")
        else:
            print(f"[ERROR] Could not interpret '{name}'.")
