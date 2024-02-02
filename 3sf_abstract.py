from __future__ import annotations
import copy
from dataclasses import dataclass
from enum import Enum
from typing import TypeVar, Optional
from pyrsistent import PClass, m, pmap, v, PRecord, field, pset, PSet, PMap

def Requires(expr: bool) -> bool:
    pass

@dataclass(frozen=True)
class Hash(str):
    pass

@dataclass(frozen=True)
class Signature:
    pass

@dataclass(frozen=True)
class NodeIdentity(str):
    pass

ValidatorBalances = dict[NodeIdentity, int]

@dataclass(frozen=True)
class Checkpoint:
    block_hash: Hash
    chkp_slot: int
    block_slot: int

@dataclass(frozen=True)
class BlockBody(object):
    pass

@dataclass(frozen=True)
class Block:
    parent_hash: Hash
    slot: int
    votes: set[SignedVoteMessage]
    body: BlockBody

@dataclass(frozen=True)
class VoteMessage:
    slot: int  # Do we need this. We could just use ffg_target.slot
    head_hash: Hash
    ffg_source: Checkpoint
    ffg_target: Checkpoint

@dataclass(frozen=True)
class ProposeMessage:
    block: Block
    proposer_view: list[SignedVoteMessage]

@dataclass(frozen=True)
class SignedProposeMessage:
    message: ProposeMessage
    signature: Signature

@dataclass(frozen=True)
class SignedVoteMessage:
    message: VoteMessage
    signature: Signature
    sender: NodeIdentity

@dataclass(frozen=True)
class NodePhase(Enum):
    PROPOSE = 0
    VOTE = 1
    CONFIRM = 2
    MERGE = 3

@dataclass(frozen=True)
class Configuration:
    delta: int
    genesis: Block
    eta: int
    k: int


class NodeState(PRecord):
    configuration: Configuration = field(type=Configuration)
    identity: NodeIdentity = field(type=NodeIdentity)
    current_slot: int = field(type=int)
    current_phase: NodePhase = field(type=NodePhase)
    blocks: dict[Hash,Block] = field() # Using field(type=dict[Hash,Block]) raises a max stack depth rec. error in execution. Same for sets below
    view_vote: PSet[SignedVoteMessage] = field()
    view_lmd: dict[NodeIdentity, SignedVoteMessage] = field()
    buffer_vote: PSet[SignedVoteMessage] = field()
    buffer_blocks: PMap[Hash, Block] = field()
    s_cand = PSet[Block] = field()
    chava: Block = field()


def init() -> NodeState:
    return NodeState(
        identity=NodeIdentity(),
        current_phase = NodePhase.PROPOSE,
        current_slot=0,
        blocks=[],
        configuration=Configuration(
            delta=10,
            genesis=Block(
                parent_hash="",
                body=BlockBody()
            )
        )
    )


T1 = TypeVar('T1')
T2 = TypeVar('T2')

def merge_dict(a: dict[T1, T2], b:dict[T1, T2]) -> dict[T1, T2]:
    return {**a, **b}

def concat_lists(a: list[T1], b: list[T1]) -> list[T1]:
    return a + b

def merge_sets(a: set[T1], b: set[T2]) -> set[T1]:
    return set().union(a).union(b)

def create_set(l: list[T1]) -> PSet[T1]:
    return PSet(l)

def pick_from_set(s: PSet[T1]) -> T1:
    Requires(len(s) > 0)
    return list(s)[0]

def get_key_set(d: dict[T1,T2]) -> set[T1]:
    return set(d.keys)

def block_hash(block: Block) -> Hash:
    pass

def verify_vote_signature(vote: SignedVoteMessage) -> bool:
    pass

def get_block_body() -> BlockBody:
    pass

def get_slot_from_time(time:int, configuration: Configuration) -> int:
    return time // (4 * configuration.delta)

def get_phase_from_time(time:int, configuration: Configuration) -> NodePhase:
    time_in_slot = time % (4 * configuration.delta)

    if time_in_slot >= 3 * configuration.delta:
        return NodePhase.MERGE
    elif time_in_slot >= 2 * configuration.delta:
        return NodePhase.CONFIRM
    elif time_in_slot >= configuration.delta:
        return NodePhase.VOTE
    else:
        return NodePhase.PROPOSE

