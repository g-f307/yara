import os
import httpx
from typing import List, Dict
import aiofiles
from pathlib import Path

CACHE_DIR = "/tmp/yara_projects"

class ProjectManager:
    @staticmethod
    async def sync_files(project_id: str, files: List[Dict[str, str]]):
        """
        Downloads files from URLs and caches them locally by project_id.
        """
        project_dir = Path(CACHE_DIR) / project_id
        project_dir.mkdir(parents=True, exist_ok=True)
        
        results = []
        async with httpx.AsyncClient() as client:
            print(f"Syncing {len(files)} files for project {project_id}")
            for f in files:
                url = f.get("url")
                name = f.get("name")
                if not url or not name:
                    results.append({"name": name, "status": "skipped", "reason": "Missing URL or Name"})
                    continue
                    
                file_path = project_dir / str(name)
                if file_path.exists():
                    results.append({"name": name, "status": "skipped", "reason": "Already downloaded"})
                    continue # Skip if already downloaded
                
                try:
                    print(f"Downloading {name} from {url}...")
                    response = await client.get(url, follow_redirects=True)
                    response.raise_for_status()
                    async with aiofiles.open(file_path, 'wb') as out_file:
                        await out_file.write(response.content)
                    print(f"Downloaded {name} successfully.")
                    results.append({"name": name, "status": "downloaded"})
                except Exception as e:
                    print(f"Failed to download {name} from {url}: {e}")
                    results.append({"name": name, "status": "failed", "reason": str(e)})
                    
        return {"status": "success", "synced_files": [f["name"] for f in files], "details": results}

    @staticmethod
    def get_project_dir(project_id: str) -> Path:
        return Path(CACHE_DIR) / project_id

    @staticmethod
    def get_project_data(project_id: str, data_type: str):
        from analysis.qiime_parser import load_qiime2_data
        
        project_dir = ProjectManager.get_project_dir(project_id)
        if not project_dir.exists():
            raise FileNotFoundError(f"Arquivos do projeto {project_id} não sincronizados no Python Core.")
            
        files = [f for f in project_dir.iterdir() if f.is_file() and f.suffix in ['.tsv', '.qzv']]
        
        # Helper to guess file type by content
        def is_likely_type(df, dt: str) -> bool:
            if df is None or df.empty: return False
            lower_cols = [str(c).lower() for c in df.columns]
            if dt == 'alpha':
                return any(c in ['shannon', 'observed_features', 'faith_pd', 'chao1', 'pielou_e', 'simpson'] for c in lower_cols)
            elif dt == 'beta':
                # Beta diversity distance matrices are square (nxn)
                return df.shape[0] == df.shape[1] and df.shape[0] > 1
            elif dt == 'taxonomy':
                return any('taxon' in c for c in lower_cols) or any('taxa' in c for c in lower_cols)
            elif dt == 'rarefaction':
                # Typically has numeric column names representing sampling depths
                return any(c.isdigit() for c in lower_cols)
            return True

        # First, we load all TSVs and check their content
        for f in files:
            try:
                # read blindly as a standard TSV
                import pandas as pd
                temp_df = pd.read_csv(f, sep='\t', index_col=0, comment='#')
                if is_likely_type(temp_df, data_type):
                    df = load_qiime2_data(str(f), data_type=data_type)
                    if df is not None and not df.empty:
                        return df
            except Exception as e:
                pass
                
        raise ValueError(f"Não foram encontrados dados válidos para a análise de {data_type} nos arquivos do projeto {project_id}.")

    @staticmethod
    def get_project_metadata(project_id: str):
        import pandas as pd
        project_dir = ProjectManager.get_project_dir(project_id)
        if not project_dir.exists():
            return None
            
        files = [f for f in project_dir.iterdir() if f.is_file() and f.suffix in ['.tsv', '.txt']]
        target_files = sorted(files, key=lambda f: 'metadata' not in f.name.lower())
        
        for f in target_files:
            try:
                df = pd.read_csv(f, sep='\t')
                # Try to identify sample ID column
                sample_col = next((c for c in df.columns if c.lower() in ['sample-id', 'sampleid', 'id', '#sampleid']), None)
                if sample_col:
                    df = df.set_index(sample_col)
                return df
            except:
                pass
        return None
