class Account(GraphObject):
    __primarykey__ = "address"

    address = Property()
    account_index = Property()
    nonce = Property()
    reward_destination = Property()

    has_balances = RelatedTo("Balance")
    current_balance = RelatedTo("Balance")
    transfer_to = RelatedTo("Account")
    controls = RelatedTo("Account")
    is_validator = RelatedTo("Validator")
    is_nominator = RelatedTo("Nominator")

    def get_current_balance(self):
        triples = list(self.current_balance.triples())
        if not len(triples):
            balance = Balance.create(0, 0, 0, 0)
        else:
            balance = triples[0][-1]

        return balance

    @staticmethod
    def create(address: str):
        account = Account(
            address=address
        )
        null_balance = Balance.create(0, 0, 0, 0)
        account.has_balances.add(null_balance)
        account.current_balance.add(null_balance)
        Account.save(account)
        return account

    @staticmethod
    def get(address: str):
        return Account.match(Driver().get_driver(), address).first()

    @staticmethod
    def save(account: "Account"):
        Driver().get_driver().save(account)

    @staticmethod
    def get_treasury():
        treasury = Account.match(Driver().get_driver(), treasury_address).first()
        if not treasury:
            treasury = Account.create(treasury_address)
        return treasury

    def update_balance(self, block_number=None, other_account: "Account" = None, transferable=0, reserved=0, bonded=0,
                       unbonding=0):

        last_balance = self.get_current_balance()

        last_balance.transferable += transferable
        last_balance.reserved += reserved
        last_balance.bonded += bonded
        last_balance.unbonding += unbonding

        from_balance = Balance.createFromObject(last_balance, last_balance)

        self.has_balances.add(from_balance)
        self.current_balance.remove(last_balance)
        self.current_balance.add(from_balance)

        if other_account is not None and block_number is not None:
            self.transfer_to.add(other_account, {"block_number": block_number})

        Account.save(self)