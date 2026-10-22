raise ... from exc: Keeps the original error attached. You see the friendly message, but the full technical cause is still there in traceback when you're debugging.

Two separate try blocks:
Because there are two different failure stages. The first handles "couldn't get a response". The second handles "got a response, but it isn't shaped like we expected." ValueError covers invalid JSON, and KeyError/IndexError cover JSON that's missing the fields we need.

