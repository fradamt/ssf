from pyrsistent import PSet, PMap, PVector

from data_structures import *
from formal_verification_annotations import *
from pythonic_code_generic import *
from stubs import *


def get_slot_from_time(time: int, nodeState: NodeState) -> int:
    return time // (4 * nodeState.configuration.delta)


def get_phase_from_time(time: int, nodeState: NodeState) -> NodePhase:
    time_in_slot = time % (4 * nodeState.configuration.delta)

    if time_in_slot >= 3 * nodeState.configuration.delta:
        return NodePhase.MERGE
    elif time_in_slot >= 2 * nodeState.configuration.delta:
        return NodePhase.CONFIRM
    elif time_in_slot >= nodeState.configuration.delta:
        return NodePhase.VOTE
    else:
        return NodePhase.PROPOSE


def genesis_checkpoint(nodeState: NodeState) -> Checkpoint:
    return Checkpoint(
        block_hash=block_hash(nodeState.configuration.genesis),
        chkp_slot=0,
        block_slot=0
    )


def has_block_hash(block_hash: Hash, nodeState: NodeState) -> bool:
    return pmap_has(nodeState.blocks, block_hash)


def get_block_from_hash(block_hash: Hash, nodeState: NodeState) -> Block:
    Requires(has_block_hash(block_hash, nodeState))
    return pmap_get(nodeState.blocks, block_hash)


def has_parent(block: Block, nodeState: NodeState) -> bool:
    return has_block_hash(block.parent_hash, nodeState)


def get_parent(block: Block, nodeState: NodeState) -> Block:
    Requires(has_parent(block, nodeState))
    return get_block_from_hash(block.parent_hash, nodeState)


def get_all_blocks(nodeState: NodeState) -> PSet[Block]:
    return pmap_values(nodeState.blocks)


def is_complete_chain(block: Block, nodeState: NodeState) -> bool:
    if block == nodeState.configuration.genesis:
        return True
    elif not has_parent(block, nodeState):
        return False
    else:
        return is_complete_chain(get_parent(block, nodeState), nodeState)


def get_blockchain(block: Block, nodeState: NodeState) -> PVector[Block]:
    Requires(is_complete_chain(block, nodeState))
    if block == nodeState.configuration.genesis:
        return pvector_of_one_element(block)
    else:
        return pvector_concat(
            pvector_of_one_element(block),
            get_blockchain(get_parent(block, nodeState), nodeState)
        )


def is_ancestor_descendant_relationship(ancestor: Block, descendant: Block, nodeState: NodeState) -> bool:
    if ancestor == descendant:
        return True
    elif descendant == nodeState.configuration.genesis:
        return False
    else:
        return (
            has_parent(descendant, nodeState) and
            is_ancestor_descendant_relationship(
                ancestor,
                get_parent(descendant, nodeState),
                nodeState
            )
        )


def validator_set_weight(validators: PSet[NodeIdentity], validatorBalances: ValidatorBalances) -> int:
    total_weight = 0
    for validator in validators:
        if validator in validatorBalances:
            total_weight = total_weight + validatorBalances[validator]

    return total_weight


def get_set_FFG_targets(votes: PSet[SignedVoteMessage]) -> PSet[Checkpoint]:
    return pset_map(
        lambda vote: vote.message.ffg_target,
        votes
    )

def is_FFG_vote_in_support_of_checkpoint_justification(vote: SignedVoteMessage, checkpoint: Checkpoint, nodeState: NodeState) -> bool:
    return (
        valid_vote(vote, nodeState) and
        vote.message.ffg_target.chkp_slot == checkpoint.chkp_slot and
        is_ancestor_descendant_relationship(
            get_block_from_hash(checkpoint.block_hash, nodeState),
            get_block_from_hash(vote.message.ffg_target.block_hash, nodeState),
            nodeState) and
        is_ancestor_descendant_relationship(
            get_block_from_hash(vote.message.ffg_source.block_hash, nodeState),
            get_block_from_hash(checkpoint.block_hash, nodeState),
            nodeState) and
        is_justified_checkpoint(vote.message.ffg_source, nodeState)
    )


