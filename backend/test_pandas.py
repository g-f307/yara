import sys
import pandas as pd
from pathlib import Path

# Add /app to sys.path since we run from within docker
sys.path.append('/app')

from analysis.qiime_parser import load_qiime2_data

def is_likely_type(df, dt: str) -> bool:
    if df is None or df.empty: return False
    lower_cols = [str(c).lower() for c in df.columns]
    if dt == 'alpha':
        return any(c in ['shannon', 'observed_features', 'faith_pd', 'chao1', 'pielou_e', 'simpson'] for c in lower_cols)
    elif dt == 'beta':
        return df.shape[0] == df.shape[1] and df.shape[0] > 1
    elif dt == 'taxonomy':
        return any('taxon' in c for c in lower_cols) or any('taxa' in c for c in lower_cols)
    elif dt == 'rarefaction':
        return any(c.isdigit() for c in lower_cols)
    return True

f = '/tmp/yara_projects/15443099-1d33-439b-8f82-56a7684fbe42/alpha_mock.tsv'
try:
    temp_df = pd.read_csv(f, sep='\t', index_col=0, comment='#')
    print("Columns:", [str(c).lower() for c in temp_df.columns])
    print("Is Likely Alpha:", is_likely_type(temp_df, 'alpha'))
    print("Is Likely Beta:", is_likely_type(temp_df, 'beta'))
    print("Is Likely Tax:", is_likely_type(temp_df, 'taxonomy'))
    print("Is Likely Rare:", is_likely_type(temp_df, 'rarefaction'))
    
    df = load_qiime2_data(f, data_type='alpha')
    print("Loaded df shape:", df.shape if df is not None else None)
    if df is not None:
        print(df.head(2))
except Exception as e:
    print("Error:", e)
