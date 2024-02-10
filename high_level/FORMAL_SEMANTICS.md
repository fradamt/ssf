# Formal Semantics [Do not read. Still under review!]

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

An execution path $\pi$ of a DLTS $\mathcal{D} = (S, s_0, I, O, t, E, v)$ is an infinite alternating sequence of states, input events and output messages $\pi = \langle s_0, i_0, o_0, s_1, i_1, o_1, s_2, \cdots  \rangle$ such that $\forall j \geq 0:  (s_{j+1}, o_j) = t(s_j, i_j)$.
Let $\Pi_\mathcal{{D}}$ be the set of all possible paths of the DLTS $\mathcal{D}$.

The external behavior $\mathsf{EB}(\pi)$ of an execution path $\pi = \langle s_0, i_0, o_0, s_1, i_1, o_1, s_2, \ldots  \rangle$ corresponds to the execution path $\pi$ with each state mapped to its corresponding externally visible state, i.e., $\mathsf{EB}(\pi) =  \langle v(s_0), i_0, o_0, v(s_1), i_1, o_1, v(s_2), \ldots \rangle$.
Then the external behavior specified by $\mathcal{D}$ is $\mathsf{EB}(\mathcal{D}) := \bigcup_{\pi \in \Pi_\mathcal{D}} \mathsf{EB}(\pi)$.

A mapping between a DLTS $\mathcal{D}^L = (S^L, s_0^L, I^L, O^L, t^L, E^L, v^L)$ and a DLTS $\mathcal{D}^H = (S^H, s_0^H, I^H, O^H, t^H, E^H, v^H)$ is a triple $M = (m_I, m_O, m_S)$ where $m_I: I^L \to I^H$, $m_O: O^L \to O^H$ and $m_S: S^L \to S^H$ are all surjective functions.
For any $M_O \subseteq O^L$, $m_O(M_O)$ is defined as $m_O(M_O) := \{m_O(m) : m \in M_O \}$.

In the context of this specification, a DLTS $\mathcal{D}^L = (S^L, s_0^L, I^L, O^L, t^L, E^L, v^L)$ _implements_ a DLTS $\mathcal{D}^H = (S^H, s_0^H, I^H, O^H, t^H, E^H, v^H)$ according to the mapping $M=(m_I, m_O, m_S)$ iff:

<!-- 1. $M_E(v^L(s_0^L)) = v^H(s_0^H)$ -->

1. $m_S(s_0^L) = s_0^H$
2. $\forall s_s^L, s_d^L \in S^L, i^L \in I^L, M_O^L \subseteq O^L: t^L(s_s^L, i^L) = (s_d^L, M_O^L) \implies t^H(m_S(s_s^L), m_I(i^L)) = (m_S(s_d^L), m_O(M_O^L))$.
3. $\forall e^L \in E^L : |\{v^H(m_S(s^L)) : s^L \in S^L \land v^L(s^L) = e^L\}| = 1$

Intuitively, condition 1 states that the transition function $t^L$ relates source states, input events, destination states and output events like transition function $t^H$ does, modulo the mapping.
Given the requirements on $t^L$ being a total function and the surjectivity of each function in the mapping $M$, this implies that $t^L$ and $t^H$ are equivalent, modulo the mapping.

Condition 2 ensures that external states of $\mathcal{D}^L$ can be mapped to external states of $\mathcal{D}^H$.
Specifically, it is possible to define $M_E: E^L \to E^H$ as $M_E(e^L) = v^H(m_S(s^L))$ for any $s^L \in {v^L}^{-1}(e^L)$.
Hence, $\forall s^L \in S^L : v^H(m_S(s^L)) = M_E(v^L(s^L))$.

