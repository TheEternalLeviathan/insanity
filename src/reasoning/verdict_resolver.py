

# src/reasoning/verdict_resolver.py

class VerdictResolver:
    """
    Hybrid verdict resolution with authority tiering and mixed evidence handling.
    """
    
    # Authority tier definitions
    TIER_1_AUTHORITY = [  # Highest trust
        "wikipedia.org", "britannica.com",
        ".gov", ".edu",
        "reuters.com", "apnews.com", "bbc.com"
    ]
    
    TIER_2_AUTHORITY = [  # High trust
        "theguardian.com", "nytimes.com", "washingtonpost.com",
        "thehindu.com", "indianexpress.com", "hindustantimes.com",
        "indiatoday.in", "timesofindia.com"
    ]
    
    TIER_3_AUTHORITY = [  # Moderate trust
        "snopes.com", "factcheck.org", "politifact.com",
        "aljazeera.com", "cnn.com", "forbes.com"
    ]

    def resolve(self, ml: dict, evidence: dict):
        """Resolve with authority-weighted confidence and mixed evidence handling"""
        
        supporting = evidence.get("supporting_facts", [])
        contradicting = evidence.get("contradicting_facts", [])
        sources = evidence.get("sources", [])
        claim = evidence.get("claim", "")
        
        sup_count = len(supporting)
        con_count = len(contradicting)
        
        ml_verdict = ml.get("verdict", "needs_verification")
        ml_confidence = ml.get("confidence", 0.5)
        
        # Check authority tier
        authority_tier = self._get_authority_tier(sources)
        has_tier1 = authority_tier == 1
        has_tier2 = authority_tier == 2
        has_authority = authority_tier <= 2
        
        print(f"\n📊 VERDICT RESOLUTION:")
        print(f"   ML: {ml_verdict} ({ml_confidence:.2f})")
        print(f"   Evidence: {sup_count} supporting, {con_count} contradicting")
        print(f"   Authority tier: {authority_tier} (1=highest)")
        
        # ================================
        # NEW: HANDLE MIXED EVIDENCE FIRST
        # ================================
        
        if sup_count >= 1 and con_count >= 1:
            print(f"   ⚠️ Mixed evidence detected")
            
            # If contradictions outnumber support significantly
            if con_count >= sup_count * 2:
                return self._create_verdict(
                    verdict="likely_false",
                    confidence=0.75,
                    source="mixed_evidence_contradiction_dominant",
                    sup_count=sup_count,
                    con_count=con_count,
                    sources=sources,
                    ml=ml
                )
            
            # If support outnumbers contradictions significantly
            elif sup_count >= con_count * 2:
                return self._create_verdict(
                    verdict="likely_true",
                    confidence=0.75,
                    source="mixed_evidence_support_dominant",
                    sup_count=sup_count,
                    con_count=con_count,
                    sources=sources,
                    ml=ml
                )
            
            # Roughly equal - uncertain
            else:
                return self._create_verdict(
                    verdict="needs_verification",
                    confidence=0.60,
                    source="conflicting_evidence",
                    sup_count=sup_count,
                    con_count=con_count,
                    sources=sources,
                    ml=ml
                )
        
        # ================================
        # TIER 1: STRONG EVIDENCE (NO CONFLICT)
        # ================================
        
        # 🔴 Strong contradiction with Tier 1 authority
        if con_count >= 1 and sup_count == 0 and has_tier1:
            return self._create_verdict(
                verdict="false",
                confidence=0.97,
                source="tier1_authoritative_contradiction",
                sup_count=sup_count,
                con_count=con_count,
                sources=sources,
                ml=ml
            )
        
        # 🔴 Strong contradiction with Tier 2 authority
        if con_count >= 1 and sup_count == 0 and has_tier2:
            return self._create_verdict(
                verdict="false",
                confidence=0.95,
                source="authoritative_contradiction",
                sup_count=sup_count,
                con_count=con_count,
                sources=sources,
                ml=ml
            )
        
        # 🔴 Multiple contradictions (any source)
        if con_count >= 2 and sup_count == 0:
            return self._create_verdict(
                verdict="false",
                confidence=0.92,
                source="strong_contradiction",
                sup_count=sup_count,
                con_count=con_count,
                sources=sources,
                ml=ml
            )
        
        # 🟢 Strong support with Tier 1 authority
        if sup_count >= 2 and con_count == 0 and has_tier1:
            return self._create_verdict(
                verdict="true",
                confidence=0.95,
                source="tier1_authoritative_support",
                sup_count=sup_count,
                con_count=con_count,
                sources=sources,
                ml=ml
            )
        
        # 🟢 Strong support with Tier 2 authority
        if sup_count >= 2 and con_count == 0 and has_tier2:
            return self._create_verdict(
                verdict="true",
                confidence=0.92,
                source="authoritative_support",
                sup_count=sup_count,
                con_count=con_count,
                sources=sources,
                ml=ml
            )
        
        # ================================
        # TIER 2: ML HIGH CONFIDENCE
        # ================================
        
        if ml_confidence >= 0.85 and con_count == 0:
            return self._create_verdict(
                verdict=ml_verdict,
                confidence=ml_confidence,
                source="ml_high_confidence",
                sup_count=sup_count,
                con_count=con_count,
                sources=sources,
                ml=ml
            )
        
        if ml_confidence >= 0.75 and con_count == 0:
            if ml_verdict == "false":
                return self._create_verdict(
                    verdict="false",
                    confidence=ml_confidence,
                    source="ml_supported_by_evidence",
                    sup_count=sup_count,
                    con_count=con_count,
                    sources=sources,
                    ml=ml
                )
        
        # ================================
        # TIER 3: WEAKER PATTERNS
        # ================================
        
        if con_count == 1 and sup_count == 0:
            return self._create_verdict(
                verdict="likely_false",
                confidence=0.75,
                source="single_contradiction",
                sup_count=sup_count,
                con_count=con_count,
                sources=sources,
                ml=ml
            )
        
        if sup_count >= 2 and con_count == 0:
            return self._create_verdict(
                verdict="true",
                confidence=0.85,
                source="strong_support",
                sup_count=sup_count,
                con_count=con_count,
                sources=sources,
                ml=ml
            )
        
        if sup_count == 1 and con_count == 0:
            return self._create_verdict(
                verdict="likely_true",
                confidence=0.70,
                source="single_support",
                sup_count=sup_count,
                con_count=con_count,
                sources=sources,
                ml=ml
            )
        
        # Rumor pattern
        if self._is_rumor_pattern(claim) and sup_count == 0:
            if ml_verdict == "false" and ml_confidence >= 0.6:
                return self._create_verdict(
                    verdict="likely_false",
                    confidence=0.80,
                    source="rumor_ml_agreement",
                    sup_count=sup_count,
                    con_count=con_count,
                    sources=sources,
                    ml=ml
                )
            else:
                return self._create_verdict(
                    verdict="likely_false",
                    confidence=0.70,
                    source="rumor_without_evidence",
                    sup_count=sup_count,
                    con_count=con_count,
                    sources=sources,
                    ml=ml
                )
        
        if ml_confidence >= 0.60 and con_count == 0:
            return self._create_verdict(
                verdict=ml_verdict,
                confidence=ml_confidence,
                source="ml_medium_confidence",
                sup_count=sup_count,
                con_count=con_count,
                sources=sources,
                ml=ml
            )
        
        return self._create_verdict(
            verdict="needs_verification",
            confidence=0.50,
            source="insufficient_evidence",
            sup_count=sup_count,
            con_count=con_count,
            sources=sources,
            ml=ml
        )
    
    def _get_authority_tier(self, sources) -> int:
        """Get highest authority tier (1=best, 4=none)"""
        if not sources:
            return 4
        
        for source in sources:
            url = (source.get("url") or "").lower()
            
            if any(domain in url for domain in self.TIER_1_AUTHORITY):
                return 1
            
            if any(domain in url for domain in self.TIER_2_AUTHORITY):
                return 2
            
            if any(domain in url for domain in self.TIER_3_AUTHORITY):
                return 3
        
        return 4
    
    def _create_verdict(self, verdict, confidence, source, sup_count, con_count, sources, ml):
        return {
            "final_verdict": verdict,
            "confidence": confidence,
            "decision_source": source,
            "evidence_summary": {
                "supporting": sup_count,
                "contradicting": con_count,
                "sources": len(sources),
            },
            "ml_input": ml
        }
    
    def _is_rumor_pattern(self, claim: str) -> bool:
        claim_lower = claim.lower()
        rumor_indicators = [
            "according to sources", "allegedly", "leaked", "secret", "hidden",
            "claim the government", "sources say", "reportedly",
            "it is said that", "rumors suggest", "unconfirmed reports"
        ]
        return any(indicator in claim_lower for indicator in rumor_indicators)