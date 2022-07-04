class Singleton(type):
    _instances = {}
    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]
        
class Driver(metaclass=Singleton):
    """
    This class passes the db driver around, couldn't think of a better way than a singleton 
    which breaks my heart.
    TODO: Find a better way to pass the driver around
    """
    

    def add_driver(self, driver):
        self.driver = driver
    def get_driver(self):
        return self.driver