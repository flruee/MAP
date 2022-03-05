# Polkadot events/functions

## [Polkadot lightpaper](https://polkadot.network/Polkadot-lightpaper.pdf)

A block is produced every 6 seconds.

tx_fee model:

- Weight fee
	- base weight accounts for the overhead of inclusion (e.g. signature verification)
	- call weight accounts for the time to execute the transaction
- length fee
- tip

The inclusion fee is deducted from the sender's account before transaction execution. A portion of the fee will go to the block author, and the remainder will go to the Treasury. This is 20% and 80%, respectively.

Block Limits and Transaction Priority
Blocks in Polkadot have both a maximum length (in bytes) and a maximum weight. Block producers will fill blocks with transactions up to these limits. A portion of each block - currently 25% - is reserved for critical transactions that are related to the chain's operation. Block producers will only fill up to 75% of a block with normal transactions. Some examples of operational transactions:

- Misbehavior reports
- Council operations
- Member operations in an election (e.g. renouncing candidacy)
Block producers prioritize transactions based on each transaction's total fee. Since a portion of the fee will go to the block producer, producers will include the transactions with the highest fees to maximize their reward.


## [PolkadotEvents](https://polkadot.js.org/docs/substrate/events/)

Extrinsics
= pieces of info that come from outside of chain. three categories:
-signed tx
signed transactions come from an account that has funds, and therefore Polkadot can charge a transaction fee as a way to prevent spam.
-unsigned tx
Unsigned transactions are for special cases where a user needs to submit an extrinsic from a key pair that does not control funds. For example, when users claim their DOT tokens after genesis, their DOT address doesn't have any funds yet, so that uses an unsigned transaction. Validators also submit unsigned transactions in the form of "heartbeat" messages to indicate that they are online. These heartbeats must be signed by one of the validator's session keys. Session keys never control funds. Unsigned transactions are only used in special cases because, since Polkadot cannot charge a fee for them, each one needs its own, custom validation logic.
-inherents.
inherents are pieces of information that are not signed or included in the transaction queue. As such, only the block author can add inherents to a block. Inherents are assumed to be "true" simply because a sufficiently large number of validators have agreed on them being reasonable. For example, Polkadot blocks include a timestamp inherent. There is no way to prove that a timestamp is true the way one proves the desire to send funds with a signature. Rather, validators accept or reject the block based on how reasonable they find the timestamp. In Polkadot, it must be within some acceptable range of their own system clocks.


Relay Chain:
The heart of Polkadot,
responsible for the
network’s security,
consensus and cross-chain
interoperability

Parachains:
Sovereign blockchains
that can have their own
tokens and optimize their
functionality for specific
use cases. To connect to
the Relay Chain, parachains
can pay as they go or
lease a slot for continuous
connectivity.

Bridges:
Special blockchains that
allow Polkadot shards
to connect to and
communicate with external
networks like Ethereum and
Bitcoin.

Validators:
Secure the Relay Chain by staking DOTs,
validating proofs from collators and
participating in consensus with other
validators.

Collators:
Maintain shards by collecting shard
transactions from users and producing
proofs for validators.

Nominators:
Secure the Relay Chain by selecting
trustworthy validators and staking
DOTs.
can nominate themselves as validator or someone else. However if nominated node misbehaves,
they lose dot aswell. One can un-nominate at any time. Unbonding period of 28 days on main, 7 days on kusama. Every era may be assigned different active nomination amongst validators you,
select. Validators can currently only have 256 nominators. Others will not receive rewards. Mapping computed offchain (& has to fit on single block). Rewards are "lazy" - i.e. one must actively claim rewards.


Fishermen:
Monitor the network and report bad
behavior to validators. Collators and
any parachain full node can perform
the fisherman role. 

Kusama: 
Testnet of Polkadot

Substrate:
Blockchain building framework. Allows for easy construction of Polkadot Parachain.

Planck:
smallest unit of DOT. A Planck's relation to DOT is like the relation of a Satoshi to Bitcoin.

Polkadot accounts:
Polkadot addresses always start with the number 1.
Kusama addresses always start with a capital letter, such as C D, F, G, H, J.
Generic Substrate addresses always start with the number 5.

Existential Deposit and Reaping:
When you generate an account (address), you only generate a key that lets you access it. The account does not exist yet on-chain. For that, it needs the existential deposit: 0.0000333333 KSM (on Kusama) or 1 DOT (on Polkadot mainnet).
Having an account go below the existential deposit causes that account to be reaped. The account will be wiped from the blockchain's state to conserve space, along with any funds in that address. You do not lose access to the reaped address - as long as you have your private key or recovery phrase, you can still use the address - but it needs a top-up of another existential deposit to be able to interact with the chain.
Transaction fees cannot cause an account to be reaped. Since fees are deducted from the account before any other transaction logic, accounts with balances equal to the existential deposit cannot construct a valid transaction. Additional funds will need to be added to cover the transaction fees.