def on_tick(node: NodeState, time: int) -> NodeState:
    new_node: NodeState = copy(node)

    new_slot = get_slot_from_time(time, node.configuration)
    new_phase = get_phase_from_time(time, node.configuration)

    if new_slot != node.current_slot or new_phase != node.current_phase:
        new_node.current_slot = new_slot
        new_node.current_phase = new_phase

        if new_phase == NodePhase.PROPOSE:
            return on_propose(new_node)

    return new_node



def get_proposer(nodeState: NodeState) -> NodeIdentity:
    pass


def genesis_checkpoint(nodeState: NodeState) -> Checkpoint:
    return Checkpoint(
        block_hash=block_hash(nodeState.configuration.genesis),
        chkp_slot=0,
        block_slot=0
    )
    
    
def get_block(block_hash: Hash, nodeState: NodeState) -> Block:
    Requires(block_hash in nodeState.blocks)
    return nodeState.blocks[block_hash]

def has_parent(block: Block, nodeState: NodeState) -> bool:
    return block.parent_hash in nodeState.blocks


def get_parent(block: Block, nodeState: NodeState) -> Block:
    Requires(has_parent(block, nodeState))
    return nodeState.blocks[block.parent_hash]

def is_complete_chain(block: Block, nodeState: NodeState) -> bool:
    if block == nodeState.configuration.genesis:
        return True
    elif block.parent_hash not in nodeState.blocks:
        return False
    else:
        return is_complete_chain(nodeState.blocks[block.parent_hash])

def get_blockchain(block: Block, nodeState: NodeState) -> list[Block]:
    Requires(is_complete_chain(block, nodeState))
    if block == nodeState.configuration.genesis:
        return [block]
    else:
        return concat_lists([block], get_blockchain(nodeState.blocks[block.parent_hash]))


def get_validator_set_for_slot(block: Block, slot: int, nodeState: NodeState) -> ValidatorBalances:
    Requires(is_complete_chain(block, nodeState))
    pass

def sign_propose_message(node: NodeState, propose_message: ProposeMessage) -> SignedProposeMessage:
    pass

def get_signer_of_vote_message(vote: SignedVoteMessage) -> NodeIdentity:
    pass

def sign_vote_message(node: NodeState, vote_message: VoteMessage) -> SignedVoteMessage:
    pass



def is_ancestor_descendant_relationship(ancestor: Block, descendant: Block, nodeState: NodeState) -> bool:
    Requires(is_complete_chain(descendant, nodeState))
    if ancestor == descendant:
        return True
    elif descendant == nodeState.configuration.genesis:
        return False
    else:
        return is_ancestor_descendant_relationship(ancestor, NodeState.blocks[descendant.parent_hash], nodeState)

def get_votes_for_FFG_link(source: Checkpoint, target: Checkpoint, nodeState: NodeState) -> set[SignedVoteMessage]:
    filtered_votes: set[SignedVoteMessage] = set()

    for vote in nodeState.view_vote:
        if vote.ffg_source == source and vote.ffg_target == target:
            filtered_votes.add(vote)

    return filtered_votes


def get_senders_of_votes(votes: PSet[SignedVoteMessage]) -> PSet[NodeIdentity]:
    senders: PSet[SignedVoteMessage] = pset()

    for vote in votes:
        senders = senders.add(vote.sender)

    return senders

def get_valid_votes_with_FFG_target(target: Checkpoint, nodeState: NodeState) -> PSet[SignedVoteMessage]:
    filtered_votes: PSet[SignedVoteMessage] = pset()

    for vote in filter_out_invalid_votes(nodeState.view_vote, nodeState):
        if vote.ffg_target == target:
            filtered_votes = filtered_votes.add(vote)

    return filtered_votes


def validator_set_weight(validators: set[NodeIdentity], validatorBalances: ValidatorBalances) -> int:
    total_weight = 0
    for validator in validators:
        if validator in validatorBalances:
            total_weight = total_weight + validatorBalances[validator]

    return total_weight

