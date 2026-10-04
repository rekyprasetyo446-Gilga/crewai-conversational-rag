import os
import zipfile

def create_frontend_zip():
    source_dir = "templates"
    output_filename = "crewairag_html_index_only.zip"
    print(f"Creating {output_filename} from {source_dir}/ ...")
    
    with zipfile.ZipFile(output_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(source_dir):
            for file in files:
                if file.endswith('.bak'):
                    continue
                file_path = os.path.join(root, file)
                # Make paths relative to the templates folder
                arcname = os.path.relpath(file_path, source_dir)
                zipf.write(file_path, arcname)
                
    print(f"Successfully created {output_filename}")

if __name__ == "__main__":
    create_frontend_zip()
