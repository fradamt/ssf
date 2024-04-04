from data_structures import *
from formal_verification_annotations import *
from pythonic_code_generic import *
from stubs import *
from helpers import *

# @Init
# def init() -> NodeState:
#     return NodeState(
#         identity=NodeIdentity(),
#         current_phase = NodePhase.PROPOSE,
#         current_slot=0,
#         blocks=[],
#         configuration=Configuration(
#             delta=10,
#             genesis=Block(
#                 parent_hash="",
#                 body=BlockBody()
#             )
#         )
#     )


@Event
def on_tick(node_state: NodeState, time: int) -> NewNodeStateAndMessagesToTx:
    """
    Manages the transition of the system's state, making changes in both the current slot and the phase. 
    Upon initiating a new phase, it activates one of four distinct events based on the phase transition:
    - `on_propose`: Triggered at the start of a new slot, signaling that a designated proposer should submit a new block.
    - `on_vote`: Indicates that validators are now expected to cast their votes in support of a proposed block.
    - `on_confirm`: Calls for validators to update their set of confirmation candidates.
    - `on_merge`: Signals the integration of the current buffer contents into a validator's local view.
    """

    current_slot = get_slot(node_state)
    current_phase = get_phase(node_state)
    node_state = node_state.set(time=time)
    new_slot = get_slot(node_state)
    new_phase = get_phase(node_state)
    
    if new_slot != current_slot or new_phase != current_phase:
        if new_phase == NodePhase.PROPOSE:
            return on_propose(node_state)
        elif new_phase == NodePhase.VOTE:
            return on_vote(node_state)
        elif new_phase == NodePhase.CONFIRM:
            return on_confirm(node_state)
        else:
            return on_merge(node_state)
    else:
        return NewNodeStateAndMessagesToTx(
            state=node_state,
            proposeMessagesToTx=pset_get_empty(),
            voteMessagesToTx=pset_get_empty()
        )


def on_propose(node_state: NodeState) -> NewNodeStateAndMessagesToTx:
    """
    A validator acting as a proposer first merges its buffer with its local view using the `execute_view_merge` function. 
    This step prepares the validator to propose a new block, generated through `get_new_block`.
    Next, the proposer constructs a new proposal `signed_propose` by signing the block together with its local view. 
    Finally, the validator broadcasts such proposal.
    """
    proposer = get_proposer(node_state)

    if proposer == node_state.identity:

        node_state = update_justified_and_candidate(node_state)

        signed_propose = sign_propose_message(ProposeMessage(
                block=get_new_block(node_state),
                greatest_justified_checkpoint=node_state.greatest_justified_checkpoint,
                highest_candidate_block_hash=block_hash(node_state.highest_candidate_block)
            ),
            node_state,
        )

        return NewNodeStateAndMessagesToTx(
            state=node_state,
            proposeMessagesToTx=pset_get_singleton(signed_propose),
            voteMessagesToTx=pset_get_empty()
        )

    else:
        return NewNodeStateAndMessagesToTx(
            state=node_state,
            proposeMessagesToTx=pset_get_empty(),
            voteMessagesToTx=pset_get_empty()
        )


def on_vote(node_state: NodeState) -> NewNodeStateAndMessagesToTx:
    """
    A validator in the role of a voter begins by identifying the current tip of the canonical blockchain using the `get_head` function. 
    The validator then filters through its confirmation candidates, removing any that conflict with the `get_head` output, while also 
    including the greatest justified checkpoint.
    The candidate block, `bcand`, is determined as the max among the confirmation candidates and the greatest justified checkpoint. 
    The validator then considers the k deep prefix from the canonical chain's tip, referred to as `k_deep_block`, and compares it with `bcand`.
    The next step involves updating the validator's available chain, `node_state.chava`, to reflect the max between `bcand` and `k_deep_block`, provided neither are ancestors of `node_state.chava`. 
    Finally, the validator casts a vote, specifying the `get_greatest_justified_checkpoint` as the source checkpoint and defining the target checkpoint based on `node_state.chava`, the current slot, and the slot of `chAva`.
    """
    head = get_head(node_state)
    s_cand = pset_add(
        filter_out_blocks_non_ancestor_of_block(
            head,
            node_state.s_cand,
            node_state
        ),
        get_greatest_justified_block(node_state)
    )

    bcand = pset_max(s_cand, lambda b: b.slot)

    k_deep_block = get_block_k_deep(head, node_state.configuration.k, node_state)

    if not (
        is_ancestor_descendant_relationship(bcand, node_state.chava, node_state) and
        is_ancestor_descendant_relationship(k_deep_block, node_state.chava, node_state)
    ):
        node_state = node_state.set(
            chAva=pset_max(
                pset_merge(
                    pset_get_singleton(bcand),
                    pset_get_singleton(k_deep_block)
                ),
                lambda b: b.slot
            )
        )

    signedVoteMessage = sign_vote_message(
        VoteMessage(
            slot=node_state.current_slot,
            head_hash=block_hash(get_head(node_state)),
            ffg_source=get_greatest_justified_checkpoint(node_state),
            ffg_target=Checkpoint(
                block_hash=block_hash(node_state.chava),
                chkp_slot=node_state.current_slot,
                block_slot=node_state.chava.slot
            )
        ),
        node_state
    )

    return NewNodeStateAndMessagesToTx(
        state=node_state,
        proposeMessagesToTx=pset_get_empty(),
        voteMessagesToTx=pset_get_singleton(signedVoteMessage)
    )