def filter_out_FFG_votes_not_in_FFG_support_of_checkpoint_justification(votes: PSet[SignedVoteMessage], checkpoint: Checkpoint, nodeState: NodeState) -> PSet[SignedVoteMessage]:
    return pset_filter(lambda vote: is_FFG_vote_in_support_of_checkpoint_justification(vote, checkpoint, nodeState), votes)


def get_validators_in_FFG_support_of_checkpoint_justification(votes: PSet[SignedVoteMessage], checkpoint: Checkpoint, nodeState: NodeState) -> PSet[NodeIdentity]:
    return pset_map(
        lambda vote: vote.sender,
        filter_out_FFG_votes_not_in_FFG_support_of_checkpoint_justification(votes, checkpoint, nodeState)
    )


def is_justified_checkpoint(checkpoint: Checkpoint, nodeState: NodeState) -> bool:
    if checkpoint == genesis_checkpoint(nodeState):
        return True
    else:
        if not has_block_hash(checkpoint.block_hash, nodeState) or not is_complete_chain(get_block_from_hash(checkpoint.block_hash, nodeState), nodeState):
            return False

        validatorBalances = get_validator_set_for_slot(get_block_from_hash(checkpoint.block_hash, nodeState), checkpoint.block_slot, nodeState)

        FFG_support_weight = validator_set_weight(get_validators_in_FFG_support_of_checkpoint_justification(nodeState.view_vote, checkpoint, nodeState), validatorBalances)
        tot_validator_set_weight = validator_set_weight(pmap_keys(validatorBalances), validatorBalances)

        return FFG_support_weight * 3 >= tot_validator_set_weight * 2


def filter_out_non_justified_checkpoint(checkpoints: PSet[Checkpoint], nodeState: NodeState) -> PSet[Checkpoint]:
    return pset_filter(lambda checkpoint: is_justified_checkpoint(checkpoint, nodeState), checkpoints)


def get_justified_checkpoints(nodeState: NodeState) -> PSet[Checkpoint]:
    return pset_add(
        filter_out_non_justified_checkpoint(get_set_FFG_targets(nodeState.view_vote), nodeState),
        genesis_checkpoint(nodeState)
    )


def get_highest_justified_checkpoint(nodeState: NodeState) -> Checkpoint:
    highest_justified_checkpoint = genesis_checkpoint(nodeState)

    for checkpoint in get_justified_checkpoints(nodeState):
        if checkpoint.chkp_slot > highest_justified_checkpoint.chkp_slot:
            highest_justified_checkpoint = checkpoint

    return highest_justified_checkpoint


def is_FFG_vote_linking_to_a_checkpoint_in_next_slot(vote: SignedVoteMessage, checkpoint: Checkpoint, nodeState: NodeState) -> bool:
    return (
        valid_vote(vote, nodeState) and
        vote.message.ffg_source == checkpoint and
        vote.message.ffg_target.chkp_slot == checkpoint.chkp_slot + 1
    )


def filter_out_FFG_vote_not_linking_to_a_checkpoint_in_next_slot(checkpoint: Checkpoint, nodeState: NodeState) -> PSet[SignedVoteMessage]:
    return pset_filter(lambda vote: is_FFG_vote_linking_to_a_checkpoint_in_next_slot(vote, checkpoint, nodeState), nodeState.view_vote)


def get_validators_in_FFG_votes_linking_to_a_checkpoint_in_next_slot(checkpoint: Checkpoint, nodeState) -> PSet[NodeIdentity]:
    return pset_map(
        lambda vote: vote.sender,
        filter_out_FFG_vote_not_linking_to_a_checkpoint_in_next_slot(checkpoint, nodeState)
    )


def is_finalized_checkpoint(checkpoint: Checkpoint, nodeState: NodeState) -> bool:
    if not is_justified_checkpoint(checkpoint, nodeState):
        return False

    validatorBalances = get_validator_set_for_slot(get_block_from_hash(checkpoint.block_hash, nodeState), checkpoint.block_slot, nodeState)
    FFG_support_weight = validator_set_weight(get_validators_in_FFG_votes_linking_to_a_checkpoint_in_next_slot(checkpoint, nodeState), validatorBalances)
    tot_validator_set_weight = validator_set_weight(pmap_keys(validatorBalances), validatorBalances)

    return FFG_support_weight * 3 >= tot_validator_set_weight * 2


