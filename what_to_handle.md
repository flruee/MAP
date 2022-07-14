# Extrinsics
Redenomination of DOT in block 1_248_328
Treasury address: 13UVJyLnbVp9RBZYFwFGyDvVd1y27Tt8tkntv6Q7JVPhFsTB

good account: 14d2kv44xf9nFnYdms32dYPKQsr5C9urbDzTz7iwU8iHb9az

# Fee
The last 3 events of each transaction (maybe not) contain the fee.
the third to last event is useless and foreshadows (*MENACING*) the next.
the second to last event Treasury(Deposit) is the value for the treasury (0.8 of the fee)
the last event Balance(Deposit) is the value for the validator (0.2 of the fee + tip)
Note: if an extrinsic contains a tip the tip is added to the last event


## assets TBH
## Balances Implemented

### Transfer (1349471,1349473,1349474) Implemented
Create Transfer
add amount to transfer
Select accounts.
Select current balance of accounts.
create two new balances.
Create relations:
 * Extrinsic->transfer
 * transfer->fromBalance
 * transfer->toBalance
 * transfer->validatorBalance
 * transfer->treasuryBalance
 * change current_balance of accounts
 * add last_balance to current_balance
 * add balance to has_balance
 * add Transfer Type

### TransferAll (alias of Transfer, 10855617, 10855625, 10856155) Implemented

### TransferKeepAlive Implemented

## Bounty
### claimBounty (alias of transfer, need to take data from events) (found only once: 6535806)

### proposeBounty TBH

## childBounty
### addChildBounty TBH

## contracts

### call TBH

### instantiateContract TBH

### instantiateWithCode TBH

## democracy

### propose TBH

### vote TBH

## identity


## society
### bid TBH

### vouch TBH

## staking

### bond (currency shuffle, ) 6498556 Implemented
from transferable to bonded.


### bondExtra (see bonded) 6499896

### rebond 6497272
### setController 4474128
### withdrawUnbonded (currency shuffle)
use Staking(withdrawn) event to migrate bonded to transferable

## Tips TBH

## Treasury
### proposeSpend (transferable -> reserved)





### Deposit



# Conspiracy
Stash: 14d2kv44xf9nFnYdms32dYPKQsr5C9urbDzTz7iwU8iHb9az aka Coinstudio
Controller: 12MnpxhC2cSRTWXiwX8jwxegwXZNuxTZsJMCLfCLfCiUpWeu



# handle ValidatorPool  (328745 --> Era index 0)
* if grandpa(newAuthorities) then Validatorpool starts and last Validatorpool ends.
* connect new to old via previous
* in old Validatorpool set attribute "to_block" to current block - 1 .

## Finding Validators
1. author -> validator
2. some validators might not mine, but will surely claim their reward -> use the `Staking(PayoutStakers)` extrinsic (called from any Account DANGERZONE) it will contain the address of validatorStash and validatorpool era.


    * create Validator node with stash account.
    * connect Validator node to validatorPool of era.
    * use `staking(Rewarded)` event to get the nominator addresses and their reward for era.
    * create Nominator node and connect it to account (check if stash or not).
    * connect Nominator and Validator Node.   
 
# 


