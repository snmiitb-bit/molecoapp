import ipywidgets as widgets
from IPython.display import display, HTML, clear_output
import pubchempy as pcp
import pandas as pd
import requests
from rdkit import Chem
from rdkit.Chem import Draw
import base64
from io import BytesIO
import io

# -------------------------------------------------------------------------
# STRUCTURE RENDERING HELPER
# -------------------------------------------------------------------------

def smiles_to_base64_img(smiles):
    """Converts a SMILES string into a 2D image encoded as a base64 HTML string."""
    if not smiles or pd.isna(smiles) or smiles == 'N/A':
        return "<div style='width:160px; height:160px; display:flex; align-items:center; justify-content:center; background:#f7fafc; border-radius:8px; font-size:12px; color:#a0aec0;'>No Structure</div>"
    try:
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            return "<div style='width:160px; height:160px; display:flex; align-items:center; justify-content:center; background:#fff5f5; color:#e53e3e; border-radius:8px; font-size:11px; font-weight:600;'>Invalid SMILES</div>"
        
        img = Draw.MolToImage(mol, size=(180, 180))
        buffered = BytesIO()
        img.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
        return f'<img src="data:image/png;base64,{img_str}" width="180" height="180" style="mix-blend-mode: multiply; margin: auto; display: block;" />'
    except Exception:
        return "Error Rendering"

# -------------------------------------------------------------------------
# DATABASE SEARCH PIPELINES
# -------------------------------------------------------------------------

def search_pubchem(identifier):
    results_list = []
    try:
        compounds = pcp.get_compounds(identifier, namespace='name')
        if not compounds and any(c in identifier for c in ['=', '#', '(', ')']):
            try: compounds = pcp.get_compounds(identifier, namespace='smiles')
            except: pass

        for comp in compounds:
            synonyms = comp.synonyms if comp.synonyms else []
            cas_numbers = [syn for syn in synonyms if syn.replace('-', '').isdigit() and '-' in syn]
            cas_str = cas_numbers[0] if cas_numbers else "N/A"

            results_list.append({
                "Source": "PubChem (.GOV)",
                "ID": f"CID: {comp.cid}",
                "Name": comp.iupac_name if comp.iupac_name else (comp.synonyms[0] if comp.synonyms else "N/A"),
                "CAS": cas_str,
                "Formula": comp.molecular_formula,
                "MW": f"{comp.molecular_weight} g/mol",
                "SMILES": comp.isomeric_smiles,
                "Link": f"https://pubchem.ncbi.nlm.nih.gov/compound/{comp.cid}"
            })
    except: pass
    return results_list

def search_epa_comptox(identifier):
    results_list = []
    url = f"https://api.epa.gov/comptox/api/chemical/search/equal/{identifier}"
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            for item in data:
                results_list.append({
                    "Source": "EPA CompTox (.GOV)",
                    "ID": item.get('dtxsid', 'N/A'),
                    "Name": item.get('preferredName', 'N/A'),
                    "CAS": item.get('casrn', 'N/A'),
                    "Formula": item.get('formula', 'N/A'),
                    "MW": f"{item.get('monoisotopicMass', 'N/A')} g/mol",
                    "SMILES": item.get('smiles', 'N/A'),
                    "Link": f"https://comptox.epa.gov/dashboard/chemical/details/{item.get('dtxsid')}"
                })
    except: pass
    return results_list

# -------------------------------------------------------------------------
# FLASHCARD HTML GENERATOR
# -------------------------------------------------------------------------

