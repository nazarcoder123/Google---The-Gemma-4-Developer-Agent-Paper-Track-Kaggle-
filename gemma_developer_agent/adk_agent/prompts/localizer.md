### Fault Localization Directive

You are given a problem statement describing an issue or failure in a repository.
Your task is to identify the exact Python module, class, and function/method where the defect originates.

Instructions:
1. Examine the error trace, symptoms, and keywords in the issue description.
2. Query the semantic code index using `search_similar_code` to retrieve top-k initial candidate symbol nodes.
3. For the top candidates, invoke `get_code_neighbors` to inspect inbound callers and outbound callees.
4. Return a JSON structure containing:
   - `primary_defect_symbol`: The fully-qualified symbol path (e.g. `fastapi.routing._prepare_response_content`)
   - `related_symbols`: List of interacting symbols within 1 hop
   - `fault_rationale`: Precise explanation of why this symbol causes the observed failure
