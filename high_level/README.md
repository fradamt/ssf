# High-Level Specification of the 3SF Protocol [WIP]

This folder contains an initial high-level specification of the 3SF protocol.

## Status

The current specification is just a start and is therefore rather incomplete.

## Intent

This high-level specification aims to specify the external behavior of a node implementing the 3SF protocol.

Intuitively, the external behavior corresponds to the messages sent and the canonical chain exposed by a node in response to a given sequence of input events (messages received and time updates).

This specification is not concerned with computational efficiency at all.
However, every function must be computable within a finite, but potentially unbounded, amount of time.

Computational efficiency is intended to be handled by lower-level specifications _implementing_ this high-level specification.
Intuitively, a specification $S1$ implements a specification $S2$ if any external behavior specified by specification $S1$ is also an external behavior of specification $S2$.

Note that it is admitted for a specification $S1$ implementing a specification $S2$ to extend the data carried by each message.
In this case, intuitively, a specification $S1$ implements a specification $S2$ if any external behavior specified by specification $S1$, _with the portion of data added to each message by $S1$ being removed_, is also an external behavior of specification $S2$.

A more formal definition is provided below.

## How to Read the Specification

### Files

- `3sf_high_level.py` is the "entry" point of the specification. It includes all the event handlers.
- `helpers.py` contains all of the helper functions used by `3sf_high_level.py`.
- `data_structures.py` contains all the data structure definitions.
- `stubs.`pyi` contains functions that have not yet been defined.
- `formal_verification_annotations.py` include the definition of all the annotations used to aid the formal verification of this specification.

### Event Handlers

The dummy decorator `@Event` is used to identify the Python functions that specify the behavior in response to specific external events.

For example, the following Python function specifies how the node should behave when the node receives a Propose message.

```python
@Event
def on_received_propose(propose: SignedProposeMessage, nodeState: NodeState) -> NewNodeStateAndMessagesToTx:
    ...
