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
    new_slot = get_slot_from_time(time, node_state)
    new_phase = get_phase_from_time(time, node_state)

    if new_slot != node_state.current_slot or new_phase != node_state.current_phase:
        node_state = node_state.set(current_slot=new_slot)
        node_state = node_state.set(current_phase=new_phase)

        if node_state.current_phase == NodePhase.PROPOSE:
            return on_propose(node_state)
        elif node_state.current_phase == NodePhase.VOTE:
            return on_vote(node_state)
        elif node_state.current_phase == NodePhase.CONFIRM:
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

    proposer = get_proposer(node_state)

    if proposer == node_state.identity:
        node_state = execute_view_merge(node_state)

        signed_propose = sign_propose_message(
            ProposeMessage(
                block=get_new_block(node_state),
                proposer_view=get_votes_to_include_in_propose_message_view(node_state)
            ),
            node_state
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
    ch = get_head(node_state)
    s_cand = pset_add(
        filter_out_blocks_non_ancestor_of_block(
            ch,
            node_state.s_cand,
            node_state
        ),
        get_block_from_hash(get_highest_justified_checkpoint(node_state).block_hash, node_state)
    )

    bcand = pset_pick_element(s_cand)
    for block in s_cand:
        if block.slot > bcand.slot:
            bcand = block

    k_deep_block = get_block_k_deep(ch, node_state.configuration.k, node_state)

    if not (
        is_ancestor_descendant_relationship(bcand, node_state.chava, node_state) and
        is_ancestor_descendant_relationship(k_deep_block, node_state.chava, node_state)
    ):
        newChAva: Block

        if bcand.slot >= k_deep_block.slot:
            newChAva = bcand
        else:
            newChAva = k_deep_block

        node_state = node_state.set(
            chAva=newChAva
        )

    signedVoteMessage = sign_vote_message(
        VoteMessage(
            slot=node_state.current_slot,
            head_hash=block_hash(get_head(node_state)),
            ffg_source=get_highest_justified_checkpoint(node_state),
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
    return NewNodeStateAndMessagesToTx(
        state=execute_view_merge(node_state),
        proposeMessagesToTx=pset_get_empty(),
        voteMessagesToTx=pset_get_empty()
    )


@Event
def on_received_propose(propose: SignedProposeMessage, node_state: NodeState) -> NewNodeStateAndMessagesToTx:
    node_state = node_state.set(
        buffer_blocks=pmap_set(
            node_state.buffer_blocks,
            block_hash(propose.message.block), 
            propose.message.block)
        )

    if node_state.current_phase == NodePhase.PROPOSE:  # Is this Ok or do we need to also include 4\Delta t + \Delta ?
        node_state = node_state.set(
            view_vote=pset_merge(
                node_state.view_votes,
                from_pvector_to_pset(propose.message.proposer_view))
        )

    return NewNodeStateAndMessagesToTx(
        state=node_state,
        proposeMessagesToTx=pset_get_empty(),
        voteMessagesToTx=pset_get_empty()
    )


@Event
def on_block_received(block: Block, node_state: NodeState) -> NewNodeStateAndMessagesToTx:
    return NewNodeStateAndMessagesToTx(
        state=node_state.set(
            buffer_blocks=pmap_set(
                node_state.buffer_blocks,
                block_hash(block), 
                block)
            ),
        proposeMessagesToTx=pset_get_empty(),
        voteMessagesToTx=pset_get_empty()
    )


@Event
def on_vote_received(vote: SignedVoteMessage, node_state: NodeState) -> NewNodeStateAndMessagesToTx:
    return NewNodeStateAndMessagesToTx(
        state=node_state.set(
            buffer_vote=pset_add(
                node_state.buffer_votes,
                vote
            )
        ),
        proposeMessagesToTx=pset_get_empty(),
        voteMessagesToTx=pset_get_empty()
    )


@View
def finalized_chain(node_state: NodeState) -> PVector[Block]:
    return get_blockchain(
        get_block_from_hash(
            get_highest_finalized_checkpoint(node_state).block_hash,
            node_state
        ),
        node_state
    )


@View
def available_chain(node_state: NodeState) -> PVector[Block]:
    return get_blockchain(
        node_state.chava,
        node_state
    )
