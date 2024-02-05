# High-Level Specification of the 3SF Protocol [WIP]

This folder contains an initial high-level specification of the 3SF protocol.

## Status

The current specification is just a start and is therefore rather incomplete.

## Intent

This high-level specification aims to specify the external behavior of a node implementing the 3SF protocol.

Intuitively, the external behavior corresponds to the messages sent and the canonical chain exposed by a node in response to a given sequence of input events (messages received and time updates).

This specification is not concerned with computational efficiency.
However, every function must be computable within a finite, but potentially unbounded, amount of time.

Computational efficiency is intended to be handled by lower-level specifications _implementing_ this high-level specification.
Intuitively, a specification $S1$ implements a specification $S2$ if any external behavior specified by specification $S1$ is also an external behavior of specification $S2$.
A more formal definition is provided below.

## How to Read the Specification

The dummy decorator `@Event` is used to identify the Python functions that specify the behavior in response to specific external events.

For example, the following Python function specifies how the node should behave when the node receives a Propose message.

```python
@Event
def on_received_propose(propose: SignedProposeMessage, nodeState: NodeState) -> NewNodeStateAndMessagesToTx:
    ...
```

In the above, `nodeState` corresponds to the current state of a node.
The value returned is a `dataclass` with the following three fields:

- `state`: the new state of the node in response to receiving the Propose message `propose`
- `proposeMessagesToTx`: the set, possibly empty, of Propose messages that the node must send in response  to receiving the Propose message `propose`
- `voteMessagesToTx`: the set, possibly empty, of Vote messages that the node must send in response to  to receiving the Propose message `propose`


