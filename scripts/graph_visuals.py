import argparse
from pathlib import Path
import hashlib
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

def h(v,m): return int(hashlib.sha256(str(v).encode()).hexdigest()[:10],16)%m

def main(inp):
    df=pd.read_csv(inp).head(5000)
    out=Path('reports/figures'); out.mkdir(parents=True,exist_ok=True)
    # Shared-device-style enrichment graph
    accounts=pd.concat([df.nameOrig,df.nameDest[df.nameDest.str.startswith('C')]],ignore_index=True).drop_duplicates().head(80).tolist()
    device={a:f'D{h(a,8)+1:02d}' for a in accounts}
    edges=[]
    for a,d in device.items(): edges.append((a,d))
    fig,ax=plt.subplots(figsize=(10,7))
    ax.axis('off')
    rng=np.random.default_rng(42)
    pos={}
    for i,a in enumerate(accounts): pos[a]=(np.cos(2*np.pi*i/max(1,len(accounts)))*3.2,np.sin(2*np.pi*i/max(1,len(accounts)))*3.2)
    for d in sorted(set(device.values())):
        idx=sorted(set(device.values())).index(d); pos[d]=(np.cos(2*np.pi*idx/max(1,len(set(device.values()))))*1.2,np.sin(2*np.pi*idx/max(1,len(set(device.values()))))*1.2)
    for a,d in edges: ax.plot([pos[a][0],pos[d][0]],[pos[a][1],pos[d][1]],linewidth=.7,alpha=.35)
    ax.scatter([pos[a][0] for a in accounts],[pos[a][1] for a in accounts],s=30)
    devs=sorted(set(device.values())); ax.scatter([pos[d][0] for d in devs],[pos[d][1] for d in devs],s=80,marker='s')
    for x,y in pos.values(): pass
    ax.set_title('Synthetic Device-Enrichment Graph (Demo)')
    fig.tight_layout(); fig.savefig(out/'11_shared_device_graph.png',dpi=180); plt.close(fig)

    # transaction network, top nodes
    tx=df[df.nameDest.str.startswith('C')].copy().head(250)
    nodes=pd.concat([tx.nameOrig,tx.nameDest]).value_counts().head(35).index.tolist()
    nodes=set(nodes)
    tx=tx[tx.nameOrig.isin(nodes)&tx.nameDest.isin(nodes)]
    pos={n:(np.cos(2*np.pi*i/max(1,len(nodes)))*3.0,np.sin(2*np.pi*i/max(1,len(nodes)))*3.0) for i,n in enumerate(sorted(nodes))}
    fig,ax=plt.subplots(figsize=(10,7)); ax.axis('off')
    for _,r in tx.iterrows():
        x1,y1=pos[r.nameOrig]; x2,y2=pos[r.nameDest]
        ax.annotate('',xy=(x2,y2),xytext=(x1,y1),arrowprops=dict(arrowstyle='->',alpha=.12,linewidth=.7))
    deg=tx.nameOrig.value_counts().add(tx.nameDest.value_counts(),fill_value=0)
    sizes=[35+15*float(deg.get(n,0)) for n in sorted(nodes)]
    ax.scatter([pos[n][0] for n in sorted(nodes)],[pos[n][1] for n in sorted(nodes)],s=sizes)
    ax.set_title('Transaction Network – Top Connected Customers (Demo)')
    fig.tight_layout(); fig.savefig(out/'12_transaction_network.png',dpi=180); plt.close(fig)

if __name__=='__main__':
    ap=argparse.ArgumentParser(); ap.add_argument('--input',default='data/processed/paysim_subset.csv'); args=ap.parse_args(); main(args.input)
