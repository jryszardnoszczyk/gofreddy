## Track f Assignment — Platform: Utility + Agent Core + Pages

Execute ONLY the capabilities assigned to track `f` in the test-matrix `tracks:` block.

Your flows:
1. **Flow 3**: Check Usage/Billing (C6)
2. **Flow 4** (DYNAMIC — excluded from convergence): Agent core — ambiguous prompt (C8), multi-tool search+fraud (C9), workspace query (C10), error recovery (C11)
3. **Page tests**: Settings page (C7), Sessions page (C12), conversation create (C13), send+rename (C14), delete (C15), split-view collapse/restore (C16)

Start a new conversation for each flow. Read `harness/test-matrix.md` for exact prompts, expected tools, sections, timeouts, and pass criteria.

### What to watch for:
- Usage card with credit balance and cost breakdown
- Settings page with API keys, model selection, billing
- Agent responding to ambiguous prompts without tool calls
- Multi-tool chains (search → fraud) rendering both sections
- Workspace queries returning previously saved results
- Graceful error handling (no crash, error message in chat, app stays usable)
- Sessions page with session list and cards
- Conversation CRUD: create, rename, delete
- Split-view: collapse canvas, restore canvas, no layout glitches