def filter_out_non_finalized_checkpoint(checkpoints: PSet[Checkpoint], nodeState: NodeState) -> PSet[Checkpoint]:
    return pset_filter(lambda checkpoint: is_finalized_checkpoint(checkpoint, nodeState), checkpoints)


def get_finalized_checkpoints(nodeState: NodeState) -> PSet[Checkpoint]:
    return pset_add(
        filter_out_non_finalized_checkpoint(get_set_FFG_targets(nodeState.view_vote), nodeState),
        genesis_checkpoint(nodeState)
    )


def get_highest_finalized_checkpoint(nodeState: NodeState) -> Checkpoint:
    highest_finalized_checkpoint = genesis_checkpoint(nodeState)

    for checkpoint in get_finalized_checkpoints(nodeState):
        if checkpoint.chkp_slot > highest_finalized_checkpoint.chkp_slot:
            highest_finalized_checkpoint = checkpoint

    return highest_finalized_checkpoint


def filter_out_blocks_non_ancestor_of_block(block: Block, blocks: PSet[Block], nodeState: NodeState) -> PSet[Block]:
    return pset_filter(
        lambda b: is_ancestor_descendant_relationship(b, block, nodeState),
        blocks
    )


def filter_out_GHOST_votes_non_descendant_of_block(block: Block, votes: PSet[SignedVoteMessage], nodeState: NodeState) -> PSet[SignedVoteMessage]:
    return pset_filter(
        lambda vote:
            has_block_hash(vote.message.head_hash, nodeState) and
            is_ancestor_descendant_relationship(
                block,
                get_block_from_hash(vote.message.head_hash, nodeState),
                nodeState
            ),
        votes
    )


def is_GHOST_vote_for_block_in_blockchain(vote: SignedVoteMessage, blockchainHead: Block, nodeState: NodeState) -> bool:
    return (
        has_block_hash(vote.message.head_hash, nodeState) and
        is_ancestor_descendant_relationship(
            get_block_from_hash(vote.message.head_hash, nodeState), 
            blockchainHead, 
            nodeState)
    )


def filter_out_GHOST_votes_not_for_blocks_in_blockchain(votes: PSet[SignedVoteMessage], blockchainHead: Block, nodeState: NodeState) -> PSet[SignedVoteMessage]:
    return pset_filter(
        lambda vote: is_GHOST_vote_for_block_in_blockchain(vote, blockchainHead, nodeState),
        votes
    )


def filter_out_GHOST_votes_for_blocks_in_blockchain(votes: PSet[SignedVoteMessage], blockchainHead: Block, nodeState: NodeState) -> PSet[SignedVoteMessage]:
    return pset_filter(
        lambda vote: not is_GHOST_vote_for_block_in_blockchain(vote, blockchainHead, nodeState),
        votes
    )


def is_GHOST_vote_expired(vote: SignedVoteMessage, nodeState: NodeState) -> bool:
    return vote.message.slot + nodeState.configuration.eta < nodeState.current_slot


def filter_out_expired_GHOST_votes(votes: PSet[SignedVoteMessage], nodeState: NodeState) -> PSet[SignedVoteMessage]:
    return pset_filter(
        lambda vote: is_GHOST_vote_expired(vote, nodeState),
        votes
    )


def filter_out_non_LMD_GHOST_votes(votes: PSet[SignedVoteMessage]) -> PSet[SignedVoteMessage]:
    lmd: PMap[NodeIdentity, SignedVoteMessage] = pmap_get_empty()

    for vote in votes:
        if not pmap_has(lmd, vote.sender) or vote.message.slot > pmap_get(lmd, vote.sender).message.slot:
            lmd = pmap_set(lmd, vote.sender, vote)

    return pmap_values(lmd)


def is_equivocating_GHOST_vote(vote: SignedVoteMessage, nodeState: NodeState) -> bool:
    for vote_check in nodeState.view_vote:
        if (
            vote_check.message.slot == vote.message.slot and
            vote_check.sender == vote.sender and
            vote_check.message.head_hash != vote.message.head_hash
        ):
            return True

    return False


def filter_out_GHOST_equivocating_votes(votes: PSet[SignedVoteMessage], nodeState: NodeState) -> PSet[SignedVoteMessage]:
    return pset_filter(
        lambda vote: not is_equivocating_GHOST_vote(vote, nodeState),
        votes
    )