def is_FFG_link_supermajority(source: Checkpoint, target: Checkpoint, nodeState: NodeState, validatorBalances: ValidatorBalances) -> bool:
    link_weight = validator_set_weight(get_senders_of_votes(get_votes_for_FFG_link(source, target, nodeState)), validatorBalances)
    tot_validator_set_weight = validator_set_weight(get_key_set(validatorBalances), validatorBalances)

    return link_weight * 3 >= tot_validator_set_weight * 2

def get_set_FFG_targets(votes: set[SignedVoteMessage]) -> PSet[Checkpoint]:
    FFG_source_checkpoints: PSet[Checkpoint] = pset()

    for vote in votes:
        FFG_source_checkpoints = FFG_source_checkpoints.add(vote.message.ffg_target)

    return FFG_source_checkpoints

def get_descendant_FFG_targets_for_same_slot(checkpoint: Checkpoint, votes: PSet[SignedVoteMessage], nodeState: NodeState) -> PSet[Checkpoint]:
    Requires(checkpoint.block_hash in nodeState.blocks)

    descendant_checkpoints: PSet[Checkpoint] = pset()
    descendant_checkpoints = descendant_checkpoints.add(checkpoint)

    checkpoint_block = nodeState.blocks[checkpoint.block_hash]

    for vote in votes:
        if (
            vote.message.slot == checkpoint.slot and
            vote.message.ffg_target.block_hash in nodeState.blocks and
            is_ancestor_descendant_relationship(checkpoint_block, nodeState.blocks[vote.message.ffg_target.block_hash], nodeState)
        ):
            descendant_checkpoints = descendant_checkpoints.add(vote.message.ffg_target)

    return descendant_checkpoints

def get_ancestor_FFG_sources(checkpoint: Checkpoint, votes: PSet[SignedVoteMessage], nodeState: NodeState) -> PSet[Checkpoint]:
    Requires(checkpoint.block_hash in nodeState.blocks)

    ancestor_checkpoint: PSet[Checkpoint] = pset()
    ancestor_checkpoint = ancestor_checkpoint.add(checkpoint)

    checkpoint_block = nodeState.blocks[checkpoint.block_hash]

    for vote in votes:
        if (
            vote.message.ffg_source.block_hash in nodeState.blocks and
            is_ancestor_descendant_relationship(nodeState.blocks[vote.message.ffg_source.block_hash], checkpoint_block, nodeState)
        ):
            ancestor_checkpoint = ancestor_checkpoint.add(vote.message.ffg_source)

    return ancestor_checkpoint

def is_FFG_vote_in_support_of_checkpoint(vote: SignedVoteMessage, checkpoint: Checkpoint, nodeState: NodeState) -> bool:
    return (
        valid_vote(vote, nodeState) and
        vote.message.ffg_target.chkp_slot == checkpoint.chkp_slot and
        is_ancestor_descendant_relationship(nodeState.blocks[checkpoint.block_hash], nodeState.blocks[vote.message.ffg_target.block_hash], nodeState) and
        is_ancestor_descendant_relationship(nodeState.blocks[vote.message.ffg_source.block_hash], nodeState.blocks[checkpoint.block_hash], nodeState) and
        is_justified(vote.message.ffg_source, nodeState)
    )


def filter_out_votes_not_in_FFG_support_of_checkpoint(votes: PSet[SignedVoteMessage], checkpoint: Checkpoint, nodeState: NodeState) -> PSet[SignedVoteMessage]:
    return filter(lambda x: is_FFG_link_supermajority(x, checkpoint, nodeState), votes)

def get_validators_in_FFG_support_of_checkpoint(votes: PSet[SignedVoteMessage], checkpoint: Checkpoint, nodeState: NodeState) -> PSet[NodeIdentity]:
    validators: PSet[NodeIdentity] = pset()

    for vote in filter_out_votes_not_in_FFG_support_of_checkpoint(votes, checkpoint, nodeState):
        validators = validators.add(vote.sender)

    return validators

