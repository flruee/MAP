import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
df = pd.read_csv("data/balances_block_7mio.csv")
bins = np.logspace(0,18,1000)
#df2=(df["transferable"]-df["transferable"].min())/(df["transferable"].max()-df["transferable"].min())
df2 = df[df["transferable"]>0]
print(df[df["transferable"]<0].count())
print(df[df["transferable"]>0].count())


plt.hist(df2["transferable"],bins=bins )
plt.axvline(1e10,c="r",ls="--")
plt.xlabel("Planck")
plt.ylabel("Count")
plt.title(f"Balance distribution of block {df['block_number'].max()} in log-log")
plt.yscale("log")
plt.xscale("log")
plt.savefig("imgs/balance_snapshot_hist.png",dpi=300)
"""
df.drop(0,axis=0,inplace=True)
plt.plot(df["era"], df["validator_payout"],"k-", label="validator payout")
plt.xlabel("era")
plt.ylabel("DOT")
plt.legend()
plt.savefig("imgs/validator_payout_over_era.png",dpi=300)
"""