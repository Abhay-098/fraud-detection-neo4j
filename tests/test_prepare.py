import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import pandas as pd
from scripts.prepare_paysim import prepare

def test_prepare(tmp_path):
    inp=tmp_path/'in.csv'; out=tmp_path/'out.csv'
    df=pd.DataFrame({
      'step':[1,2],'type':['TRANSFER','PAYMENT'],'amount':[100,50],
      'nameOrig':['C1','C2'],'oldbalanceOrg':[200,100],'newbalanceOrig':[100,50],
      'nameDest':['C3','M1'],'oldbalanceDest':[10,20],'newbalanceDest':[110,20],
      'isFraud':[1,0],'isFlaggedFraud':[0,0]
    })
    df.to_csv(inp,index=False); prepare(inp,out,rows=2)
    got=pd.read_csv(out)
    assert len(got)==2
    assert 'transaction_id' in got
    assert 'drain_ratio' in got
