from pyrsistent import PSet, PMap, PVector

from data_structures import *
from formal_verification_annotations import *
from pythonic_code_generic import *
from stubs import *


def get_slot_from_time(time: int, node_state: NodeState) -> int:
    return time // (4 * node_state.configuration.delta)


def get_phase_from_time(time: int, node_state: NodeState) -> NodePhase:
    time_in_slot = time % (4 * node_state.configuration.delta)

    if time_in_slot >= 3 * node_state.configuration.delta:
        return NodePhase.MERGE
    elif time_in_slot >= 2 * node_state.configuration.delta:
        return NodePhase.CONFIRM
    elif time_in_slot >= node_state.configuration.delta:
        return NodePhase.VOTE
    else:
        return NodePhase.PROPOSE


def genesis_checkpoint(node_state: NodeState) -> Checkpoint:
    return Checkpoint(
        block_hash=block_hash(node_state.configuration.genesis),
        chkp_slot=0,
        block_slot=0
    )


def has_block_hash(block_hash: Hash, node_state: NodeState) -> bool:
    return pmap_has(node_state.view_blocks, block_hash)


def get_block_from_hash(block_hash: Hash, node_state: NodeState) -> Block:
    Requires(has_block_hash(block_hash, node_state))
    return pmap_get(node_state.view_blocks, block_hash)


def has_parent(block: Block, node_state: NodeState) -> bool:
    return has_block_hash(block.parent_hash, node_state)


def get_parent(block: Block, node_state: NodeState) -> Block:
    Requires(has_parent(block, node_state))
    return get_block_from_hash(block.parent_hash, node_state)


def get_all_blocks(node_state: NodeState) -> PSet[Block]:
    return pmap_values(node_state.view_blocks)


def is_complete_chain(block: Block, node_state: NodeState) -> bool:
    if block == node_state.configuration.genesis:
        return True
    elif not has_parent(block, node_state):
        return False
    else:
        return is_complete_chain(get_parent(block, node_state), node_state)


def get_blockchain(block: Block, node_state: NodeState) -> PVector[Block]:
    Requires(is_complete_chain(block, node_state))
    if block == node_state.configuration.genesis:
        return pvector_of_one_element(block)
    else:
        return pvector_concat(
            pvector_of_one_element(block),
            get_blockchain(get_parent(block, node_state), node_state)
        )


