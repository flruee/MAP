class Balance(GraphObject):
    __tablename__ = "balance"

    transferable = Property()
    reserved = Property()
    bonded = Property()
    unbonding = Property()

    previous_balance = RelatedTo("Balance")

    @staticmethod
    def create(transferable: int, reserved: int, bonded: int, unbonding: int,
               previous_balance: "Balance" = None) -> "Balance":
        balance = Balance(
            transferable=transferable,
            reserved=reserved,
            bonded=bonded,
            unbonding=unbonding
        )
        if previous_balance:
            balance.previous_balance.add(previous_balance)

        Balance.save(balance)
        return balance

    @staticmethod
    def createFromObject(balance: "Balance", previous_balance) -> "Balance":
        return Balance.create(balance.transferable, balance.reserved, balance.bonded, balance.unbonding,
                              previous_balance)

    @staticmethod
    def save(balance: "Balance"):
        Driver().get_driver().save(balance)