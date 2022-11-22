import pandas as pd
import matplotlib.pyplot as plt


def plot(data_x, data_y,label,x_label, y_label, title, figure_index):
    ax = fig.add_subplot(ROWS, COLUMNS,figure_index)
    ax.plot(data_x, data_y, "k-",label=label)
    ax.set_xlabel(x_label)
    ax.set_ylabel(y_label)
    ax.set_title(title)
    ax.legend()

ROWS = 2
COLUMNS = 2
fig = plt.figure(figsize=(10,10))
df = pd.read_csv("data/aggregator.csv")
print(df.head())

plot(df["block_number"], df["total_staked"], label="staked", x_label="block",y_label="DOT",title="Cumulative stakes over time",figure_index=1)
plot(df["block_number"], df["total_accounts"], label="accounts", x_label="block", y_label="n_accounts", title="Cumulative accounts over time",figure_index=2)
plot(df["block_number"], df["total_transfers"], label="transfers", x_label="block", y_label="n_transfers", title="Cumulative transfers over time",figure_index=3)
plot(df["block_number"], df["total_extrinsics"], label="extrinsics", x_label="block", y_label="n_extrinsics", title="Cumulative extrinsics over time",figure_index=4)
#plot(df["block_number"], df["total_events"], label="events", x_label="block", y_label="n_events", title="Cumulative events over time")
fig.savefig(f"imgs/cumulative_aggregator.png",dpi=300)

df = df[::-1]
df2 = df.diff()
fig = plt.figure(figsize=(10,10))
plot(df["block_number"], df2["total_staked"], label="diff staked", x_label="block", y_label="new stakes", title="delta staked",figure_index=1)
plot(df["block_number"], df2["total_accounts"], label="diff account", x_label="block", y_label="new accounts", title="delta account",figure_index=2)
plot(df["block_number"], df2["total_transfers"], label="diff transfer", x_label="block", y_label="new transfers", title="delta transfers",figure_index=3)
plot(df["block_number"], df2["total_extrinsics"], label="diff extrinsics", x_label="block", y_label="new extrinsics", title="delta extrinsics",figure_index=4)
#plot(df["block_number"], df2["total_events"], label="diff events", x_label="block", y_label="new events", title="delta events")
fig.savefig(f"imgs/delta_aggregator.png",dpi=300)

#df2 = df.diff()

#plot(df["block_number"].iloc[4900000:5000000], df2["total_transfers"].iloc[4900000:5000000], label="diff transfer", x_label="block", y_label="new transfers", title="exa boi")