def build_flashcards_html(search_batch, layout_mode):
    """
    search_batch: List of dicts, e.g. [{"query": "aspirin", "db": "Both"}]
    layout_mode: "Individual Cards" or "Combined Grid"
    """
    combined_results = []
    
    # Process queries sequentially
    for entry in search_batch:
        q = entry["query"].strip()
        db = entry["db"]
        if not q:
            continue
            
        pubchem_res = []
        epa_res = []
        
        if db in ["Both", "PubChem Only"]:
            pubchem_res = search_pubchem(q)
        if db in ["Both", "EPA CompTox Only"]:
            epa_res = search_epa_comptox(q)
            
        combined_results.extend(pubchem_res + epa_res)
        
    if not combined_results:
        return "<p style='color:#e53e3e; font-weight:bold; padding: 15px;'>No matching compounds found for your input list.</p>"

    # HTML header injecting html2canvas and canvas render engine functions
    html_out = """
    <script src="https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js"></script>
    <script>
    function downloadFlashcard(cardId, filename) {
        const cardElement = document.getElementById(cardId);
        const downloadBtn = cardElement.querySelector('.download-trigger-btn');
        const linkBtn = cardElement.querySelector('.btn-link');
        if(downloadBtn) downloadBtn.style.visibility = 'hidden';
        if(linkBtn) linkBtn.style.visibility = 'hidden';

        html2canvas(cardElement, {
            useCORS: true,
            scale: 2,
            backgroundColor: "#ffffff"
        }).then(canvas => {
            let link = document.createElement('a');
            link.download = filename + '.png';
            link.href = canvas.toDataURL('image/png');
            link.click();
            
            if(downloadBtn) downloadBtn.style.visibility = 'visible';
            if(linkBtn) linkBtn.style.visibility = 'visible';
        });
    }

    function downloadCombinedGrid(containerId, filename) {
        const gridElement = document.getElementById(containerId);
        // Hide all downlaod elements in the whole frame temporarily
        const buttons = gridElement.querySelectorAll('.download-trigger-btn, .btn-link');
        buttons.forEach(b => b.style.visibility = 'hidden');

        html2canvas(gridElement, {
            useCORS: true,
            scale: 2,
            backgroundColor: "#ffffff"
        }).then(canvas => {
            let link = document.createElement('a');
            link.download = filename + '.png';
            link.href = canvas.toDataURL('image/png');
            link.click();
            
            buttons.forEach(b => b.style.visibility = 'visible');
        });
    }
    </script>
    
    <style>
        .outer-wrapper {
            padding: 10px;
            background: #ffffff;
        }
        .master-download-bar {
            margin-bottom: 20px;
            background: #f7fafc;
            padding: 12px;
            border-radius: 8px;
            border: 1px solid #e2e8f0;
        }
        .flashcard-container {
            display: flex;
            flex-wrap: wrap;
            gap: 24px;
            padding: 15px 0;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            background: #ffffff;
        }
        .chem-card {
            background: #ffffff;
            border: 2px solid #1a365d;
            border-radius: 16px;
            box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
            width: 340px;
            padding: 20px;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            position: relative;
            overflow: hidden;
            background-image: linear-gradient(to bottom, #ffffff 90%, #f7fafc 100%);
        }
        .brand-header {
            text-align: center;
            font-size: 11px;
            letter-spacing: 2px;
            font-weight: 800;
            color: #1a365d;
            border-bottom: 2px solid #cbd5e0;
            padding-bottom: 6px;
            margin-bottom: 12px;
            text-transform: uppercase;
        }
        .card-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 12px;
        }
        .badge {
            background: #ebf8ff;
            color: #2b6cb0;
            font-size: 10px;
            font-weight: 700;
            padding: 4px 8px;
            border-radius: 12px;
            border: 1px solid #bee3f8;
        }
        .card-id {
            font-size: 11px;
            color: #4a5568;
            font-family: monospace;
            font-weight: bold;
        }
        .structure-frame {
            background: #ffffff;
            border: 1px solid #e2e8f0;
            border-radius: 10px;
            padding: 10px;
            min-height: 180px;
            display: flex;
            align-items: center;
            justify-content: center;
            margin-bottom: 14px;
        }
        .chem-name {
            font-size: 18px;
            font-weight: 800;
            color: #1a202c;
            margin: 0 0 10px 0;
            line-height: 1.3;
            word-wrap: break-word;
        }
        .info-row {
            display: flex;
            font-size: 13px;
            margin-bottom: 6px;
        }
        .info-label {
            width: 90px;
            font-weight: 700;
            color: #4a5568;
            flex-shrink: 0;
        }
        .info-value {
            color: #2d3748;
            word-break: break-all;
        }
        .card-footer {
            margin-top: 18px;
            padding-top: 12px;
            border-top: 1px solid #e2e8f0;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .btn-link {
            font-size: 11px;
            font-weight: 700;
            color: #2b6cb0 !important;
            text-decoration: underline !important;
        }
        .download-trigger-btn {
            background: #1a365d;
            color: #ffffff !important;
            border: none;
            cursor: pointer;
            font-size: 11px;
            font-weight: 700;
            padding: 6px 12px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .download-trigger-btn:hover {
            background: #2a4365;
        }
        .master-download-btn {
            background: #2b6cb0;
            color: #ffffff !important;
            border: none;
            cursor: pointer;
            font-size: 13px;
            font-weight: 700;
            padding: 10px 20px;
            border-radius: 8px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        .master-download-btn:hover {
            background: #2c5282;
        }
    </style>
    <div class="outer-wrapper" id="molway-grid-capture-container">
    """

    # Add master combined downscaling controller if combined layout is targeted
    if layout_mode == "Combined Grid":
        html_out += """
        <div class="master-download-bar">
            <button class="master-download-btn" onclick="downloadCombinedGrid('molway-grid-capture-container', 'MOLWAY_ECOSYSTEM_Batch_Grid')">
                💾 Download All as Combined Grid Image (PNG)
            </button>
        </div>
        """

    html_out += '<div class="flashcard-container">'

    for idx, molecule in enumerate(combined_results):
        card_id = f"molway-card-{idx}"
        img_html = smiles_to_base64_img(molecule["SMILES"])
        download_filename = f"MOLWAY_{molecule['CAS'].replace(' ', '_')}" if molecule['CAS'] != 'N/A' else f"MOLWAY_Card_{idx}"
        
        html_out += f"""
        <div class="chem-card" id="{card_id}">
            <div>
                <div class="brand-header">MOLWAY ECOSYSTEM</div>
                
                <div class="card-header">
                    <span class="badge">{molecule['Source']}</span>
                    <span class="card-id">{molecule['ID']}</span>
                </div>
                
                <div class="structure-frame">
                    {img_html}
                </div>
                
                <h4 class="chem-name">{molecule['Name']}</h4>
                
                <div class="info-row">
                    <span class="info-label">CAS Reg:</span>
                    <span class="info-value" style="font-weight: bold; color: #1a365d;">{molecule['CAS']}</span>
                </div>
                <div class="info-row">
                    <span class="info-label">Formula:</span>
                    <span class="info-value">{molecule['Formula']}</span>
                </div>
                <div class="info-row">
                    <span class="info-label">Mol Wt:</span>
                    <span class="info-value">{molecule['MW']}</span>
                </div>
                <div class="info-row" style="margin-top: 8px;">
                    <span class="info-label" style="font-size: 11px; color:#718096;">SMILES:</span>
                    <span class="info-value" style="font-size: 11px; color:#718096; font-family: monospace;">{molecule['SMILES']}</span>
                </div>
            </div>
            
            <div class="card-footer">
                <a class="btn-link" target="_blank" href="{molecule['Link']}">Source Link &rarr;</a>
                """
        # Render individual buttons only if combined mode is disabled
        if layout_mode == "Individual Cards":
            html_out += f"""
                <button class="download-trigger-btn" onclick="downloadFlashcard('{card_id}', '{download_filename}')">
                    Download PNG
                </button>
            """
        
        html_out += """
            </div>
        </div>
        """
        
    html_out += "</div></div>"
    return html_out