"(Babe,report_equivocation_unsigned)"
"(Balances,force_transfer)"
"(Balances,set_balance)"
"(Balances,transfer)"
"(Balances,transfer_all)"
"(Balances,transfer_keep_alive)"
"(Bounties,claim_bounty)"
"(Bounties,propose_bounty)"
"(Claims,attest)"
"(Claims,claim)"
"(Claims,claim_attest)"
"(Claims,mint_claim)"
"(Claims,move_claim)"
"(Council,close)"
"(Council,propose)"
"(Council,vote)"
"(Democracy,blacklist)"
"(Democracy,cancel_proposal)"
"(Democracy,cancel_queued)"
"(Democracy,cancel_referendum)"
"(Democracy,clear_public_proposals)"
"(Democracy,delegate)"
"(Democracy,note_imminent_preimage)"
"(Democracy,note_preimage)"
"(Democracy,propose)"
"(Democracy,reap_preimage)"
"(Democracy,remove_other_vote)"
"(Democracy,remove_vote)"
"(Democracy,second)"
"(Democracy,undelegate)"
"(Democracy,unlock)"
"(Democracy,vote)"
"(ElectionProviderMultiPhase,submit)"
"(ElectionProviderMultiPhase,submit_unsigned)"
"(ElectionsPhragmen,remove_member)"
"(ElectionsPhragmen,remove_voter)"
"(ElectionsPhragmen,renounce_candidacy)"
"(ElectionsPhragmen,submit_candidacy)"
"(ElectionsPhragmen,vote)"
"(FinalityTracker,final_hint)"
"(Grandpa,report_equivocation_unsigned)"
"(Identity,add_registrar)"
"(Identity,add_sub)"
"(Identity,cancel_request)"
"(Identity,clear_identity)"
"(Identity,kill_identity)"
"(Identity,provide_judgement)"
"(Identity,quit_sub)"
"(Identity,remove_sub)"
"(Identity,rename_sub)"
"(Identity,request_judgement)"
"(Identity,set_account_id)"
"(Identity,set_fee)"
"(Identity,set_fields)"
"(Identity,set_identity)"
"(Identity,set_subs)"
"(ImOnline,heartbeat)"
"(Indices,claim)"
"(Indices,force_transfer)"
"(Indices,free)"
"(Indices,freeze)"
"(Indices,transfer)"
"(Multisig,approve_as_multi)"
"(Multisig,as_multi)"
"(Multisig,cancel_as_multi)"
"(ParaInherent,enter)"
"(Parachains,set_heads)"
"(PhragmenElection,remove_voter)"
"(PhragmenElection,submit_candidacy)"
"(PhragmenElection,vote)"
"(Poll,vote)"
"(Proxy,add_proxy)"
"(Proxy,announce)"
"(Proxy,anonymous)"
"(Proxy,proxy)"
"(Proxy,proxy_announced)"
"(Proxy,remove_announcement)"
"(Proxy,remove_proxies)"
"(Proxy,remove_proxy)"
"(Purchase,create_account)"
"(Purchase,payout)"
"(Purchase,set_payment_account)"
"(Purchase,set_statement)"
"(Purchase,set_unlock_block)"
"(Purchase,update_validity_status)"
"(Scheduler,cancel)"
"(Session,purge_keys)"
"(Session,set_keys)"
"(Staking,bond)"
"(Staking,bond_extra)"
"(Staking,cancel_deferred_slash)"
"(Staking,chill)"
"(Staking,chill_other)"
"(Staking,force_new_era)"
"(Staking,force_unstake)"
"(Staking,kick)"
"(Staking,nominate)"
"(Staking,payout_stakers)"
"(Staking,reap_stash)"
"(Staking,rebond)"
"(Staking,set_controller)"
"(Staking,set_invulnerables)"
"(Staking,set_payee)"
"(Staking,set_validator_count)"
"(Staking,submit_election_solution)"
"(Staking,submit_election_solution_unsigned)"
"(Staking,unbond)"
"(Staking,validate)"
"(Staking,withdraw_unbonded)"
"(Sudo,set_key)"
"(Sudo,sudo)"
"(Sudo,sudo_as)"
"(Sudo,sudo_unchecked_weight)"
"(System,kill_storage)"
"(System,remark)"
"(System,remark_with_event)"
"(TechnicalCommittee,close)"
"(TechnicalCommittee,propose)"
"(TechnicalCommittee,vote)"
"(TechnicalMembership,change_key)"
"(TechnicalMembership,swap_member)"
"(Timestamp,set)"
"(Tips,close_tip)"
"(Tips,report_awesome)"
"(Tips,retract_tip)"
"(Tips,tip)"
"(Tips,tip_new)"
"(Treasury,accept_curator)"
"(Treasury,close_tip)"
"(Treasury,propose_bounty)"
"(Treasury,propose_spend)"
"(Treasury,report_awesome)"
"(Treasury,retract_tip)"
"(Treasury,tip)"
"(Treasury,tip_new)"
"(Utility,as_derivative)"
"(Utility,batch)"
"(Utility,batch_all)"
"(Vesting,force_vested_transfer)"
"(Vesting,vest)"
"(Vesting,vest_other)"
"(Vesting,vested_transfer)"