def get_set_FFG_sources(votes: set[SignedVoteMessage]) -> PSet[Checkpoint]:
    FFG_source_checkpoints: PSet[Checkpoint] = pset()

    for vote in votes:
        FFG_source_checkpoints = FFG_source_checkpoints.add(vote.message.ffg_source)

    return FFG_source_checkpoints


def is_justified(checkpoint: Checkpoint, nodeState: NodeState) -> bool:
    if checkpoint == genesis_checkpoint(nodeState):
        return True
    else:
        if checkpoint.block_hash not in nodeState.blocks or not is_complete_chain(nodeState.blocks[checkpoint.block_hash], nodeState):
            return False

        validatorBalances = get_validator_set_for_slot(nodeState.blocks[checkpoint.block_hash], checkpoint.block_slot, nodeState)

        FFG_support_weight = validator_set_weight(get_validators_in_FFG_support_of_checkpoint(nodeState.view_vote, checkpoint, nodeState), validatorBalances)
        tot_validator_set_weight = validator_set_weight(get_key_set(validatorBalances), validatorBalances)

        return FFG_support_weight * 3 >= tot_validator_set_weight * 2

def filter_out_non_justified_checkpoint(checkpoints: PSet[Checkpoint], nodeState: NodeState) -> PSet[Checkpoint]:
    justified_checkpoints: PSet[Checkpoint] = pset()

    for checkpoint in checkpoints:
        if is_justified(checkpoint, nodeState):
            justified_checkpoints = justified_checkpoints.add(checkpoint)

    return justified_checkpoints


def get_justified_checkpoints(nodeState: NodeState) -> set[Checkpoint]:
    return filter_out_non_justified_checkpoint(get_set_FFG_targets(nodeState.view_vote), nodeState).add(Checkpoint(
        block_hash=block_hash(nodeState.configuration.genesis),
        chkp_slot=0,
        block_slot=0
    ))

def get_highest_justified_checkpoint(nodeState: NodeState) -> Checkpoint:
    highest_justified_checkpoint = genesis_checkpoint(nodeState)

    for checkpoint in get_justified_checkpoints(nodeState):
        if checkpoint.chkp_slot > highest_justified_checkpoint.chkp_slot:
            highest_justified_checkpoint = checkpoint

    return highest_justified_checkpoint


def filter_out_blocks_non_ancestor_of_block(block: Block, blocks: PSet[Block], nodeState: NodeState) -> PSet[Block]:
    pass

def filter_out_votes_non_descendant_of_block(block: Block, votes: set[SignedVoteMessage], nodeState: NodeState) -> set[SignedVoteMessage]:
    filtered_votes: set[SignedVoteMessage] = set()

    for vote in votes:
        if  (
                vote.message.head_hash in nodeState.blocks and
                is_complete_chain(nodeState.blocks[vote.message.head_hash], nodeState.blocks, nodeState.genesis) and
                is_ancestor_descendant_relationship(block, nodeState.blocks[vote.message.head_hash], nodeState.blocks, nodeState.genesis)
        ):
            filtered_votes.add(vote)

    return filtered_votes

def is_vote_for_block_in_blockchain(vote: SignedVoteMessage, blockchainHead: Block, nodeState: NodeState) -> bool:
    return (
        vote.message.head_hash in nodeState.blocks and
        is_ancestor_descendant_relationship(nodeState.blocks[vote.message.head_hash], blockchainHead, nodeState)
    )

def filter_out_votes_not_for_blocks_in_blockchain(votes: PSet[SignedVoteMessage], blockchainHead: Block, nodeState: NodeState) -> PSet[SignedVoteMessage]:
    filtered_votes: set[SignedVoteMessage] = pset()

    for vote in votes:
        if is_vote_for_block_in_blockchain(vote, blockchainHead, nodeState):
            filtered_votes.add(vote)

    return filtered_votes

def filter_out_votes_for_blocks_in_blockchain(votes: PSet[SignedVoteMessage], blockchainHead: Block, nodeState: NodeState) -> PSet[SignedVoteMessage]:
    filtered_votes: set[SignedVoteMessage] = pset()

    for vote in votes:
        if not is_vote_for_block_in_blockchain(vote, blockchainHead, nodeState):
            filtered_votes.add(vote)

    return filtered_votes