```

In the above, `nodeState` corresponds to the current state of a node.
The value returned is a `@dataclass NewNodeStateAndMessagesToTx` instance with the following three fields:

- `state`: the new state of the node in response to receiving the Propose message `propose`
- `proposeMessagesToTx`: the set, possibly empty, of Propose messages that the node must send in response  to receiving the Propose message `propose`
- `voteMessagesToTx`: the set, possibly empty, of Vote messages that the node must send in response to  to receiving the Propose message `propose`

## General Rules Used in Writing the Python Code

### Hard Rules

1. Use only immutable data structures. For composite data structures that never need to be manipulated during any function, use `@dataclass(frozen=True)`. For the composite data structures that need to be manipulated during the execution of some of the functions, base them off the `PRecord` class from the [`pyrsistent`](https://pypi.org/project/pyrsistent/) library. This is to use `PRecord`s only when strictly necessary because, as of today, MyPy cannot typecheck `PRecord`s, but it can typecheck `@dataclass`es.

2. Reduce the usage of Pythonic code as much as possible. This is to have a spec with very simple semantics and therefore reduce the risk of possible misinterpretations. As a consequence of this principle, the following rules have been followed:
    1. For all the files, except for `data_structure.py` and `pythonic_code_generic.py`, use only the following features of the Python language
       1. Function definitions
       2. `if` statements
       3. `for` statements
       4. lambdas
    2. Relegate all of the code that needs features of the Python language outside of those listed above to the file  `pythonic_code_generic.py` except for data structures definition which are placed in the file `data_structure.py`.


### Soft Rules

1. Employ functions effectively to encapsulate the semantics of operations. This is to improve readability. For example, rather than using `nodeState.blocks[hash]` throughout the code to retrieve a block with hash `hash`, define and use the function `get_block_from_hash(Hash, NodeState)` which better captures the semantics.

## General Rules Used in Writing this High-Level Specification

1. Add a field to `NodeState` only if it cannot be computed from the others. 

### Formally

<!-- The behavior of a node is specified as a Labelled Transition System $LTS = (S, S_0, I, O, P, T, L)$ where:

- $S$ is the set, possibly infinite, of states that the node can be in
- $S_0 \subseteq S$ is the set of possible initial states
- $I$ is the set, possibly infinite, of input events
- $O$ is the set, possibly infinite, of output messages
- $P$ is the set, possibly infinite, of atomic propositions associated with each state
- $T \subseteq S \times I \times S \times 2^O$ is the transition relation
- $L: S \to 2^P$ is the labelling function

A node starts in one of the possible initial states $S_0$.
A node in state $s_s$, on input event $i \in I$, it can atomically move to any state $s_d$ and output any finite set of messages $M_O$ such that that $(s_s, i, s_d, M_O) \in T$.

An execution path $\pi$ of $LTS$ is any possibly infinite sequence of states, input events $\pi = s_0 i_0 o_0 s_1 i_1 o_1 \cdots s_k i_k o_k s_{k+1}$ such that
- $s_o \in S_0$
- $\forall i \in [0, k]: (s_i, i_i, s_{i+1}, o_i) \in T$.

The external behavior $E(\pi)$ of an execution path $\pi = s_0 i_0 o_0 s_1 i_1 o_1 \cdots s_k i_k o_k s_{k+1}$ corresponds to the execution path $\pi$ with each state replaced by its label, i.e., $E(\pi) = \pi = L(s_0) i_0 o_0 L(s_1) i_1 o_1 \cdots L(s_k) i_k o_k L(s_{k+1})$.
Let $\Pi_{LTS}$ be the set of all possible paths of the labelled transition system $LTS$.
Then the external behaviour specified by $LTS$ is $E_{LTS} := \bigcup_{\pi \in \Pi} E(\pi)$. -->


The behavior of a node is specified by a Deterministic Labelled Transition System (DLTS) $(S, s_0, I, O, t, E, v)$ where:

- $S$ is the set, possibly infinite, of states that the node can be in
- $s_0 \in S$ is the initial state
- $I$ is the set, possibly infinite, of input events
- $O$ is the set, possibly infinite, of output messages
- $t: (S \times I) \to (S \times 2^O)$ is the transition function which is defined for all elements of $S \times I$ and it guarantees that for any $s \in S$ and $i \in I$, it outputs a tuple $(s_d, M_O) = t(s, i)$ where $M_O$ is finite
- $E$ is the set, possibly infinite, of externally visible states
- $v: S \to E$ is the external view function which is defined for all elements of $S$

A node starts in state $s_0$ and then it progresses as follows:
From any state $s_s$ on input event $i \in I$ with $t(s_s, i) = (s_d, M_O)$, it atomically transitions to state $s_d$ and outputs the finite set of messages $M_O$.

An execution path $\pi$ of a DLTS $\mathcal{D} = (S, s_0, I, O, t, E, v)$ is an infinite alternating sequence of states, input events and output messages $\pi = \langle s_0, i_0, o_0, s_1, i_1, o_1, s_2, \cdots  \rangle$ such that $\forall i \geq 0:  (s_{i+1}, o_i) = t(s_i, i_i)$.

The external behavior $E(\pi)$ of an execution path $\pi = \langle s_0, i_0, o_0, s_1, i_1, o_1, s_2, \ldots  \rangle$ corresponds to the execution path $\pi$ with each state mapped to its corresponding externally visible state, i.e., $B(\pi) =  \langle v(s_0), i_0, o_0, v(s_1), i_1, o_1, v(s_2), \ldots \rangle$.
Let $\Pi_\mathcal{{D}}$ be the set of all possible paths of the DLTS $\mathcal{D}$.
Then the external behaviour specified by $\mathcal{D}$ is $B(\mathcal{D}) := \bigcup_{\pi \in \Pi_\mathcal{D}} B(\pi)$.

A mapping between a DLTS $\mathcal{D}^L = (S^L, s_0^L, I^L, O^L, t^L, E^L, v^L)$ and DLTS $\mathcal{D}^H = (S^H, s_0^H, I^H, O^H, t^H, E^H, v^H)$ is a triple $M = (m_I, m_O, m_S)$ where $m_I: I^L \to I_H$, $m_O: O^L \to O^H$ and $m_S: S^L \to S^H$ are all surjective functions.

In the context of this specification, a DLTS $\mathcal{D}^L = (S^L, s_0^L, I^L, O^L, t^L, E^L, v^L)$ _implements_ a DLTS $\mathcal{D}^H = (S^H, s_0^H, I^H, O^H, t^H, E^H, v^H)$ according to the mapping $(m_I, m_O, m_S)$ iff:

<!-- 1. $M_E(v^L(s_0^L)) = v^H(s_0^H)$ -->

1. $\forall s_s^L, s_d^L \in S^L, i^L \in I^L, M_O^L \in 2^{O^L}: t^L(s_s^L, i^L) = (s_d^L, M_O^L) \implies t^H(m_S(s_s^L), m_I(i^L)) = (m_S(s_d^L), m_O(M_O^L))$.
2. $\forall e^L \in E^L : |\{v^H(m_S(s^L)) \mid s^L \in S^L \land v^L(s^L) = e^L\}| = 1$

Given condition 2 above, it is possible to define $M_E: E^L \to E^H$ as $M_E(e^L) = v^H(m_S(s^L))$ for any $s^L \in {v^L}^{-1}(e^L)$ and we have that $\forall s^L \in S^L : v^H(m_S(s^L)) = M_E(v^L(s^L))$.


Given the requirements on $t^L$ being a total function and the surjectivity of each function in the mapping $M$, the above essentially defines the bisimulation relation $R$ between $\mathcal{D}^L$ and $\mathcal{D}^H$ as 

$R_I = \{ (s^L, i^L, s^H, i^H) \in S^L \times I^L  \times S^H \times I^H  \mid s^H=m_S(s^L) \land i^H = m_I(i^L)\}$

$R_O = \{ (s^L, o^L, s^H, o^H) \in S^L \times O^L \times S^H \times O^H \mid s^H=m_S(s^L)  \land o^H=m_O(o^L)\}$

Hence we have that
<!-- - $\forall (s_s^L, i^L, s_s^H, i^H) \in R_I, (s_d^L, o^L, s_d^H, o^H) \in R_O: t^L(s_s^L, i^L) = (s_d^L, o^L) \implies t^H(s_s^H, i^H) = (s_d^H, o^H)$ -->
- $\forall (s_s^L, i^L, s_s^H, i^H) \in R_I, s_d^L \in S^L, o^L \in O^L: t^L(s_s^L, i^L) = (s_d^L, o^L) \implies (\exists s_d^H \in S^H, o^H \in O^H: t^H(s_s^H, i^H) = (s_d^H, o^H) \land (s_d^L, o^L, s_d^H, o^H) \in R_O)$
- $\forall (s_s^L, i^L, s_s^H, i^H) \in R_I, s_d^H \in S^H, o^H \in O^H: t^H(s_s^H, i^H) = (s_d^H, o^H) \implies (\exists s_d^L \in S^L, o^L \in O^L: t^L(s_s^L, i^L) = (s_d^L, o^L) \land (s_d^H, o^H, s_d^L, o^L) \in R_O)$

Given a mapping $M=(m_I, m_O, m_S)$ between a DLTS $\mathcal{D}^L = (S^L, s_0^L, I^L, O^L, t^L, E^L, v^L)$ and DLTS $\mathcal{D}^H = (S^H, s_0^H, I^H, O^H, t^H, E^H, v^H)$, define $B^M(\pi)$ where $\pi = \langle s_0, i_0, o_0, s_1, i_1, o_1, s_2, \ldots  \rangle\in \Pi_{\mathcal{D}^L}$ as $B^M(\pi) = \langle v^H(m_S(s_0)), m_I(i_0), m_O(o_0), v^H(m_S(s_1)), m_I(i_1), m_O(o_1), v^H(m_S(s_2))\ldots \rangle$.

According to the definition above, if a DLTS $\mathcal{D}^L$ implements a DLTS $\mathcal{D}^H$ according to the mapping $M$, then $B^M(\mathcal{D}^L) = B(\mathcal{D}^H)$.


Let $v^{L \to H}:S^L \to E^H$ be defined as $v^{L \to H}(s^L) = v^H(m_S(s^L))$.



Let $\mathcal{I}^L$

A mapping between a DLTS $\mathcal{D}^L = (S^L, s_0^L, I^L, O^L, t^L, E^L, v^L)$ and DLTS $\mathcal{D}^H  = (S^H, s_0^H, I^H, O^H, t^H, E^H, v^H)$, let $M(\mathcal{D}^L)$ be the DLTS $(S^H, s_0^H, I^H, O^H, t, E^H, v^H)$ with:

- $t(s_d, i) = t^H(m_S($

#### The $LTS$ defined by this specification

The set $S$ of possible states corresponds to the domain of the type $\texttt{NodeState}$.

Each `@Event` annotation defines a specific subset of the input events and the transition relation.

Specifically, take the following piece of code.

```python
@Event
def foo(a_1: T1, a_2: T2, ..., a_k: TN, nodeState: NodeState) -> NewNodeStateAndMessagesToTx:
    ...
