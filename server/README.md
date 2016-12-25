TODO:

- Update all connections upon disconnected bot, not only when trying to send to that bot fails.  Use 'select'
    - currently detects disconnection after 2nd failed send (as customary with the protocol, would be nice to improve this)
- determine cause of occasional error: [Errno 32] Broken pipe
- terminal prompt give current directory
- stall terminal prompt if response expected (difficult)
- consider threaded bots to send commands to groups of bots at once