def on_confirm(node_state: NodeState) -> NewNodeStateAndMessagesToTx:
    """
    A validator refines its set of confirmation candidates, specifically, the set `s_cand` of blocks that garnered over two-thirds 
    of the votes during the NodePhase.VOTE stage.    
    """
    return NewNodeStateAndMessagesToTx(
        state=node_state.set(
            s_cand=pset_merge(
                node_state.s_cand,
                filter_out_not_confirmed(
                    get_all_blocks(node_state),
                    node_state
                )
            )
        ),
        proposeMessagesToTx=pset_get_empty(),
        voteMessagesToTx=pset_get_empty()
    )


def on_merge(node_state: NodeState) -> NewNodeStateAndMessagesToTx:
    """
    """
    return NewNodeStateAndMessagesToTx(
        state=update_justified_and_candidate(node_state),
        proposeMessagesToTx=pset_get_empty(),
        voteMessagesToTx=pset_get_empty()
    )


@Event
def on_propose_received(propose: SignedProposeMessage, node_state: NodeState) -> NewNodeStateAndMessagesToTx:
    """
    A validator merges the proposer's view with its own local view upon receiving a proposal within the timeframe from 
    4Δt to 4Δt+Δ, preparing it for the phase NodePhase.VOTE.    
    """
    node_state = node_state.set(
        blocks=pmap_set(
            node_state.blocks,
            block_hash(propose.message.block),
            propose.message.block)
    )

    if node_state.current_phase == NodePhase.PROPOSE:
        proposed_checkpoint = propose.message.greatest_justified_checkpoint
        if is_justified_checkpoint(proposed_checkpoint, node_state):
            if is_greater_checkpoint(proposed_checkpoint, node_state.greatest_justified_checkpoint):
                node_state = node_state.set(
                    greatest_justified_checkpoint=proposed_checkpoint
                )

            greatest_justified_block = get_greatest_justified_block(node_state)
            if not is_ancestor_descendant_relationship(greatest_justified_block,
                                            node_state.highest_candidate_block, 
                                            node_state):
                node_state = node_state.set(
                    highest_candidate_block=greatest_justified_block
                )

        proposed_candidate = get_block_from_hash(propose.message.highest_candidate_block_hash, node_state)
        if is_recent_quorum_for_block(propose.message.block.votes, proposed_candidate, node_state):
            if is_ancestor_descendant_relationship(node_state.highest_candidate_block,
                                                proposed_candidate, 
                                                node_state):
                node_state = node_state.set(
                    highest_candidate_block=block_hash(propose.message.highest_candidate_block_hash)
                )

    return NewNodeStateAndMessagesToTx(
        state=node_state,
        proposeMessagesToTx=pset_get_empty(),
        voteMessagesToTx=pset_get_empty()
    )


@Event
def on_block_received(block: Block, node_state: NodeState) -> NewNodeStateAndMessagesToTx:
    """
    A validator, upon receiving a `block` at any moment, adds it to its local view `node_state.blocks`.    
    """
    return NewNodeStateAndMessagesToTx(
        state=node_state.set(
            blocks=pmap_set(
                node_state.blocks,
                block_hash(block),
                block)
        ),
        proposeMessagesToTx=pset_get_empty(),
        voteMessagesToTx=pset_get_empty()
    )


@Event
def on_vote_received(vote: SignedVoteMessage, node_state: NodeState) -> NewNodeStateAndMessagesToTx:
    """
    A validator, upon receiving a `vote` at any moment, adds it to its local view `node_state.votes`, 
    and records the time of reception in `node_state.vote_receival_times`. 
    """

    node_state = node_state.set(
            votes=pset_add(
                node_state.votes,
                vote
            )
        )
    node_state = node_state.set(
        vote_receival_times=pmap_set(
            node_state.vote_receival_times,
            vote,
            node_state.time)
    )
    return NewNodeStateAndMessagesToTx(
        state=node_state,
        proposeMessagesToTx=pset_get_empty(),
        voteMessagesToTx=pset_get_empty()
    )


@View
def finalized_chain(node_state: NodeState) -> PVector[Block]:
    """
    The finalized chain is the chain output by the finalizing component of the protocol.
    """
    return get_blockchain(
        get_block_from_hash(
            get_greatest_finalized_checkpoint(node_state).block_hash,
            node_state
        ),
        node_state
    )


@View
def available_chain(node_state: NodeState) -> PVector[Block]:
    """
    The available chain `node_state.chava` is the chain output by the dynamically available component of the protocol.
    """
    return get_blockchain(
        node_state.chava,
        node_state
    )
