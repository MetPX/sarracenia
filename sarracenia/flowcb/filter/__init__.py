"""
a module that is focused on transforming data should be called a filter.
Filter plugins intended for after_accept(self, worklist) entry_point.

At that point:
Messages have been gathered, then passed through the accept and reject pattern matches.
One of the first callbacks is the nodupe, so that duplicate suppression may cause additional
rejections.

"""
pass
