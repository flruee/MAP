import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv("data/validator_pool_rewards.csv")
df.drop(0,axis=0,inplace=True)
plt.plot(df["era"], df["validator_payout"],"g-", label="validator payout")
plt.plot(df["era"], df["treasury_payout"],"r--",label="treasury payout")
plt.xlabel("era")
plt.ylabel("DOT")
plt.legend()
plt.savefig("imgs/era_rewards.png")