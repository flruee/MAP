import pandas as pd
import matplotlib.pyplot as plt


def plot(data_x, data_y,label,x_label, y_label, title):
    fig,ax = plt.subplots()
    ax.plot(data_x, data_y, "k-",label=label)
    ax.set_xlabel(x_label)
    ax.set_ylabel(y_label)
    ax.set_title(title)
    ax.legend()
    fig.savefig(f"imgs/{title.replace(' ','_').lower()}.png",dpi=300)


df = pd.read_csv("data/aggregator.csv")
df2 = df.diff()

print(df2["total_transfers"].idxmax())

print(df2[df2["total_transfers"] > 100].index)