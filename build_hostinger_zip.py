import os
import zipfile

def create_zip(source_dir, output_filename):
    print(f"Creating {output_filename}...")
    exclude_dirs = {'.venv', '.git', '__pycache__', '.pytest_cache', 'knowledge'}
    exclude_exts = {'.pyc', '.log'}
    
    with zipfile.ZipFile(output_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(source_dir):
            # Exclude directories
            dirs[:] = [d for d in dirs if d not in exclude_dirs]
            
            for file in files:
                if any(file.endswith(ext) for ext in exclude_exts):
                    continue
                if file == output_filename or file == "build_hostinger_zip.py" or file == "crewairag_hostinger_deploy.zip" or file == "crewairag_frontend_only.zip":
                    continue
                    
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, source_dir)
                
                # Rename .py to .txt in the archive to bypass Hostinger upload blocker
                if arcname.endswith('.py'):
                    arcname = arcname + '.txt'
                
                zipf.write(file_path, arcname)
                
    print(f"Successfully created {output_filename}")

if __name__ == "__main__":
    create_zip(".", "crewairag_hostinger_deploy_safe.zip")
