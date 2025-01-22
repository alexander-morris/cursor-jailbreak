# Development Process

## 1. Planning Phase
- Break down todo items into small, testable increments
- Each increment should be independently verifiable
- Define clear acceptance criteria for each increment
- Prioritize changes that can be tested in isolation

## 2. Implementation Cycle
For each increment:
1. Write or update test(s) first
2. Implement the minimal required code changes
3. Run the specific test(s) for this increment
4. If tests fail:
   - Review logs and output
   - Make necessary adjustments
   - Repeat until tests pass
5. Run the full test suite
6. Only if all tests pass:
   - Git commit with format: `[TODO-#.#] Description`
   - Reference specific todo item and increment
   - Keep commits focused and atomic

## 3. Documentation
- Update docstrings for any new/modified code
- Include usage examples in docstrings
- Document error handling behavior
- Add type hints for all functions
- Update README.md if new features are added

## 4. Testing Strategy
- Write unit tests for isolated functionality
- Add integration tests for component interactions
- Test both success and failure cases
- Include edge cases and error conditions
- Verify working directory safety
- Test tool call parsing accuracy

## 5. Error Handling
- Add descriptive error messages
- Log important operations and errors
- Implement appropriate recovery strategies
- Test error conditions explicitly
- Document error handling in tests

## 6. Performance Considerations
- Profile code for bottlenecks
- Test with large inputs/files
- Measure and log execution times
- Optimize only with test evidence
- Document performance characteristics

## 7. Code Review Checklist
- All tests pass
- Documentation is updated
- Error handling is complete
- Type hints are present
- Commits are atomic and clear
- No unnecessary changes
- Performance impact considered 