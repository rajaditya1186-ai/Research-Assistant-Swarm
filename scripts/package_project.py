import os
import zipfile
import sys

def package_project():
    archive_name = "research_assistant_swarm.zip"
    
    # Exclude directories (normalized for cross-platform matches)
    exclude_dirs = {
        ".venv",
        "venv",
        "env",
        ".git",
        ".gemini",
        ".agents",
        "__pycache__",
        ".pytest_cache",
        ".mypy_cache",
        os.path.normpath("data/chroma_db"),
        os.path.normpath("data/chroma_db_test"),
        os.path.normpath("data/uploads")
    }
    
    # Exclude files
    exclude_files = {
        ".env",
        archive_name,
        "Thumbs.db",
        ".DS_Store"
    }
    
    print("==================================================")
    print("PACKAGE: ScholarSwarm Submission Packaging Suite")
    print(f"Creating archive: {archive_name}")
    print("==================================================")
    
    file_count = 0
    total_size = 0
    
    try:
        with zipfile.ZipFile(archive_name, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk("."):
                # Normalize path separators
                rel_root = os.path.relpath(root, ".")
                
                # Check directory exclusions
                skip_dir = False
                for ex_dir in exclude_dirs:
                    # Match exact folder name or relative path prefix
                    if rel_root == ex_dir or rel_root.startswith(ex_dir + os.sep) or rel_root.startswith(ex_dir + "/"):
                        skip_dir = True
                        break
                        
                if skip_dir or rel_root.startswith(".git"):
                    continue
                    
                for file in files:
                    # Ignore logs and intermediate cached outputs
                    if file.endswith(".log") or file.endswith(".pyc") or file.endswith(".pyo"):
                        continue
                        
                    file_path = os.path.join(root, file)
                    rel_path = os.path.relpath(file_path, ".")
                    
                    if rel_path in exclude_files or file in exclude_files:
                        continue
                        
                    zipf.write(file_path, rel_path)
                    file_count += 1
                    total_size += os.path.getsize(file_path)
                    print(f"Added: {rel_path} ({os.path.getsize(file_path)} bytes)")
                    
        print("==================================================")
        print("FINISHED: Packaging completed successfully!")
        print(f"Total files archived: {file_count}")
        print(f"Compressed archive size: {os.path.getsize(archive_name)} bytes ({os.path.getsize(archive_name)/(1024*1024):.2f} MB)")
        print("==================================================")
        
    except Exception as e:
        print(f"ERROR: Packaging failed - {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    package_project()