def is_vote_expired(vote: SignedVoteMessage, nodeState: NodeState) -> bool:
    return vote.message.slot + nodeState.configuration.eta < nodeState.current_slot


def filter_out_expired_votes(votes: set[SignedVoteMessage], nodeState: NodeState) -> PSet[SignedVoteMessage]:
    pass

def filter_out_non_LMD_votes(votes: PSet[SignedVoteMessage]) -> PSet[SignedVoteMessage]:
    lmd: PMap[NodeIdentity, SignedVoteMessage] = pmap()

    for vote in votes:
        if vote.sender not in lmd or vote.message.slot > lmd[vote.sender].message.slot:
            lmd = lmd.set(vote.sender, vote)

    return lmd.values()

def is_equivocating_vote(vote: SignedVoteMessage, nodeState: NodeState) -> bool:
    for vote_check in nodeState.view_vote:
        if (
            vote_check.message.slot == vote.message.slot and
            vote_check.sender == vote.message.sender and
            vote_check.message.head_hash != vote.message.head_hash
        ):
            return True

    return False

def filter_out_equivocating_votes(nodeState: NodeState) -> PSet[SignedVoteMessage]:
    pass

def valid_vote(vote: SignedVoteMessage, nodeState: NodeState) -> bool:
    return (
        verify_vote_signature(vote) and
        vote.message.head_hash in nodeState.blocks and
        is_complete_chain(nodeState.blocks[vote.message.head_hash], nodeState) and
        vote.message.sender in get_validator_set_for_slot(nodeState.blocks[vote.message.head_hash], vote.message.slot, nodeState) and
        is_ancestor_descendant_relationship(nodeState.blocks[vote.message.ffg_source.block_hash], nodeState.blocks[vote.message.ffg_target.block_hash], nodeState) and
        is_ancestor_descendant_relationship(nodeState.blocks[vote.message.ffg_target.block_hash], nodeState.blocks[vote.message.head_hash], nodeState) and
        vote.message.ffg_source.chkp_slot < vote.message.ffg_target.chkp_slot and
        vote.message.ffg_source.block_hash in nodeState.blocks and
        nodeState.blocks[vote.message.ffg_source.block_hash].slot == vote.message.ffg_source.block_slot and
        vote.message.ffg_target.block_hash in nodeState.blocks and
        nodeState.blocks[vote.message.ffg_target.block_hash].slot == vote.message.ffg_target.block_slot
    )

def filter_out_invalid_votes(votes: set[SignedVoteMessage], nodeState: NodeState) -> set[SignedVoteMessage]:
    filtered_votes: set[SignedVoteMessage] = set()

    for vote in votes:
        if valid_vote(vote, nodeState):
            filtered_votes.add(vote)

    return filtered_votes

def get_votes_included_in_blockchain(block: Block, nodeState: NodeState) -> set[SignedVoteMessage]:
    if block == nodeState.configuration.genesis or block.parent_hash not in nodeState.blocks:
        return block.votes
    else:
        return merge_sets(block.votes, get_votes_included_in_blockchain(nodeState.blocks[block.parent_hash], nodeState))


def get_votes_included_in_blocks(blocks: set[Block]) -> set[SignedVoteMessage]:
    votes: PSet[SignedVoteMessage] = pset()

    for block in blocks:
        votes = merge_sets(votes, block.votes)

    return votes




def votes_to_include_in_proposed_block(nodeState: NodeState) -> set[SignedVoteMessage]:
    head_block = get_head(nodeState)
    votes_for_blocks_in_canonical_chain = filter_out_votes_not_for_blocks_in_blockchain(
        filter_out_invalid_votes(nodeState.view_vote, nodeState),
        head_block,
        nodeState
    )

    return votes_for_blocks_in_canonical_chain.difference(get_votes_included_in_blockchain(head_block, nodeState))