def valid_vote(vote: SignedVoteMessage, nodeState: NodeState) -> bool:
    return (
        verify_vote_signature(vote) and
        has_block_hash(vote.message.head_hash, nodeState) and
        is_complete_chain(get_block_from_hash(vote.message.head_hash, nodeState), nodeState) and
        pmap_has(get_validator_set_for_slot(get_block_from_hash(vote.message.head_hash, nodeState), vote.message.slot, nodeState), vote.sender) and
        is_ancestor_descendant_relationship(
            get_block_from_hash(vote.message.ffg_source.block_hash, nodeState), 
            get_block_from_hash(vote.message.ffg_target.block_hash, nodeState), 
            nodeState) and
        is_ancestor_descendant_relationship(
            get_block_from_hash(vote.message.ffg_target.block_hash, nodeState), 
            get_block_from_hash(vote.message.head_hash, nodeState), 
            nodeState) and
        vote.message.ffg_source.chkp_slot < vote.message.ffg_target.chkp_slot and
        has_block_hash(vote.message.ffg_source.block_hash, nodeState) and
        get_block_from_hash(vote.message.ffg_source.block_hash, nodeState).slot == vote.message.ffg_source.block_slot and
        has_block_hash(vote.message.ffg_target.block_hash, nodeState) and
        get_block_from_hash(vote.message.ffg_target.block_hash, nodeState).slot == vote.message.ffg_target.block_slot
    )


def filter_out_invalid_votes(votes: PSet[SignedVoteMessage], nodeState: NodeState) -> PSet[SignedVoteMessage]:
    return pset_filter(
        lambda vote: valid_vote(vote, nodeState),
        votes
    )


def get_votes_included_in_blockchain(block: Block, nodeState: NodeState) -> PSet[SignedVoteMessage]:
    if block == nodeState.configuration.genesis or not has_block_hash(block.parent_hash, nodeState):
        return block.votes
    else:
        return pset_merge(block.votes, get_votes_included_in_blockchain(get_block_from_hash(block.parent_hash, nodeState), nodeState))


def get_votes_included_in_blocks(blocks: PSet[Block]) -> PSet[SignedVoteMessage]:
    votes: PSet[SignedVoteMessage] = pset_get_empty()

    for block in blocks:
        votes = pset_merge(votes, block.votes)

    return votes


def votes_to_include_in_proposed_block(nodeState: NodeState) -> PSet[SignedVoteMessage]:
    """
    The votes to include in a proposed block are all those with a GHOST vote for a block in the chain
    of the proposed block that have not already been included in such a chain
    """
    head_block = get_head(nodeState)
    votes_for_blocks_in_canonical_chain = filter_out_GHOST_votes_not_for_blocks_in_blockchain(
        filter_out_invalid_votes(nodeState.view_vote, nodeState),
        head_block,
        nodeState
    )

    return votes_for_blocks_in_canonical_chain.difference(
        get_votes_included_in_blockchain(head_block, nodeState)
    )


def get_new_block(nodeState: NodeState) -> Block:
    head_block = get_head(nodeState)
    return Block(
        parent_hash=block_hash(head_block),
        body=get_block_body(nodeState),
        slot=nodeState.current_slot,
        votes=votes_to_include_in_proposed_block(nodeState)
    )


def get_votes_to_include_in_propose_message_view(nodeState: NodeState) -> PVector[SignedVoteMessage]:
    """
    The votes to include in the view shared via a Propose message are all valid, non-expired GHOST votes
    for a block descendant of the greatest justified checkpoint but that are not in the chain of the proposed block
    (as those in the chain of the proposed block are already included in the proposed block itself via, see `votes_to_include_in_proposed_block`)
    """
    head_block = get_head(nodeState)
    return from_set_to_pvector(
        filter_out_GHOST_votes_for_blocks_in_blockchain(
            filter_out_GHOST_votes_non_descendant_of_block(
                get_block_from_hash(get_highest_justified_checkpoint(nodeState).block_hash, nodeState),
                filter_out_expired_GHOST_votes(
                    filter_out_invalid_votes(nodeState.view_vote, nodeState),
                    nodeState
                ),
                nodeState
            ),
            head_block,
            nodeState
        )
    )


