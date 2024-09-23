"""
Long running sleeps prevent Sarracenia from being shutdown cleanly in a
reasonable amount of time.

This implements a reusable sleep function that can be called from other parts
of the code to sleep for a long time, but can still be interrupted.
"""

import time

def interruptible_sleep(sleep_time:float, obj: object, stop_flag_name: str='_stop_requested', nap_time: float=5.0) -> bool:
    """ Sleep for sleep_time, divided up into shorter nap_time intervals.
        Pass a reference to an object that contains a boolean attribute named stop_flag_name. 
        Between each nap_time, the function will check if obj.stop_flag_name has become True.
        If the flag is False, it will continue sleeping, if True, it will abort the sleep.

         Args:
            sleep_time (float): total amount of time to sleep, if not interrupted
            obj (object): the object containing the boolean attribute named stop_flag_name
            stop_flag_name (str): the name of the boolean attribute in obj
            nap_time (float): default = 5.0, sleep in intervals of nap_time

        Returns:
            bool: ``True`` if the sleep **was** interrupted, ``False`` if it slept for the entire ``sleep_time`` 
                    time without interruption.
    """
    interrupted = False
    while sleep_time > 0 and not interrupted:
        time.sleep(min(nap_time, sleep_time))
        sleep_time -= nap_time
        interrupted = (hasattr(obj, stop_flag_name) and getattr(obj, stop_flag_name))
    return interrupted
