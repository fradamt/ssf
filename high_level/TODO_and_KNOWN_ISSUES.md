# TODOs and Known Issues

## TODOs

### Coding

- [ ] Decide code conventions for function prefixes, in general. Specifically,
  - [ ] Is the `filter_out` prefix Ok or do we prefer something else?
  - [ ] `get` vs `compute_`
- [ ] Decide when to pass the set of `votes` in a function and when just passing `nodeState` is enough.
- [ ] Decide whether to use max function rather the having manual implementation of it every time that is needed
- [ ] Decide whether to pass Block or Hash to functions dealing with blocks
- [ ] Ensure that all the rules/guidelines defined for how to write the specs are applied

### Protocol Definition

- [ ] Add slashing
- [ ] Code @Init function
- [ ] Fill in stubs

## Known Issues

1. The logic used to determine the validator set and weight is all over the places. We need to decide, what the validator set and the validator balances depend on. Do they depend on the chain up to the checkpoint for which we are checking whether it is justified? Do they depend on the chain up to the head block? Do they depend on the chain up to the latest finalized checkpoint?
2. `Requires` declaration are not use everywhere they should be used
