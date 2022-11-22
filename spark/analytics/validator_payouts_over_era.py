import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv("data/validator_pool_map3.csv")
df.drop(0,axis=0,inplace=True)

fig, ax1 = plt.subplots()
ax2 = ax1.twinx()
ax1.plot(df["era"], df["validator_payout"],"k-", label="validator payout")
ax1.plot(df["era"], df["treasury_payout"],"k--", label="treasury payout")
ax2.plot(df["era"], df["total_stake"],"k", label="total stake",linestyle="dotted")

ax1.set_xlabel("era")
ax1.set_ylabel("Payout in Planck")
ax2.set_ylabel("Stakes in Planck")
lines1, labels1 = ax1.get_legend_handles_labels()
lines2, labels2 = ax2.get_legend_handles_labels()
ax2.legend(lines1+lines2, labels1+labels2,loc=2)
plt.savefig("imgs/validator_payout_over_era.png",dpi=300)