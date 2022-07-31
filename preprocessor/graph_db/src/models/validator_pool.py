

class ValidatorPool(GraphObject):
    __primarykey__ = "era"

    era = Property()
    total_staked = Property()
    total_reward = Property()

    hasValidators = RelatedTo("Validator")
    from_block = RelatedTo("Block")
    to_block = RelatedTo("Block")
    previous_validator_pool = RelatedTo("ValidatorPool")

    @staticmethod
    def get(era):
        return ValidatorPool.match(Driver().get_driver(), era).first()

    @staticmethod
    def create(era, block, total_staked=0, total_reward=0):
        validatorpool = ValidatorPool(
            era=era,
            total_staked=total_staked,
            total_reward=total_reward
        )
        validatorpool.from_block.add(block)
        ValidatorPool.save(validatorpool)
        return validatorpool

    @staticmethod
    def save(validatorpool: "ValidatorPool"):
        Driver().get_driver().save(validatorpool)