# -------------------------------------------------------------------------
# INTERACTIVE UI LAYOUT (TABS FOR MODES)
# -------------------------------------------------------------------------

# Tab 1: Dedicated 3-5 Row Inputs
rows = []
for i in range(5):
    txt = widgets.Text(placeholder=f"Chemical Identifier #{i+1}...", layout=widgets.Layout(width='45%'))
    drop = widgets.Dropdown(options=['Both', 'PubChem Only', 'EPA CompTox Only'], value='Both', layout=widgets.Layout(width='25%'))
    row = widgets.HBox([widgets.Label(f"Input {i+1}:", layout=widgets.Layout(width='8%')), txt, drop])
    rows.append((txt, drop, row))

tab1_container = widgets.VBox([r[2] for r in rows])

# Tab 2: Semicolon Bulk Upload Form
file_uploader = widgets.FileUpload(
    accept='.csv,.txt',  
    multiple=False,
    description='Select File',
    button_style='warning',
    icon='upload',
    layout=widgets.Layout(width='30%')
)
upload_instructions = widgets.HTML("""
    <div style="font-size: 12px; color: #4a5568; margin-top: 5px;">
        Accepts <b>.txt</b> or <b>.csv</b> files. Columns must be separated by semicolons (<b>;</b>).<br>
        <b>Format Example:</b><br>
        <code style="background: #edf2f7; padding: 2px 5px; border-radius: 4px;">chemical_identifier;database_option</code><br>
        <code style="background: #edf2f7; padding: 2px 5px; border-radius: 4px;">Aspirin;Both</code><br>
        <code style="background: #edf2f7; padding: 2px 5px; border-radius: 4px;">50-78-2;PubChem Only</code>
    </div>
""")
tab2_container = widgets.VBox([file_uploader, upload_instructions])

