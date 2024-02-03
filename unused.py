def get_slot_from_time(time:int, configuration: Configuration) -> int:
    return time // (4 * configuration.delta)

def get_blockchain(block: Block, nodeState: NodeState) -> list[Block]:
    Requires(is_complete_chain(block, nodeState))
    if block == nodeState.configuration.genesis:
        return [block]
    else:
        return concat_lists([block], get_blockchain(nodeState.blocks[block.parent_hash]))
    
    
def get_valid_votes_with_FFG_target(target: Checkpoint, nodeState: NodeState) -> PSet[SignedVoteMessage]:
    filtered_votes: PSet[SignedVoteMessage] = pset()

    for vote in filter_out_invalid_votes(nodeState.view_vote, nodeState):
        if vote.message.ffg_target == target:
            filtered_votes = filtered_votes.add(vote)

    return filtered_votes