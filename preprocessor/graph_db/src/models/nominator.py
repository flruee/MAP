
class Nominator(GraphObject):
    total_staked = Property()
    reward = Property()

    @staticmethod
    def get_from_account(account: "Account") -> "Nominator":
        nominator_list = list(account.is_nominator.triples())
        if not len(nominator_list):
            nominator = Nominator.create(account=account)
        else:
            nominator = nominator_list[0][-1]
        return nominator

    @staticmethod
    def create(total_staked=0, reward=0, account:"Account"=None):
        nominator = Nominator(
            total_staked=total_staked,
            reward=reward
        )

        Nominator.save(nominator)
        account.is_nominator.add(nominator)
        Account.save(account)
        return nominator

    @staticmethod
    def save(nominator: "Nominator"):
        Driver().get_driver().save(nominator)