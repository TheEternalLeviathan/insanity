from src.reasoning.layer_5 import EvidencePipeline
from src.retrieval.evidence_fetcher import EvidenceFetcher


class GetSourcesTest:
    def __init__(self):
        self.reasoner = EvidencePipeline()
        self.fetcher = EvidenceFetcher()

    def run(self, claim: str):
        print(f"\n🔍 TESTING GET SOURCES FOR CLAIM: {claim}\n")
        
        # Step 1: Fetch evidence documents
        evidence_docs = self.fetcher.fetch(claim)
        print(f"🌐 Fetched {len(evidence_docs)} evidence documents.\n")

        # Step 2: Process with reasoner to extract sources
        reasoning_output = self.reasoner.run(claim, evidence_docs=evidence_docs)

        sources = reasoning_output.get("sources", [])
        
        print(f"\n✅ Extracted {len(sources)} sources:")
        for i, src in enumerate(sources, 1):
            url = src.get("url", "No URL")
            title = src.get("title", "No Title")
            print(f"{i}. {title[:40]} - {url}")


