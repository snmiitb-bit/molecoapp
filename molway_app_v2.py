import sys
import requests
import xml.etree.ElementTree as ET
import webbrowser
import tkinter as tk
from tkinter import ttk, messagebox

class PubMedSearchApp:
    def __init__(self, root):
        self.root = root
        self.root.title("PubMed Literature Search Utility")
        self.root.geometry("750x550")
        self.root.minsize(600, 400)
        
        # Configure layout styling
        self.style = ttk.Style()
        self.style.theme_use("clam")
        
        self.create_widgets()
        
    def create_widgets(self):
        # Header / Info Panel
        header_frame = ttk.Frame(self.root, padding="15")
        header_frame.pack(fill=tk.X)
        
        title_label = ttk.Label(
            header_frame, 
            text="PubMed Literature Search", 
            font=("Helvetica", 16, "bold")
        )
        title_label.pack(anchor=tk.W)
        
        desc_label = ttk.Label(
            header_frame, 
            text="Enter a chemical name, CAS number, or keyword to retrieve related medical and scientific literature.",
            font=("Helvetica", 10),
            wraplength=700
        )
        desc_label.pack(anchor=tk.W, pady=(5, 0))
        
        # Search Entry Bar
        search_frame = ttk.LabelFrame(self.root, text=" Search Query ", padding="15")
        search_frame.pack(fill=tk.X, padx=15, pady=5)
        
        self.query_var = tk.StringVar()
        self.search_entry = ttk.Entry(
            search_frame, 
            textvariable=self.query_var, 
            font=("Helvetica", 11)
        )
        self.search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        self.search_entry.bind("<Return>", lambda event: self.execute_search())
        
        search_btn = ttk.Button(
            search_frame, 
            text="Search", 
            command=self.execute_search
        )
        search_btn.pack(side=tk.RIGHT, ipadx=10)
        
        # Results Section
        results_frame = ttk.Frame(self.root, padding="15")
        results_frame.pack(fill=tk.BOTH, expand=True)
        
        self.status_label = ttk.Label(
            results_frame, 
            text="Ready to search.", 
            font=("Helvetica", 9, "italic")
        )
        self.status_label.pack(anchor=tk.W, pady=(0, 5))
        
        # Table Scrollbars
        scroll_y = ttk.Scrollbar(results_frame, orient=tk.VERTICAL)
        scroll_x = ttk.Scrollbar(results_frame, orient=tk.HORIZONTAL)
        
        # Results Treeview Table
        self.tree = ttk.Treeview(
            results_frame, 
            columns=("PMID", "Title", "Journal", "Date", "Link"), 
            show="headings",
            yscrollcommand=scroll_y.set,
            xscrollcommand=scroll_x.set
        )
        
        scroll_y.config(command=self.tree.yview)
        scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
        scroll_x.config(command=self.tree.xview)
        scroll_x.pack(side=tk.BOTTOM, fill=tk.X)
        self.tree.pack(fill=tk.BOTH, expand=True)
        
        # Column Definitions
        self.tree.heading("PMID", text="PMID")
        self.tree.heading("Title", text="Article Title")
        self.tree.heading("Journal", text="Journal Name")
        self.tree.heading("Date", text="Pub Date")
        self.tree.heading("Link", text="PubMed Link")
        
        self.tree.column("PMID", width=100, anchor=tk.CENTER)
        self.tree.column("Title", width=300, anchor=tk.W)
        self.tree.column("Journal", width=150, anchor=tk.W)
        self.tree.column("Date", width=100, anchor=tk.CENTER)
        self.tree.column("Link", width=80, anchor=tk.CENTER)
        
        # Bind double-click to open PubMed article in default browser
        self.tree.bind("<Double-1>", self.open_link)

    def execute_search(self):
        query = self.query_var.get().strip()
        if not query:
            messagebox.showwarning("Warning", "Please enter a search query.")
            return
            
        self.status_label.config(text="Searching PubMed database... Please wait...")
        self.root.update()
        
        # Clear old rows
        for row in self.tree.get_children():
            self.tree.delete(row)
            
        try:
            results = self.fetch_pubmed_data(query)
            
            if not results:
                self.status_label.config(text="No publications found for this query.")
                return
                
            for doc in results:
                self.tree.insert("", tk.END, values=(
                    doc.get("PMID"),
                    doc.get("Title"),
                    doc.get("Journal"),
                    doc.get("Date"),
                    doc.get("Link")
                ))
                
            self.status_label.config(text=f"Success! Found {len(results)} relevant publications.")
            
        except Exception as e:
            self.status_label.config(text="Search failed.")
            messagebox.showerror("Connection Error", f"Failed to retrieve data from NCBI servers:\n{e}")

    def fetch_pubmed_data(self, keyword, max_results=10):
        """Queries NCBI Entrez API to fetch matching medical/scientific literature."""
        base_search_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
        base_summary_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"
        
        # Step 1: Query IDs matching search term
        search_params = {
            "db": "pubmed",
            "term": keyword,
            "retmode": "json",
            "retmax": max_results
        }
        
        response = requests.get(base_search_url, params=search_params, timeout=10)
        response.raise_for_status()
        id_list = response.json().get("esearchresult", {}).get("idlist", [])
        
        if not id_list:
            return []
            
        # Step 2: Fetch detailed XML summaries for those IDs
        summary_params = {
            "db": "pubmed",
            "id": ",".join(id_list),
            "retmode": "xml"
        }
        
        summary_response = requests.get(base_summary_url, params=summary_params, timeout=10)
        summary_response.raise_for_status()
        
        # Parse XML response
        root_xml = ET.fromstring(summary_response.content)
        articles_data = []
        
        for doc_sum in root_xml.findall("DocSum"):
            pmid = doc_sum.find("Id").text
            title = "Unknown Title"
            journal = "Unknown Journal"
            pub_date = "N/A"
            
            for item in doc_sum.findall("Item"):
                name = item.get("Name")
                if name == "Title":
                    title = item.text
                elif name == "Source":
                    journal = item.text
                elif name == "PubDate":
                    pub_date = item.text
            
            articles_data.append({
                "PMID": pmid,
                "Title": title,
                "Journal": journal,
                "Date": pub_date,
                "Link": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"
            })
            
        return articles_data

    def open_link(self, event):
        """Opens the selected article's PubMed webpage."""
        selected_item = self.tree.focus()
        if not selected_item:
            return
            
        values = self.tree.item(selected_item, "values")
        if values:
            pubmed_url = values[4] # Link is in the 5th column index
            webbrowser.open(pubmed_url)

if __name__ == "__main__":
    root = tk.Tk()
    app = PubMedSearchApp(root)
    root.mainloop()