def get_new_block(nodeState: NodeState) -> Block:
    head_block = get_head(nodeState)
    return Block(
        parent_hash=block_hash(head_block),
        body=get_block_body(),
        slot=nodeState.current_slot,
        votes=votes_to_include_in_proposed_block(nodeState)
    )

def get_votes_to_include_in_propose_message_view(nodeState: NodeState) -> set[SignedVoteMessage]:
    head_block = get_head(nodeState)
    validatorBalances = get_validator_set_for_slot(head_block, nodeState.current_slot, nodeState)
    return filter_out_votes_for_blocks_in_blockchain(
        filter_out_votes_non_descendant_of_block(
                get_highest_justified_checkpoint(nodeState, validatorBalances).block,
                filter_out_expired_votes(
                    filter_out_invalid_votes(nodeState.view_vote, nodeState),
                    nodeState
                ),
                nodeState
        ),
        head_block,
        nodeState
    )

def ghost_weight(block: Block, votes: PSet[SignedVoteMessage], nodeState: NodeState, validatorBalances: ValidatorBalances) -> int:
    weight = 0

    for vote in votes:
        if (
            vote.message.head_hash in nodeState.blocks and # Perhaps not needed
            is_ancestor_descendant_relationship(block, nodeState.blocks[vote.message.head_hash], nodeState) and
            vote.sender in validatorBalances
        ):
            weight = weight + validatorBalances[vote.sender]

    return weight


def get_children(block: Block, nodeState: NodeState) -> PSet[Block]:
    children: PSet[Block] = create_set([])

    for b in nodeState.blocks:
        if nodeState.blocks[b].parent_hash == block_hash(block):
            children = children.add(nodeState.blocks[b])

    return children


def find_head_from(block: Block, votes: PSet[SignedVoteMessage], nodeState: NodeState, validatorBalances: ValidatorBalances) -> Block:
    children = get_children(block, nodeState)

    if len(children) == 0:
        return block
    else:
        best_child = pick_from_set(children)

        for child in children:
            if ghost_weight(child, votes, nodeState, validatorBalances) > ghost_weight(best_child, votes, nodeState, validatorBalances):
                best_child = child

        return find_head_from(best_child, votes, nodeState, validatorBalances)

def get_head(nodeState: NodeState) -> Block:
    relevant_votes: PSet[SignedVoteMessage] = filter_out_votes_non_descendant_of_block( # Do we really need this given that we start find_head from GJ?
        get_highest_justified_checkpoint(nodeState).block,
        filter_out_non_LMD_votes(
            filter_out_expired_votes(
                filter_out_equivocating_votes(nodeState),
                nodeState
            )
        ),
        nodeState
    )

    validatorBalances = get_validator_set_for_slot(get_highest_justified_checkpoint(nodeState).block, nodeState.current_slot, nodeState)

    return find_head_from(
        get_highest_justified_checkpoint(nodeState).block,
        relevant_votes,
        validatorBalances
    )




@dataclass(frozen=True)
class NewNodeStateAndMessagesToTx:
    state: NodeState
    proposeMessages: PSet[SignedProposeMessage]
    voteMessages: PSet[SignedVoteMessage]


    # Keeping the two fields before separate for now as this may help the Dafny translation
    # We may in the future just want to use one using a common base class for propose and vote messages
    proposeMessagesToTx: set[SignedProposeMessage] = field()
    voteMessagesToTx: set[SignedVoteMessage] = field()

def execute_view_merge(nodeState: NodeState) -> NodeState:
    nodeState = nodeState.set(blocks=merge_dict(nodeState.blocks, nodeState.buffer_blocks))
    nodeState = nodeState.set(view_vote=merge_sets(merge_sets(nodeState.view_vote, nodeState.buffer_vote), get_votes_included_in_blocks(nodeState.buffer_blocks)))
    nodeState = nodeState.set(buffer_vote=set())
    nodeState = nodeState.set(buffer_blocks=set())
    return nodeState