```
The code above defines:

- a subset of the input events $I_{\texttt{foo}} := \{\langle \texttt{foo}, a_1, a_2, \ldots, a_k \rangle \mid (a_1, a_2, \ldots, a_k) \in \texttt{T1} \times \texttt{T2} \times \cdots \times \texttt{TN} \} \subseteq I$. In the following, for any $i \in I_{\texttt{foo}}$, let $ipar(i) := a_1, a_2, \ldots, a_k$.
- a subset of the transition relations $T_{\texttt{foo}} := \left\{(s_s, i, \texttt{foo}(ipar(i), s_s)\texttt{.state}, \texttt{foo}(ipar(i), s_s)\texttt{.proposeMessagesToTx} \cup \texttt{foo}(ipar(i), s_s)\texttt{.voteMessagesToTx}) \mid i \in I_{\texttt{foo}}, s_s \in \texttt{NodeState} \right\} \subseteq T$


The set of input events $I$ defined by this specification corresponds to the union of the sets of events defined by each function annotated by `@Event`.
Similarly, the transition relation $T$ defined by this specification corresponds to the union of the transition relations defined by each function annotated by `@Event`.

Each `@Label` annotation defines a specific subset of the 
Specifically, take the following piece of code.

```python
@Label
def bar(nodeState: NodeState) -> T1:
    ...
```
The code above defines a subset of the atomic propositions $P_\texttt{bar} := \{\langle \texttt{bar}, a\rangle | a \in \texttt{T1}\}$
 the labelling function $L_\texttt{bar} := \{ \}$

The set of atomic propositions $P$ corresponds to the union of the subset of atomic propositions defined by each function annotated by `@Label`.
Let $\mathcal{L}$ be the set of all functions decorated by `@Label`.
Then, we have that the labelling function is defined as $L(s) := \{\ell(s) \mid \ell \in \mathcal{L} \}$.

The set of initial states $S_0$ defined by this specification corresponds to the singleton $\{\texttt{init()}\}$.
