from data_structures import *
from formal_verification_annotations import *
from pythonic_code_generic import *
from stubs import *
from helpers import *



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
def on_tick(nodeState: NodeState, time: int) -> NewNodeStateAndMessagesToTx:
    new_slot = get_slot_from_time(time, nodeState)
    new_phase = get_phase_from_time(time, nodeState)

    if new_slot != nodeState.current_slot or new_phase != nodeState.current_phase:
        nodeState = nodeState.set(current_slot=new_slot)
        nodeState = nodeState.set(current_phase=new_phase)

        if nodeState.current_phase == NodePhase.PROPOSE:
            return on_propose(nodeState)
        elif nodeState.current_phase == NodePhase.VOTE:
            return on_vote(nodeState)
        elif nodeState.current_phase == NodePhase.CONFIRM:
            return on_confirm(nodeState)
        else:
            return on_merge(nodeState)
    else:    
        return NewNodeStateAndMessagesToTx(
            state=nodeState,
            proposeMessages=set_get_empty(),
            voteMessages=set_get_empty()
        )

def on_propose(nodeState: NodeState) -> NewNodeStateAndMessagesToTx:

    proposer = get_proposer(nodeState)

    if proposer == nodeState.identity:
        nodeState = execute_view_merge(nodeState)

        signed_propose = sign_propose_message(
            ProposeMessage(
                block=get_new_block(nodeState),
                proposer_view=get_votes_to_include_in_propose_message_view(nodeState)
            ),
            nodeState
        )

        return NewNodeStateAndMessagesToTx(
            state=nodeState,
            proposeMessages=set_get_singleton(signed_propose),
            voteMessages=set_get_empty()
        )

    else:
        return NewNodeStateAndMessagesToTx(
            state=nodeState,
            proposeMessages=set_get_empty(),
            voteMessages=set_get_empty()
        )

def on_vote(nodeState: NodeState) -> NewNodeStateAndMessagesToTx:
    ch = get_head(nodeState)
    s_cand = set_add(
        filter_out_blocks_non_ancestor_of_block(
            ch,
            nodeState.s_cand,
            nodeState
        ),
        get_block_from_hash(get_highest_justified_checkpoint(nodeState).block_hash, nodeState)
    )

    bcand = set_pick_element(s_cand)
    for block in s_cand:
        if block.slot > bcand.slot:
            bcand = block

    k_deep_block = get_block_k_deep(ch, nodeState.configuration.k, nodeState)

    if not (
        is_ancestor_descendant_relationship(bcand, nodeState.chava, nodeState) and
        is_ancestor_descendant_relationship(k_deep_block, nodeState.chava, nodeState)
    ):
        newChAva: Block

        if bcand.slot >= k_deep_block.slot:
            newChAva = bcand
        else:
            newChAva = k_deep_block

        nodeState = nodeState.set(
            chAva=newChAva
        )
        
    signedVoteMessage = sign_vote_message(
        VoteMessage(
            slot=nodeState.current_slot,
            head_hash=block_hash(ch),
            ffg_source=get_highest_justified_checkpoint(nodeState),
            ffg_target=Checkpoint(
                block_hash=block_hash(nodeState.chava),
                chkp_slot=nodeState.current_slot,
                block_slot=nodeState.chava.slot
            )
        ),
        nodeState
    )
        
    return NewNodeStateAndMessagesToTx(
        state=nodeState,
        proposeMessages=set_get_empty(),
        voteMessages=set_get_singleton(signedVoteMessage)
    )

def on_confirm(nodeState: NodeState) -> NewNodeStateAndMessagesToTx:
    return NewNodeStateAndMessagesToTx(
        state=nodeState.set(
            s_cand = set_merge(
                nodeState.s_cand,
                filter_out_not_confirmed(
                    get_all_blocks(nodeState),
                    nodeState
                )
            )
        ),
        proposeMessages=set_get_empty(),
        voteMessages=set_get_empty()
    )
    
def on_merge(nodeState: NodeState) -> NewNodeStateAndMessagesToTx:
    return NewNodeStateAndMessagesToTx(
        state=execute_view_merge(nodeState),
        proposeMessages=set_get_empty(),
        voteMessages=set_get_empty()
    )

@Event
def on_received_propose(propose: SignedProposeMessage, nodeState: NodeState) -> NewNodeStateAndMessagesToTx:
    # nodeState = on_block_received(propose.message.block, nodeState)
    if nodeState.current_phase == NodePhase.PROPOSE: # Is this Ok or do we need to also include 4\Delta t + \Delta ?
        nodeState = nodeState.set(
            view_vote=nodeState.view_vote.union(propose.message.proposer_view),
        )
    
    return NewNodeStateAndMessagesToTx(
        state=nodeState,
        proposeMessages=set_get_empty(),
        voteMessages=set_get_empty()
    )

@Event
def on_block_received(block: Block, nodeState: NodeState) -> NewNodeStateAndMessagesToTx:
    return NewNodeStateAndMessagesToTx(
        state=nodeState.set(buffer_blocks = nodeState.buffer_blocks.set(block_hash(block), block)),
        proposeMessages=set_get_empty(),
        voteMessages=set_get_empty()
    )    

@Event  
def on_vote_received(vote: SignedVoteMessage, nodeState: NodeState) -> NewNodeStateAndMessagesToTx:
    return NewNodeStateAndMessagesToTx(
        state=nodeState.set(
            buffer_vote=
                set_add(
                    nodeState.buffer_vote,
                    vote
                )
        ),
        proposeMessages=set_get_empty(),
        voteMessages=set_get_empty()
    )
