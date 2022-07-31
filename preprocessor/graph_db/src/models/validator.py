class Validator(GraphObject):
    amount_staked = Property()
    self_staked = Property()
    nominator_staked = Property()

    has_nominator = RelatedTo("Nominator")
    account = RelatedFrom("Account", "IS_VALIDATOR")

    @staticmethod
    def get_account_from_validator(validator):
        # res1 =  Driver().get_driver().run("Match (v:Validator)<-[:IS_VALIDATOR]-(a:Account {address: '"+str(account.address)+"'}) return a")
        print(validator.account.triples())

    @staticmethod
    def get_from_account(account: "Account") -> "Validator":

        validator_list = list(account.is_validator.triples())

        if not len(validator_list):
            validator = Validator.create(account=account)
        else:
            validator = validator_list[0][-1]
        return validator

    @staticmethod
    def create(amount_staked=0, self_staked=0, nominator_staked=0, account: "Account" = None):
        validator = Validator(
            amount_staked=amount_staked,
            self_staked=self_staked,
            nominator_staked=nominator_staked
        )

        Validator.save(validator)
        account.is_validator.add(validator)
        Account.save(account)
        return validator

    @staticmethod
    def save(validator: "Validator"):
        Driver().get_driver().save(validator)
