# Polkadot events/functions

##  [ParaInherent](https://w3f.github.io/parachain-implementers-guide/runtime/parainherent.html)

This module is responsible for providing all data given to the runtime by the block author to the various parachains modules. The entry-point is mandatory, in that it must be invoked exactly once within every block, and it is also "inherent", in that it is provided with no origin by the block author. The data within it carries its own authentication; i.e. the data takes the form of signed statements by validators. If any of the steps within fails, the entry-point is considered as having failed and the block will be invalid.

This module does not have the same initialization/finalization concerns as the others, as it only requires that entry points be triggered after all modules have initialized and that finalization happens after entry points are triggered. Both of these are assumptions we have already made about the runtime's order of operations, so this module doesn't need to be initialized or finalized by the Initializer.

There are a couple of important notes to the operations in this inherent as they relate to disputes.

1. We don't accept bitfields or backed candidates if in "governance-only" mode from having a local dispute conclude on this fork.
2. When disputes are initiated, we remove the block from pending availability. This allows us to roll back chains to the block before blocks are included as opposed to backing. It's important to do this before processing bitfields.
3. Inclusion::collect_disputed is kind of expensive so it's important to gate this on whether there are actually any new disputes. Which should be never.
4. And we don't accept parablocks that have open disputes or disputes that have concluded against the candidate. It's important to import dispute statements before backing, but this is already the case as disputes are imported before processing bitfields.