Indices:
A Kusama or Polkadot address can have an index. An index is like a short and easy-to-remember version of an address. Claiming an index requires a deposit that is released when the index is cleared.
Index basically integer wo increased. Falls account reaped wird er freigeh. Possible to "freeze" index by placing deposit. Can never be reclaimed unless released by holding account. Only makes sense for index "69" and/or "420" HODL !!

There exist multi-sig accounts:
self-explanatory. They can define users + execution threshhold. I.e. alice, bob & charlie setup acc with thresh 2. --> alice & bob can execute tx w/o charlie. Cannot be altered after creation.
usecases:
acts as 2FA mechanism
Board decision
group participation

Issuing an extrinsic:
Extrinsics are pieces of information that come from outside the chain and are included in a block. Extrinsics can be one of three types: inherents, signed, and unsigned transactions.
Most extrinsics displayed on Polkadot-JS Apps are signed transactions. Inherits are non-signed and non-gossiped pieces of information included in blocks by the block author, such as timestamps, which are “true” because a sufficient number of validators have agreed about validity.
Unsigned transactions are information that does not require a signature but will require some sort of spam prevention, whereas signed transactions are issued by the originator account of a transaction which contains a signature of that account, which will be subject to a fee to include it on the chain.

Moonbeam/Moonriver
Moonbeam and its Kusama counterpart Moonriver are full EVM deployments with Ethereum RPC endpoints.
This means that the entire toolkit offered to other EVM chains (stacks like Hardhat, Remix, Truffle, Metamask, etc.) are available to Moonriver / Moonbeam users and developers, giving it a noticeable head start in attracting existing userbases.
Several dozen high profile teams are launching their products (or re-launching) on Moonriver / Moonbeam, however, it is essential to note that Moonbeam is an EVM chain and will therefore suffer from the same limitations as any other EVM chain in regards to customization and feature-richness of NFTs.
A notable advantage, however, is that Moonriver / Moonbeam is still a Substrate chain, meaning integration of custom pallets into the runtime is still possible, making NFT specific optimizations at the chain runtime level a reliable way to keep EVM compatibility of tools while at the same time optimizing storage and interactions for rich NFTs.


## [Polkadot Consensus](https://wiki.polkadot.network/docs/learn-consensus)


Voting on a referendum
To vote, a voter generally must lock their tokens up for at least the enactment delay period beyond the end of the referendum. This is in order to ensure that some minimal economic buy-in to the result is needed and to dissuade vote selling.

It is possible to vote without locking at all, but your vote is worth a small fraction of a normal vote, given your stake. At the same time, holding only a small amount of tokens does not mean that the holder cannot influence the referendum result, thanks to time-locking. 



## [Tool for decoding method data/hex-encoded call](https://polkadot.js.org/apps/#/extrinsics/decode)


##  [Polkadot Parachain Protocol Overview](https://w3f.github.io/parachain-implementers-guide/protocol-overview.html)


##  [ParaInherent](https://w3f.github.io/parachain-implementers-guide/runtime/parainherent.html)




This module is responsible for providing all data given to the runtime by the block author to the various parachains modules. The entry-point is mandatory, in that it must be invoked exactly once within every block, and it is also "inherent", in that it is provided with no origin by the block author. The data within it carries its own authentication; i.e. the data takes the form of signed statements by validators. If any of the steps within fails, the entry-point is considered as having failed and the block will be invalid.

This module does not have the same initialization/finalization concerns as the others, as it only requires that entry points be triggered after all modules have initialized and that finalization happens after entry points are triggered. Both of these are assumptions we have already made about the runtime's order of operations, so this module doesn't need to be initialized or finalized by the Initializer.

There are a couple of important notes to the operations in this inherent as they relate to disputes.

1. We don't accept bitfields or backed candidates if in "governance-only" mode from having a local dispute conclude on this fork.
2. When disputes are initiated, we remove the block from pending availability. This allows us to roll back chains to the block before blocks are included as opposed to backing. It's important to do this before processing bitfields.
3. Inclusion::collect_disputed is kind of expensive so it's important to gate this on whether there are actually any new disputes. Which should be never.
4. And we don't accept parablocks that have open disputes or disputes that have concluded against the candidate. It's important to import dispute statements before backing, but this is already the case as disputes are imported before processing bitfields.