def on_propose(nodeState: NodeState) -> NewNodeStateAndMessagesToTx:

    proposer = get_proposer(nodeState)

    if proposer == nodeState.identity:
        nodeState = execute_view_merge(nodeState)

        signed_propose = sign_propose_message(
            ProposeMessage(
                block=get_new_block(nodeState),
                proposer_view=get_votes_to_include_in_propose_message_view(nodeState)
            )
        )

        return NewNodeStateAndMessagesToTx(
            state=nodeState,
            proposeMessages=create_set([signed_propose]),
            voteMessages=create_set([])
        )

    else:
        return NewNodeStateAndMessagesToTx(
            state=nodeState,
            proposeMessages=create_set([]),
            voteMessages=create_set([])
        )

def get_block_k_deep(blockHead: Block, k: int, nodeState: NodeState) -> Block:
    Requires(is_complete_chain(blockHead, nodeState))
    if k <= 0 or blockHead == nodeState.configuration.genesis:
        return blockHead
    else:
        return get_block_k_deep(get_parent(blockHead, nodeState), k-1, nodeState)

def on_vote(nodeState: NodeState) -> NewNodeStateAndMessagesToTx:
    ch = get_head(nodeState)
    s_cand = filter_out_blocks_non_ancestor_of_block(
        ch,
        nodeState.s_cand,
        nodeState
    ).add(
        nodeState.blocks[get_highest_justified_checkpoint(nodeState).block_hash]
    )

    bcand = pick_from_set(s_cand)
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
            head_hash=ch,
            ffg_source=get_highest_justified_checkpoint(nodeState),
            ffg_target=Checkpoint(
                block_hash=block_hash(nodeState.chava),
                chkp_slot=nodeState.current_slot,
                block_slot=nodeState.chava.slot
            )
        )
    )
        
    return NewNodeStateAndMessagesToTx(
        state=nodeState,
        proposeMessages=pset(),
        voteMessages=create_set([signedVoteMessage])
    )
    
def is_confirmed(block: Block, nodeState: NodeState, validatorBalances: ValidatorBalances) -> bool:
    head_block = get_head(nodeState)
    
    validatorBalances = get_validator_set_for_slot(get_block(get_highest_justified_checkpoint(nodeState).block_hash), nodeState.current_slot, nodeState)

    tot_validator_set_weight = validator_set_weight(get_key_set(validatorBalances), validatorBalances)
    
    return (
        is_ancestor_descendant_relationship(block, head_block, nodeState) and
        ghost_weight(block, nodeState.view_vote, nodeState) * 3 >= tot_validator_set_weight * 2
    )
    
def filter_out_not_confirmed(nodeState: NodeState) -> PSet[Block]:
    pass
    
def on_confirm(nodeState: NodeState) -> NodeState:
    return nodeState.set(
        s_cand = nodeState.s_cand.update(filter_out_not_confirmed(nodeState)),
    )
    
def on_merge(nodeState: NodeState) -> NodeState:
    return execute_view_merge(nodeState)

def on_received_propose(propose: SignedProposeMessage, nodeState: NodeState) -> NodeState:
    # nodeState = on_block_received(propose.message.block, nodeState)
    if nodeState.current_phase == NodePhase.PROPOSE: # Is this Ok or do we need to also include 4\Delta t + \Delta ?
        nodeState = nodeState.set(
            view_vote=nodeState.view_vote.union(propose.message.proposer_view),
        )

def on_block_received(block: Block, nodeState: NodeState) -> NodeState:
    return nodeState.set(
        buffer_blocks = nodeState.buffer_blocks.set(block_hash(block), block)
    )
    
def on_vote_received(vote: SignedVoteMessage, nodeState: NodeState) -> NodeState:
    return nodeState.set(
        buffer_vote=nodeState.buffer_vote.add(vote)
    )


# # class ARecord(PClass):
# #     x = field(type=int)

# # # n = init()
# # # print(is_complete_chain(n.configuration.genesis,n))
# # # print(n)


# # m1 = m(a=1, b=2)
# # m1 = m1.set('c', 3)
# # m1 = m1.set('a', 5)

# # print(m1)

# # x = ARecord(x=5)
# # x2 = x.set(x=3)

# # print(x)
# # print(x2)

# # x2.x = 10