# Create Jupyter Tab Widget
mode_tabs = widgets.Tab()
mode_tabs.children = [tab1_container, tab2_container]
mode_tabs.set_title(0, 'Quick Inputs (3-5 Entries)')
mode_tabs.set_title(1, 'Bulk Upload (Semicolon ; Separated)')

# Universal Options
generation_mode = widgets.RadioButtons(
    options=['Individual Cards', 'Combined Grid'],
    value='Individual Cards',
    description='Layout Output:',
    layout=widgets.Layout(width='40%')
)

trigger_button = widgets.Button(
    description='Generate MOLWAY Batch',
    button_style='success',
    icon='cogs',
    layout=widgets.Layout(width='250px', height='40px')
)

output_area = widgets.Output()

def execute_batch_processing(b):
    with output_area:
        clear_output()
        search_batch = []
        selected_mode = mode_tabs.selected_index
        layout_style = generation_mode.value
        
        if selected_mode == 0:
            # Gather from Quick 3-5 Inputs
            for txt_widget, drop_widget, _ in rows:
                query_val = txt_widget.value.strip()
                if query_val:
                    search_batch.append({"query": query_val, "db": drop_widget.value})
            
            if not search_batch:
                print("Error: No values entered in the text rows.")
                return
                
        elif selected_mode == 1:
            # Process uploaded Semicolon-Separated CSV or TXT file
            if not file_uploader.value:
                print("Error: Please select and upload a valid text or CSV file.")
                return
            
            # Access uploaded file data safely across IPywidgets versions
            uploaded_file = list(file_uploader.value.values())[0] if isinstance(file_uploader.value, dict) else file_uploader.value[0]
            content = uploaded_file['content'].decode('utf-8')
            
            try:
                # Read via Pandas, handling custom semicolon delimiter
                df_upload = pd.read_csv(io.StringIO(content), sep=';', header=None, names=['query', 'db'])
                for _, row_data in df_upload.iterrows():
                    q = str(row_data['query']).strip()
                    db = str(row_data['db']).strip() if pd.notna(row_data['db']) else 'Both'
                    
                    # Clean the database string
                    if db not in ['Both', 'PubChem Only', 'EPA CompTox Only']:
                        db = 'Both'
                        
                    if q and q != 'nan':
                        search_batch.append({"query": q, "db": db})
            except Exception as e:
                print(f"Error parsing file: {str(e)}. Please check that elements are semicolon-separated.")
                return
                
        if not search_batch:
            print("No valid queries loaded. Try again.")
            return

        print(f"Batch loaded. Querying {len(search_batch)} identifiers from targets... Drawing 2D chemical structures...")
        
        cards_html = build_flashcards_html(search_batch, layout_style)
        
        clear_output()
        display(HTML(cards_html))

# Link event logic
trigger_button.on_click(execute_batch_processing)

# Master Page Render Block
display(HTML("""
    <div style="font-family: sans-serif; margin-bottom: 20px; border-bottom: 2px solid #1a365d; padding-bottom: 10px;">
        <h1 style="color: #1a365d; margin-bottom: 4px; font-weight: 800;">MOLWAY ECOSYSTEM</h1>
        <p style="color: #4a5568; margin-top: 0; font-size: 14px; font-weight: 600;">Enterprise Batch Cheminformatics Engine</p>
    </div>
"""))

control_box = widgets.HBox([generation_mode, trigger_button], layout=widgets.Layout(align_items='center', margin='15px 0'))
display(mode_tabs, control_box, output_area)
