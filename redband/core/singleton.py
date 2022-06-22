# class Singleton(type):
#     def __init__(cls, name, bases, dict):
#         super(Singleton, cls).__init__(name, bases, dict)
#         cls.instance = None

#     def __call__(cls, *args, **kwargs):
#         if cls.instance is None:
#             cls.instance = super(Singleton, cls).__call__(*args, **kwargs)
#         return cls.instance


# # TODO: this can be used to define a ConfigStore, but I feel like I don't need a full-complexity config store here ??
