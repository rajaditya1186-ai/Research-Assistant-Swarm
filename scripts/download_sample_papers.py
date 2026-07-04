import os
import urllib.request

def download_sample_papers():
    # Define papers to download
    papers = {
        "react_paper.pdf": "https://arxiv.org/pdf/2210.03629",
        "rag_paper.pdf": "https://arxiv.org/pdf/2005.11401"
    }
    
    target_dir = "data/sample_papers"
    os.makedirs(target_dir, exist_ok=True)
    
    print("==================================================")
    print("DOWNLOAD: ScholarSwarm Sample Papers Downloader")
    print(f"Target Directory: {target_dir}")
    print("==================================================")
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    
    for filename, url in papers.items():
        dest_path = os.path.join(target_dir, filename)
        if os.path.exists(dest_path):
            print(f"PASS: '{filename}' already exists, skipping download.")
            continue
            
        print(f"Downloading '{filename}' from arXiv...")
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req) as response:
                with open(dest_path, "wb") as out_file:
                    out_file.write(response.read())
            print(f"SUCCESS: Saved '{filename}'.")
        except Exception as e:
            print(f"ERROR: Failed to download '{filename}' - {str(e)}")
            
    print("==================================================")
    print("FINISHED: Downloader run completed!")
    print("==================================================")

if __name__ == "__main__":
    download_sample_papers()
