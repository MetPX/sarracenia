import pytest

#useful for debugging tests
class debug():
    def pretty(*things, **named_things):
        import pprint
        for t in things:
            pprint.PrettyPrinter(indent=2, width=200).pprint(t)
        for k,v in named_things.items():
            print(str(k) + ":")
            pprint.PrettyPrinter(indent=2, width=200).pprint(v)