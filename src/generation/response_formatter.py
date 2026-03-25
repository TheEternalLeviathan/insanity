from urllib.parse import urlparse


class ResponseFormatter:
    
    def _format_source_name(self, source: dict) -> str:
        """Format source name for better readability"""
        title = source.get('title', '')
        url = source.get('url', '')
        
        if title and title != "Unknown source" and len(title) > 3:
            if len(title) > 50:
                return title[:47] + "..."
            return title
        
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.replace('www.', '')
            return domain
        except:
            return "Web Source"
    
    def format(
        self,
        claim,
        verdict,
        confidence,
        explanation,
        supporting_facts,
        contradicting_facts,
        sources,
        timings=None,
    ):
        """Format output for WhatsApp (concise and readable)"""
        lines = []

        # Header with emoji
        verdict_emoji = {
            "true": "✅",
            "false": "❌",
            "likely_true": "✅",
            "likely_false": "⚠️",
            "needs_verification": "❓"
        }
        emoji = verdict_emoji.get(verdict.lower(), "❓")
        
        lines.append(f"{emoji} *FACT-CHECK RESULT*")
        lines.append("")
        
        # Claim
        claim_display = claim if len(claim) < 200 else claim[:197] + "..."
        lines.append(f"📌 *Claim:*")
        lines.append(f'"{claim_display}"')
        lines.append("")
        
        # Verdict
        verdict_display = verdict.replace("_", " ").upper()
        lines.append(f"{emoji} *Verdict:* {verdict_display}")
        lines.append(f"🎯 *Confidence:* {int(confidence * 100)}%")
        lines.append("")

        # Analysis
        lines.append("📊 *Analysis:*")
        if not explanation or not explanation.strip():
            explanation = "The verdict is based on available evidence. Please review the sources below."
        lines.append(explanation.strip())
        lines.append("")

        # Supporting Evidence (show if exists)
        if supporting_facts:
            lines.append("✅ *Supporting Evidence:*")
            for i, s in enumerate(supporting_facts[:2], 1):
                s_display = s if len(s) < 150 else s[:147] + "..."
                lines.append(f"{i}. {s_display}")
            lines.append("")

        # Contradicting Evidence (show if exists)
        if contradicting_facts:
            lines.append("❌ *Contradicting Evidence:*")
            for i, c in enumerate(contradicting_facts[:2], 1):
                c_display = c if len(c) < 150 else c[:147] + "..."
                lines.append(f"{i}. {c_display}")
            lines.append("")

        # Sources
        if sources:
            lines.append("📚 *Sources:*")
            
            source_count = 0
            for source in sources[:3]:
                url = source.get('url', '')
                
                if not url:
                    continue
                
                source_count += 1
                source_name = self._format_source_name(source)
                
                lines.append(f"{source_count}. {source_name}")
                lines.append(f"   {url}")
            
            if source_count > 0:
                lines.append("")

        # Footer
        lines.append("━" * 30)
        lines.append("🤖 *AI Fact-Checker*")
        lines.append("⚡ ML + Web Evidence")

        return "\n".join(lines)