def is_ancestor_descendant_relationship(ancestor: Block, descendant: Block, node_state: NodeState) -> bool:
    if ancestor == descendant:
        return True
    elif descendant == node_state.configuration.genesis:
        return False
    else:
        return (
            has_parent(descendant, node_state) and
            is_ancestor_descendant_relationship(
                ancestor,
                get_parent(descendant, node_state),
                node_state
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


def is_FFG_vote_in_support_of_checkpoint_justification(vote: SignedVoteMessage, checkpoint: Checkpoint, node_state: NodeState) -> bool:
    return (
        valid_vote(vote, node_state) and
        vote.message.ffg_target.chkp_slot == checkpoint.chkp_slot and
        is_ancestor_descendant_relationship(
            get_block_from_hash(checkpoint.block_hash, node_state),
            get_block_from_hash(vote.message.ffg_target.block_hash, node_state),
            node_state) and
        is_ancestor_descendant_relationship(
            get_block_from_hash(vote.message.ffg_source.block_hash, node_state),
            get_block_from_hash(checkpoint.block_hash, node_state),
            node_state) and
        is_justified_checkpoint(vote.message.ffg_source, node_state)
    )


def filter_out_FFG_votes_not_in_FFG_support_of_checkpoint_justification(votes: PSet[SignedVoteMessage], checkpoint: Checkpoint, node_state: NodeState) -> PSet[SignedVoteMessage]:
    return pset_filter(lambda vote: is_FFG_vote_in_support_of_checkpoint_justification(vote, checkpoint, node_state), votes)


def get_validators_in_FFG_support_of_checkpoint_justification(votes: PSet[SignedVoteMessage], checkpoint: Checkpoint, node_state: NodeState) -> PSet[NodeIdentity]:
    return pset_map(
        lambda vote: vote.sender,
        filter_out_FFG_votes_not_in_FFG_support_of_checkpoint_justification(votes, checkpoint, node_state)
    )


def is_justified_checkpoint(checkpoint: Checkpoint, node_state: NodeState) -> bool:
    if checkpoint == genesis_checkpoint(node_state):
        return True
    else:
        if not has_block_hash(checkpoint.block_hash, node_state) or not is_complete_chain(get_block_from_hash(checkpoint.block_hash, node_state), node_state):
            return False

        validatorBalances = get_validator_set_for_slot(get_block_from_hash(checkpoint.block_hash, node_state), checkpoint.block_slot, node_state)

        FFG_support_weight = validator_set_weight(get_validators_in_FFG_support_of_checkpoint_justification(node_state.view_vote, checkpoint, node_state), validatorBalances)
        tot_validator_set_weight = validator_set_weight(pmap_keys(validatorBalances), validatorBalances)

        return FFG_support_weight * 3 >= tot_validator_set_weight * 2


def filter_out_non_justified_checkpoint(checkpoints: PSet[Checkpoint], node_state: NodeState) -> PSet[Checkpoint]:
    return pset_filter(lambda checkpoint: is_justified_checkpoint(checkpoint, node_state), checkpoints)


def get_justified_checkpoints(node_state: NodeState) -> PSet[Checkpoint]:
    return pset_add(
        filter_out_non_justified_checkpoint(get_set_FFG_targets(node_state.view_vote), node_state),
        genesis_checkpoint(node_state)
    )


def get_highest_justified_checkpoint(node_state: NodeState) -> Checkpoint:
    highest_justified_checkpoint = genesis_checkpoint(node_state)

    for checkpoint in get_justified_checkpoints(node_state):
        if checkpoint.chkp_slot > highest_justified_checkpoint.chkp_slot:
            highest_justified_checkpoint = checkpoint

    return highest_justified_checkpoint


def is_FFG_vote_linking_to_a_checkpoint_in_next_slot(vote: SignedVoteMessage, checkpoint: Checkpoint, node_state: NodeState) -> bool:
    return (
        valid_vote(vote, node_state) and
        vote.message.ffg_source == checkpoint and
        vote.message.ffg_target.chkp_slot == checkpoint.chkp_slot + 1
    )


def filter_out_FFG_vote_not_linking_to_a_checkpoint_in_next_slot(checkpoint: Checkpoint, node_state: NodeState) -> PSet[SignedVoteMessage]:
    return pset_filter(lambda vote: is_FFG_vote_linking_to_a_checkpoint_in_next_slot(vote, checkpoint, node_state), node_state.view_vote)


def get_validators_in_FFG_votes_linking_to_a_checkpoint_in_next_slot(checkpoint: Checkpoint, node_state) -> PSet[NodeIdentity]:
    return pset_map(
        lambda vote: vote.sender,
        filter_out_FFG_vote_not_linking_to_a_checkpoint_in_next_slot(checkpoint, node_state)
    )


def is_finalized_checkpoint(checkpoint: Checkpoint, node_state: NodeState) -> bool:
    if not is_justified_checkpoint(checkpoint, node_state):
        return False

    validatorBalances = get_validator_set_for_slot(get_block_from_hash(checkpoint.block_hash, node_state), checkpoint.block_slot, node_state)
    FFG_support_weight = validator_set_weight(get_validators_in_FFG_votes_linking_to_a_checkpoint_in_next_slot(checkpoint, node_state), validatorBalances)
    tot_validator_set_weight = validator_set_weight(pmap_keys(validatorBalances), validatorBalances)

    return FFG_support_weight * 3 >= tot_validator_set_weight * 2


def filter_out_non_finalized_checkpoint(checkpoints: PSet[Checkpoint], node_state: NodeState) -> PSet[Checkpoint]:
    return pset_filter(lambda checkpoint: is_finalized_checkpoint(checkpoint, node_state), checkpoints)


def get_finalized_checkpoints(node_state: NodeState) -> PSet[Checkpoint]:
    return pset_add(
        filter_out_non_finalized_checkpoint(get_set_FFG_targets(node_state.view_vote), node_state),
        genesis_checkpoint(node_state)
    )


def get_highest_finalized_checkpoint(node_state: NodeState) -> Checkpoint:
    highest_finalized_checkpoint = genesis_checkpoint(node_state)

    for checkpoint in get_finalized_checkpoints(node_state):
        if checkpoint.chkp_slot > highest_finalized_checkpoint.chkp_slot:
            highest_finalized_checkpoint = checkpoint

    return highest_finalized_checkpoint


def filter_out_blocks_non_ancestor_of_block(block: Block, blocks: PSet[Block], node_state: NodeState) -> PSet[Block]:
    return pset_filter(
        lambda b: is_ancestor_descendant_relationship(b, block, node_state),
        blocks
    )


def filter_out_GHOST_votes_non_descendant_of_block(block: Block, votes: PSet[SignedVoteMessage], node_state: NodeState) -> PSet[SignedVoteMessage]:
    return pset_filter(
        lambda vote:
            has_block_hash(vote.message.head_hash, node_state) and
            is_ancestor_descendant_relationship(
                block,
                get_block_from_hash(vote.message.head_hash, node_state),
                node_state
            ),
        votes
    )


def is_GHOST_vote_for_block_in_blockchain(vote: SignedVoteMessage, blockchainHead: Block, node_state: NodeState) -> bool:
    return (
        has_block_hash(vote.message.head_hash, node_state) and
        is_ancestor_descendant_relationship(
            get_block_from_hash(vote.message.head_hash, node_state),
            blockchainHead,
            node_state)
    )


def filter_out_GHOST_votes_not_for_blocks_in_blockchain(votes: PSet[SignedVoteMessage], blockchainHead: Block, node_state: NodeState) -> PSet[SignedVoteMessage]:
    return pset_filter(
        lambda vote: is_GHOST_vote_for_block_in_blockchain(vote, blockchainHead, node_state),
        votes
    )


def filter_out_GHOST_votes_for_blocks_in_blockchain(votes: PSet[SignedVoteMessage], blockchainHead: Block, node_state: NodeState) -> PSet[SignedVoteMessage]:
    return pset_filter(
        lambda vote: not is_GHOST_vote_for_block_in_blockchain(vote, blockchainHead, node_state),
        votes
    )


def is_GHOST_vote_expired(vote: SignedVoteMessage, node_state: NodeState) -> bool:
    return vote.message.slot + node_state.configuration.eta < node_state.current_slot


def filter_out_expired_GHOST_votes(votes: PSet[SignedVoteMessage], node_state: NodeState) -> PSet[SignedVoteMessage]:
    return pset_filter(
        lambda vote: is_GHOST_vote_expired(vote, node_state),
        votes
    )


def filter_out_non_LMD_GHOST_votes(votes: PSet[SignedVoteMessage]) -> PSet[SignedVoteMessage]:
    lmd: PMap[NodeIdentity, SignedVoteMessage] = pmap_get_empty()

    for vote in votes:
        if not pmap_has(lmd, vote.sender) or vote.message.slot > pmap_get(lmd, vote.sender).message.slot:
            lmd = pmap_set(lmd, vote.sender, vote)

    return pmap_values(lmd)


def is_equivocating_GHOST_vote(vote: SignedVoteMessage, node_state: NodeState) -> bool:
    for vote_check in node_state.view_vote:
        if (
            vote_check.message.slot == vote.message.slot and
            vote_check.sender == vote.sender and
            vote_check.message.head_hash != vote.message.head_hash
        ):
            return True

    return False


def filter_out_GHOST_equivocating_votes(votes: PSet[SignedVoteMessage], node_state: NodeState) -> PSet[SignedVoteMessage]:
    return pset_filter(
        lambda vote: not is_equivocating_GHOST_vote(vote, node_state),
        votes
    )


def valid_vote(vote: SignedVoteMessage, node_state: NodeState) -> bool:
    return (
        verify_vote_signature(vote) and
        has_block_hash(vote.message.head_hash, node_state) and
        is_complete_chain(get_block_from_hash(vote.message.head_hash, node_state), node_state) and
        pmap_has(get_validator_set_for_slot(get_block_from_hash(vote.message.head_hash, node_state), vote.message.slot, node_state), vote.sender) and
        is_ancestor_descendant_relationship(
            get_block_from_hash(vote.message.ffg_source.block_hash, node_state),
            get_block_from_hash(vote.message.ffg_target.block_hash, node_state),
            node_state) and
        is_ancestor_descendant_relationship(
            get_block_from_hash(vote.message.ffg_target.block_hash, node_state),
            get_block_from_hash(vote.message.head_hash, node_state),
            node_state) and
        vote.message.ffg_source.chkp_slot < vote.message.ffg_target.chkp_slot and
        has_block_hash(vote.message.ffg_source.block_hash, node_state) and
        get_block_from_hash(vote.message.ffg_source.block_hash, node_state).slot == vote.message.ffg_source.block_slot and
        has_block_hash(vote.message.ffg_target.block_hash, node_state) and
        get_block_from_hash(vote.message.ffg_target.block_hash, node_state).slot == vote.message.ffg_target.block_slot
    )


def filter_out_invalid_votes(votes: PSet[SignedVoteMessage], node_state: NodeState) -> PSet[SignedVoteMessage]:
    return pset_filter(
        lambda vote: valid_vote(vote, node_state),
        votes
    )


def get_votes_included_in_blockchain(block: Block, node_state: NodeState) -> PSet[SignedVoteMessage]:
    if block == node_state.configuration.genesis or not has_block_hash(block.parent_hash, node_state):
        return block.votes
    else:
        return pset_merge(block.votes, get_votes_included_in_blockchain(get_block_from_hash(block.parent_hash, node_state), node_state))


def get_votes_included_in_blocks(blocks: PSet[Block]) -> PSet[SignedVoteMessage]:
    votes: PSet[SignedVoteMessage] = pset_get_empty()

    for block in blocks:
        votes = pset_merge(votes, block.votes)

    return votes


def votes_to_include_in_proposed_block(node_state: NodeState) -> PSet[SignedVoteMessage]:
    """
    The votes to include in a proposed block are all those with a GHOST vote for a block in the chain
    of the proposed block that have not already been included in such a chain
    """
    head_block = get_head(node_state)
    votes_for_blocks_in_canonical_chain = filter_out_GHOST_votes_not_for_blocks_in_blockchain(
        filter_out_invalid_votes(node_state.view_vote, node_state),
        head_block,
        node_state
    )

    return votes_for_blocks_in_canonical_chain.difference(
        get_votes_included_in_blockchain(head_block, node_state)
    )


def get_new_block(node_state: NodeState) -> Block:
    head_block = get_head(node_state)
    return Block(
        parent_hash=block_hash(head_block),
        body=get_block_body(node_state),
        slot=node_state.current_slot,
        votes=votes_to_include_in_proposed_block(node_state)
    )


def get_votes_to_include_in_propose_message_view(node_state: NodeState) -> PVector[SignedVoteMessage]:
    """
    The votes to include in the view shared via a Propose message are all valid, non-expired GHOST votes
    for a block descendant of the greatest justified checkpoint but that are not in the chain of the proposed block
    (as those in the chain of the proposed block are already included in the proposed block itself via, see `votes_to_include_in_proposed_block`)
    """
    head_block = get_head(node_state)
    return from_set_to_pvector(
        filter_out_GHOST_votes_for_blocks_in_blockchain(
            filter_out_GHOST_votes_non_descendant_of_block(
                get_block_from_hash(get_highest_justified_checkpoint(node_state).block_hash, node_state),
                filter_out_expired_GHOST_votes(
                    filter_out_invalid_votes(node_state.view_vote, node_state),
                    node_state
                ),
                node_state
            ),
            head_block,
            node_state
        )
    )


def get_GHOST_weight(block: Block, votes: PSet[SignedVoteMessage], node_state: NodeState, validatorBalances: ValidatorBalances) -> int:
    weight = 0

    for vote in votes:
        if (
            has_block_hash(vote.message.head_hash, node_state) and  # Perhaps not needed
            is_ancestor_descendant_relationship(
                block,
                get_block_from_hash(vote.message.head_hash, node_state),
                node_state) and
            vote.sender in validatorBalances
        ):
            weight = weight + validatorBalances[vote.sender]

    return weight


def get_children(block: Block, node_state: NodeState) -> PSet[Block]:
    children: PSet[Block] = pset_get_empty()

    for b in get_all_blocks(node_state):
        if b.parent_hash == block_hash(block):
            children = pset_add(children, b)

    return children


def find_head_from(block: Block, votes: PSet[SignedVoteMessage], node_state: NodeState, validatorBalances: ValidatorBalances) -> Block:
    children = get_children(block, node_state)

    if len(children) == 0:
        return block
    else:
        best_child = pset_pick_element(children)

        for child in children:
            if get_GHOST_weight(child, votes, node_state, validatorBalances) > get_GHOST_weight(best_child, votes, node_state, validatorBalances):
                best_child = child

        return find_head_from(best_child, votes, node_state, validatorBalances)


def get_head(node_state: NodeState) -> Block:
    relevant_votes: PSet[SignedVoteMessage] = filter_out_GHOST_votes_non_descendant_of_block(  # Do we really need this given that we start find_head from GJ?
        get_block_from_hash(get_highest_justified_checkpoint(node_state).block_hash, node_state),
        filter_out_non_LMD_GHOST_votes(
            filter_out_expired_GHOST_votes(
                filter_out_GHOST_equivocating_votes(
                    filter_out_invalid_votes(
                        node_state.view_vote,
                        node_state
                    ),
                    node_state
                ),
                node_state
            )
        ),
        node_state
    )

    validatorBalances = get_validator_set_for_slot(
        get_block_from_hash(get_highest_justified_checkpoint(node_state).block_hash, node_state),
        node_state.current_slot,
        node_state
    )

    return find_head_from(
        get_block_from_hash(get_highest_justified_checkpoint(node_state).block_hash, node_state),
        relevant_votes,
        node_state,
        validatorBalances
    )


def execute_view_merge(node_state: NodeState) -> NodeState:
    node_state = node_state.set(blocks=pmap_merge(node_state.view_blocks, node_state.buffer_blocks))
    node_state = node_state.set(view_vote=pset_merge(
        pset_merge(
            node_state.view_vote,
            node_state.buffer_vote
        ),
        get_votes_included_in_blocks(get_all_blocks(node_state)))
    )
    node_state = node_state.set(buffer_vote=pset_get_empty())
    node_state = node_state.set(buffer_blocks=pmap_get_empty())
    return node_state


def get_block_k_deep(blockHead: Block, k: int, node_state: NodeState) -> Block:
    Requires(is_complete_chain(blockHead, node_state))
    if k <= 0 or blockHead == node_state.configuration.genesis:
        return blockHead
    else:
        return get_block_k_deep(get_parent(blockHead, node_state), k - 1, node_state)


def is_confirmed(block: Block, node_state: NodeState) -> bool:
    head_block = get_head(node_state)

    validatorBalances = get_validator_set_for_slot(
        get_block_from_hash(get_highest_justified_checkpoint(node_state).block_hash, node_state),
        node_state.current_slot,
        node_state
    )

    tot_validator_set_weight = validator_set_weight(pmap_keys(validatorBalances), validatorBalances)

    return (
        is_ancestor_descendant_relationship(block, head_block, node_state) and
        get_GHOST_weight(block, node_state.view_vote, node_state, validatorBalances) * 3 >= tot_validator_set_weight * 2
    )


def filter_out_not_confirmed(blocks: PSet[Block], node_state: NodeState) -> PSet[Block]:
    return pset_filter(
        lambda block: is_confirmed(block, node_state),
        blocks
    )
