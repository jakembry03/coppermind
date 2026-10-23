The __init__ method (for a class) serves as the initializer (or constructor) for a Python class, and it runs automatically whenever you create a new instance of that class. It's primary purpose is to set up the initial state of the object, and assign values to its properties (attributes)

Without the __init__ method, every class would start empty.

Ex:

    class SmartPhone:

        def __init__(self, brand, model, storage_gb):
            self.brand = brand
            self.model = model
            self.storage_gb = storage_gb
            self.battery_level = 100

Key things to remember:
The first parameter of __init__ is always self. It acts as a temporary placeholder representing the specific boject that is currently being made, allowing Python to attach variables directly to it.

