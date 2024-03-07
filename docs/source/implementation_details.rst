Implementation Details
######################

The following information is useful for PartCAD contributors.

================================
Internal geometry representation
================================

PartCAD maintains parts as OCCT objects. Similar to ``wrapped`` objects found
in ``CadQuery`` and ``build123d``.

===========
Parallelism
===========

1. Asynchronous at heart

  PartCAD is designed to run most of its logic as coroutines in the asyncio's event loop.

2. Threads for the muscle

  There is a separate thread pool created for long-running procedures that are CPU intensive.
  The number of threads matches the number of CPU cores minus 1 (if there is more than 1).

  Coroutines can spawn tasks on the thread pool. Tasks on the thread pool can't call coroutines that use asyncio.Lock().

3. Digest external code properly

  Separate processes are spawned (optionally, in a sandboxed environment) to process third-party CAD-as-code parts and assemblies.
  One thread is consumed in the thread pool to wait for each such process to complete (to cap the number of CPU cores occupied).

4. Friendly face

  To make it apparent to external users, all externally visible coroutines have names that end with "_async".
  Each such coroutine is accompanied by a synchronous wrapper (which does not have "_async" in its name).
