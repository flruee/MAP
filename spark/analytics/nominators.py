import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
df = pd.read_csv("data/nominator_rewards.csv")
df.columns = ["nominator","validator","reward","reward_destination","era","stake","validator_total_stake","validator_self_stake","validator_commission"]


def plot_hist(df):

    bins = np.logspace(0,18,1000)



    plt.hist(df["stake"],bins=bins )
    plt.axvline(1e10,c="r",ls="--")
    plt.xlabel("Planck")
    plt.ylabel("Count")
    plt.title(f"Staking distribution of nominators in log-log")
    plt.yscale("log")
    plt.xscale("log")
    plt.savefig("imgs/staking_distribution",dpi=300)

def plot_scatter(df):
    df2 = df2[df2["stake"]>0]
    df2 = df2[df2["reward"]>0]
    df2 = df2[df2["validator_commission"]==0]
    df2["stake"].dropna(inplace=True)
    df2["reward"].dropna(inplace=True)
    #sns.scatter(df["stake"], df["reward"])
    #plt.scatter(df["stake"], df["reward"])
    splot = sns.lmplot(x="stake", y="reward", scatter_kws={"s":1},
                    data=df2, fit_reg=False)
    splot.set(xscale="log",yscale="log")
    plt.title("Staking - reward (log-log)")
    plt.savefig("imgs/staking_reward_scatter",dpi=300)

def plot_commission_scatter(df):
    df2 = df[df["validator_commission"] > 0]
    df2 = df2[df2["stake"]>0]
    df2 = df2[df2["reward"]>0]
    splot = sns.lmplot(x="stake", y="reward", scatter_kws={"s":1},
                    data=df2, fit_reg=False)
    splot.set(xscale="log",yscale="log")
    plt.title("Staking - reward (log-log)")
    plt.show()

def plot_commission_hist(df):
    #bins = np.linspace(0,1000000000,10)


    commissions = df["validator_commission"] / 1e9
    plt.hist(commissions)#,bins=bins )

    #plt.axvline(1e10,c="r",ls="--")
    plt.xlabel("Commission")
    plt.ylabel("Count")
    plt.title(f"Commission distribution")
    plt.savefig("imgs/commission_distribution",dpi=300)
    
print(np.max(df["validator_commission"]))
plot_commission_hist(df)
