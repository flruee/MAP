# Extrinsics
Redenomination of DOT in block 1_248_328
Treasury address: 13UVJyLnbVp9RBZYFwFGyDvVd1y27Tt8tkntv6Q7JVPhFsTB

# Fee
The last 3 events of each transaction (maybe not) contain the fee.
the third to last event is useless and foreshadows (*MENACING*) the next.
the second to last event Treasury(Deposit) is the value for the treasury (0.8 of the fee)
the last event Balance(Deposit) is the value for the validator (0.2 of the fee + tip)
Note: if an extrinsic contains a tip the tip is added to the last event

## Balances

### Transfer
Create Transfer
add amount to transfer
Select accounts.
Select current balance of accounts.
create two new balances.
Create relations:
 * Extrinsic->transfer
 * transfer->fromBalance
 * transfer->toBalance
 * change current_balance of accounts
 * add last_balance to current_balance
 * add balance to has_balance
 * add Transfer Type




### Deposit