Given the requirements on $t^L$ being a total function and the surjectivity of each function in the mapping $M$, the above essentially defines the following [bisimulation](https://en.wikipedia.org/wiki/Bisimulation) relation $R=(R_I, R_O)$ between $\mathcal{D}^L$ and $\mathcal{D}^H$:

$R_I = \{ (s^L, i^L, s^H, i^H) \in S^L \times I^L  \times S^H \times I^H  : s^H=m_S(s^L) \land i^H = m_I(i^L)\}$

$R_O = \{ (s^L, o^L, s^H, o^H) \in S^L \times O^L \times S^H \times O^H : s^H=m_S(s^L)  \land o^H=m_O(o^L)\}$

Such a relation ensures the following bisumulation conditions:
<!-- - $\forall (s_s^L, i^L, s_s^H, i^H) \in R_I, (s_d^L, o^L, s_d^H, o^H) \in R_O: t^L(s_s^L, i^L) = (s_d^L, o^L) \implies t^H(s_s^H, i^H) = (s_d^H, o^H)$ -->
- $\forall (s_s^L, i^L, s_s^H, i^H) \in R_I, s_d^L \in S^L, o^L \in O^L: t^L(s_s^L, i^L) = (s_d^L, o^L) \implies (\exists s_d^H \in S^H, o^H \in O^H: t^H(s_s^H, i^H) = (s_d^H, o^H) \land (s_d^L, o^L, s_d^H, o^H) \in R_O)$
- $\forall (s_s^L, i^L, s_s^H, i^H) \in R_I, s_d^H \in S^H, o^H \in O^H: t^H(s_s^H, i^H) = (s_d^H, o^H) \implies (\exists s_d^L \in S^L, o^L \in O^L: t^L(s_s^L, i^L) = (s_d^L, o^L) \land (s_d^H, o^H, s_d^L, o^L) \in R_O)$

Given a mapping $M=(m_I, m_O, m_S)$ between a DLTS $\mathcal{D}^L = (S^L, s_0^L, I^L, O^L, t^L, E^L, v^L)$ and a DLTS $\mathcal{D}^H = (S^H, s_0^H, I^H, O^H, t^H, E^H, v^H)$, define $\mathsf{EB}^M(\pi)$ where $\pi = \langle s_0, i_0, o_0, s_1, i_1, o_1, s_2, \ldots  \rangle\in \Pi_{\mathcal{D}^L}$ as $\mathsf{EB}^M(\pi) = \langle v^H(m_S(s_0)), m_I(i_0), m_O(o_0), v^H(m_S(s_1)), m_I(i_1), m_O(o_1), v^H(m_S(s_2))\ldots \rangle$.

According to the definition above, if a DLTS $\mathcal{D}^L$ implements a DLTS $\mathcal{D}^H$ according to the mapping $M$, then $\mathsf{EB}^M(\mathcal{D}^L) = \mathsf{EB}(\mathcal{D}^H)$.

<!-- Let $v^{L \to H}:S^L \to E^H$ be defined as $v^{L \to H}(s^L) = v^H(m_S(s^L))$.

Let $\mathcal{I}^L$

A mapping between a DLTS $\mathcal{D}^L = (S^L, s_0^L, I^L, O^L, t^L, E^L, v^L)$ and DLTS $\mathcal{D}^H  = (S^H, s_0^H, I^H, O^H, t^H, E^H, v^H)$, let $M(\mathcal{D}^L)$ be the DLTS $(S^H, s_0^H, I^H, O^H, t, E^H, v^H)$ with:

- $t(s_d, i) = t^H(m_S($ -->

## The DLTS defined by this specification

### Set of states, set of input events, set of output messages and transition function

The set of states, set of input events, set of output messages and transition function are all dependant on the function decorator `@Event`.

All functions decorated by `@Event` must have the same return type
and such a type must be a `@dataclass(frozen=True)` with one field named `state` and all other fields of type `PSet`.

Let `@Event` be applied to the function `foo` below and let its return type be `NewNodeStateAndMessagesToTx`.

```python
@dataclass(frozen=True)
class NewNodeStateAndMessagesToTx:
    state: NodeState
    messages_type_1_to_tx: PSet[T1]
    messages_type_2_to_tx: PSet[T2]
    ...
    messages_type_n_to_tx: PSet[TN]

@Event
def foo(a_1: T1, a_2: T2, ..., a_k: TN, node_state: NodeState) -> NewNodeStateAndMessagesToTx:
    ...
```

The code above provides the following definitions.

#### Set of States

The set $S$ of possible states corresponds to the domain of the type of the field `state` of `NewNodeStateAndMessagesToTx`, i.e. the domain of `NodeState`.

#### Output Messages

The set $O$ of possible output messages corresponds to the union of the domains of the types parametrizing `PSet` in all of the fields of `NewNodeStateAndMessagesToTx` except for the `state` field.

Considering the code above, this corresponds to the union of the domain of they types`T1`, `T2`, $\ldots$, `TN`.

#### Input Events and Transition Function

Each `@Event` annotation specifically defines a disjoint subset of the input events and the partial transition function dealing with such a subset of the input events.

A function like `foo` in the code above defines:

- a subset of the input events $I_{\texttt{foo}} := \{\langle \texttt{foo}, a_1, a_2, \ldots, a_k \rangle : (a_1, a_2, \ldots, a_k) \in \texttt{T1} \times \texttt{T2} \times \cdots \times \texttt{TN} \} \subseteq I$.
<!-- In the following, for any $i \in I_{\texttt{foo}}$, let $par_\texttt{foo}(i) := a_1, a_2, \ldots, a_k$. -->
- the partial transition function <br/> $t_\texttt{foo}(s, a_1, a_2, \ldots, a_k) := (\texttt{foo}(a_1, a_2, \ldots, a_k, s)\texttt{.state}, \bigcup_{\texttt{f} \in (\mathit{fields}(\texttt{NodeState}) \setminus \{\texttt{state}\})} \texttt{foo}(a_1, a_2, \ldots, a_k, s)\texttt{.f} )$<br/>where $\mathit{fields}(\texttt{NodeState})$ corresponds to the set of fields of the class `NodeState`.

The set of input events $I$ defined by this specification corresponds to the union of the sets of events defined by each function annotated by `@Event`.

The transition function is then defined as $t(s, i) = t_\texttt{foo}(s,  a_1, a_2, \ldots, a_k)$ if $i = \langle \texttt{foo}, a_1, a_2, \ldots, a_k \rangle$.

### Initial State

The initial state $s_0$ corresponds to the value return by the function annotated with `@Init`.

### External States and View Function

Each function decorated by `@View` defines a specific subset of the external state set and the partial external view function dealing with such a subset.

Specifically, take the following piece of code.

```python
@View
def bar(node_state: NodeState) -> T1:
    ...
```

The code above defines:

- the subset of the external states $E_\texttt{bar} := \{\langle \texttt{bar}, a\rangle | a \in \texttt{T1}\}$
- the partial view function $v_\texttt{bar}(s) := \langle \texttt{bar}, \texttt{bar}(s) \rangle$

Let $\mathit{VF}$ be the set of all functions annotated by `@View`.
The set of external states is then defined as $E := \dot{\prod}_{f \in \mathit{VF}} E_f$ where $\dot{\prod}$ represents the unordered product of sets.

The external view function is defined as $v(s) := \{v_f(s) : f \in \mathit{VF} \}$.

## Specification of Mappings between Low-Level and High-Level specifications

The decorators `@MapState`, `@MapEvent` and `@MapOutputMessage` are used to define the mapping $M=(m_I, m_O, m_S)$ between a lower-level spec and a higher-level specification as detailed below.

### States

The decorator `@MapState` is used to define the mapping between the lower-level spec states and the higher-level spec states.

```python
@MapState
def foo(l_state: LowNodeState) -> HighNodeState:
    ...
```

The code above defines the state mapping function $m_S(s) := \texttt{foo}(s)$.

### Input Events

The decorator `@MapEvent` is used to define the partial event mapping between the lower-level spec input events and the higher-level spec input events.

```python
@MapEvent
def low_event_name(a_1: LT1, a_2: LT2, ..., a_k: LTN) -> tuple[str, HT1, HT2, ..., HTN]:
    ...
```

The set of all functions decorated via `@MapEvent` defines the input event mapping function as $m_I(i) := \texttt{low\_eventname}(a_1, a_2, \ldots, a_k)$ if $i = \langle \texttt{loweventname}, a_1, a_2, \ldots, a_k \rangle$.

### Output Events

The decorator `@MapOutputMessage` is used to define the mapping between lower-level spec messages and higher-level spec messages.

```python
@MapOutputMessage
def foo(l_out_message: LowOutputMessage1) -> HighOutputMessage1:
    ...
```

For any lower-level spec output message $o$, let $\mathit{mf}(o)$ be the Python function with decorator `@MapOutputMessage` such that $o$ is in the domain of its input parameter type.

Then the set of all functions decorated by `@MapOutputMessage` defines the output message mapping fuction
$m_O(o) := \mathit{mf}(o)(o)$.
