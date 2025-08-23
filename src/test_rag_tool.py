# test_rag_tool.py

import os
import sys
from retrieval_tool import RetrievalTool
from reranking_tool import ReRankingTool

def run_all_tests():
    """
    Tests the new two-tool RAG pipeline in isolation against an existing corpus of policies.
    """
    print("--- Starting RAG Tool Test Suite ---")

    # 1. Instantiate your new tools
    # This assumes your vector store is created in-memory on each run.
    try:
        retrieval_tool = RetrievalTool()
        reranking_tool = ReRankingTool()
        print("✅ Tools instantiated successfully.")
    except Exception as e:
        print(f"❌ ERROR: Failed to instantiate the tools. {e}")
        return

    # 2. Define an array of test queries
    # This includes queries that should match content and some that should not.
    test_queries = [
        {
            "description": "A query that should find relevant context.",
            "query": "What is the company's policy on data encryption?",
            "should_find_context": True
        },
        {
            "description": "Another query that should succeed.",
            "query": "Describe the process for incident response.",
            "should_find_context": True
        },
        {
            "description": "A query about a specific standard.",
            "query": "How does the password policy align with NIST guidelines?",
            "should_find_context": True
        },
        {
            "description": "A query that should NOT find relevant context.",
            "query": "What are the approved company holidays for next year?",
            "should_find_context": False
        },
        {
            "description": "A nonsensical query that should fail.",
            "query": "Does this policy mention dragons or wizards?",
            "should_find_context": False
        }
    ]

    print(f"\nRunning {len(test_queries)} test cases...")
    print("-" * 20)

    # 3. Loop through and execute each test case
    all_tests_passed = True
    for i, test in enumerate(test_queries):
        print(f"▶️  Running Test #{i+1}: {test['description']}")
        print(f"   Query: '{test['query']}'")

        try:
            # Run the new two-step pipeline
            # Step 1: Use the retrieval tool to get candidate documents
            candidate_docs = retrieval_tool._run(query=test['query'])
            # print('CANDIDATE_DOCS')
            # print(candidate_docs)

            # Step 2: Use the reranking tool to get the most relevant context
            if not candidate_docs:
                print('Did not find candidate docs')
                # If no candidate docs, result should be empty string
                result = ""
            else:
                # Pass the original query and candidate docs to the reranking tool
                result = reranking_tool._run(query=test['query'], documents=candidate_docs)
            
            print('RESULT')
            print(result)

            # Check the outcome against the expectation
            if test["should_find_context"] and result.strip():
                print("   ✅ PASS: Tool correctly found context.")
            elif not test["should_find_context"] and not result.strip():
                print("   ✅ PASS: Tool correctly returned no context.")
            elif test["should_find_context"] and not result.strip():
                print("   ❌ FAIL: Tool was expected to find context but returned none.")
                all_tests_passed = False
            else: # not test["should_find_context"] and result.strip()
                print("   ❌ FAIL: Tool was not expected to find context but returned something.")
                print(f"      Unexpected context: '{result}'")
                all_tests_passed = False

        except Exception as e:
            print(f"   ❌ ERROR: An exception occurred during the test: {e}")
            all_tests_passed = False
        
        print("-" * 20)

    # 4. Final Summary
    print("\n--- Test Suite Finished ---")
    if all_tests_passed:
        print("🎉 All tests passed successfully!")
    else:
        print("🔥 Some tests failed. Please review the output.")

def sweep_tau(run_query_fn, positives, negatives, taus=[i/100 for i in range(15, 51)]):
    # run_query_fn(query) -> bool (True if returns any doc)
    best = None
    for tau in taus:
        os.environ["RERANK_TAU"] = str(tau)
        tp = sum(run_query_fn(q) for q in positives)
        fp = sum(run_query_fn(q) for q in negatives)
        fn = len(positives) - tp
        tn = len(negatives) - fp
        prec = tp / max(1, tp + fp)
        rec = tp / max(1, tp + fn)
        f1 = 2*prec*rec / max(1e-9, prec + rec)
        score = (f1, prec, rec)
        if best is None or score > best[0]:
            best = (score, tau, (tp, fp, fn, tn))
    return best
    
if __name__ == "__main__":
    # Ensure the policy directory exists before running
    if not os.path.isdir("./output/policies"):
        print("Error: The './output/policies' directory was not found. Please ensure it exists and contains your documents.")
    else:
        run_all_tests()