def get_GHOST_weight(block: Block, votes: PSet[SignedVoteMessage], nodeState: NodeState, validatorBalances: ValidatorBalances) -> int:
    weight = 0

    for vote in votes:
        if (
            has_block_hash(vote.message.head_hash, nodeState) and  # Perhaps not needed
            is_ancestor_descendant_relationship(
                block, 
                get_block_from_hash(vote.message.head_hash, nodeState), 
                nodeState) and
            vote.sender in validatorBalances
        ):
            weight = weight + validatorBalances[vote.sender]

    return weight


def get_children(block: Block, nodeState: NodeState) -> PSet[Block]:
    children: PSet[Block] = pset_get_empty()

    for b in get_all_blocks(nodeState):
        if b.parent_hash == block_hash(block):
            children = pset_add(children, b)

    return children


def find_head_from(block: Block, votes: PSet[SignedVoteMessage], nodeState: NodeState, validatorBalances: ValidatorBalances) -> Block:
    children = get_children(block, nodeState)

    if len(children) == 0:
        return block
    else:
        best_child = pset_pick_element(children)

        for child in children:
            if get_GHOST_weight(child, votes, nodeState, validatorBalances) > get_GHOST_weight(best_child, votes, nodeState, validatorBalances):
                best_child = child

        return find_head_from(best_child, votes, nodeState, validatorBalances)


def get_head(nodeState: NodeState) -> Block:
    relevant_votes: PSet[SignedVoteMessage] = filter_out_GHOST_votes_non_descendant_of_block(  # Do we really need this given that we start find_head from GJ?
        get_block_from_hash(get_highest_justified_checkpoint(nodeState).block_hash, nodeState),
        filter_out_non_LMD_GHOST_votes(
            filter_out_expired_GHOST_votes(
                filter_out_GHOST_equivocating_votes(
                    filter_out_invalid_votes(
                        nodeState.view_vote,
                        nodeState
                    ),
                    nodeState
                ),
                nodeState
            )
        ),
        nodeState
    )

    validatorBalances = get_validator_set_for_slot(
        get_block_from_hash(get_highest_justified_checkpoint(nodeState).block_hash, nodeState),
        nodeState.current_slot,
        nodeState
    )

    return find_head_from(
        get_block_from_hash(get_highest_justified_checkpoint(nodeState).block_hash, nodeState),
        relevant_votes,
        nodeState,
        validatorBalances
    )


def execute_view_merge(nodeState: NodeState) -> NodeState:
    nodeState = nodeState.set(blocks=pmap_merge(nodeState.blocks, nodeState.buffer_blocks))
    nodeState = nodeState.set(view_vote=pset_merge(
        pset_merge(
            nodeState.view_vote,
            nodeState.buffer_vote
        ),
        get_votes_included_in_blocks(get_all_blocks(nodeState)))
    )
    nodeState = nodeState.set(buffer_vote=pset_get_empty())
    nodeState = nodeState.set(buffer_blocks=pset_get_empty())
    return nodeState


def get_block_k_deep(blockHead: Block, k: int, nodeState: NodeState) -> Block:
    Requires(is_complete_chain(blockHead, nodeState))
    if k <= 0 or blockHead == nodeState.configuration.genesis:
        return blockHead
    else:
        return get_block_k_deep(get_parent(blockHead, nodeState), k - 1, nodeState)


def is_confirmed(block: Block, nodeState: NodeState) -> bool:
    head_block = get_head(nodeState)

    validatorBalances = get_validator_set_for_slot(
        get_block_from_hash(get_highest_justified_checkpoint(nodeState).block_hash, nodeState),
        nodeState.current_slot,
        nodeState
    )

    tot_validator_set_weight = validator_set_weight(pmap_keys(validatorBalances), validatorBalances)

    return (
        is_ancestor_descendant_relationship(block, head_block, nodeState) and
        get_GHOST_weight(block, nodeState.view_vote, nodeState, validatorBalances) * 3 >= tot_validator_set_weight * 2
    )


def filter_out_not_confirmed(blocks: PSet[Block], nodeState: NodeState) -> PSet[Block]:
    return pset_filter(
        lambda block: is_confirmed(block, nodeState),
        blocks
    )
