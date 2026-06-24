def score_findings(findings: list[dict]) -> dict:
    """
    Calculate risk score (0-100) and overall risk tier based on findings.
    Starts at 100 (low risk). Each finding deducts points based on severity and confidence.
    """
    score = 100.0
    
    counts = {
        "critical": 0,
        "high": 0,
        "medium": 0,
        "low": 0
    }
    
    # Weights for point deductions
    deductions = {
        "critical": 35,
        "high": 20,
        "medium": 10,
        "low": 3
    }
    
    for finding in findings:
        severity = finding.get("severity", "low").lower()
        confidence = float(finding.get("confidence_score", 1.0))
        
        if severity in counts:
            counts[severity] += 1
            
            # Deduct points scaled by confidence
            deduction = deductions.get(severity, 0) * confidence
            score -= deduction
            
    # Ensure score doesn't go below 0
    score = max(0.0, score)
    
    # Determine Tier based on score and criticals
    if counts["critical"] > 0 or score < 40:
        tier = "CRITICAL"
        summary = "CRITICAL RISK: Major adverse findings identified requiring immediate review or rejection."
        recommendations = "IMMEDIATE ESCALATION. Do not proceed with vendor onboarding until findings are resolved."
    elif counts["high"] > 0 or score < 70:
        tier = "HIGH"
        summary = "HIGH RISK: Significant adverse findings detected. Elevated due diligence required."
        recommendations = "Assign to compliance analyst for manual review of high-severity findings."
    elif counts["medium"] > 0 or score < 90:
        tier = "MEDIUM"
        summary = "MEDIUM RISK: Minor to moderate issues found. Standard monitoring recommended."
        recommendations = "Proceed with caution. Request clarification from vendor on medium-severity items."
    else:
        tier = "LOW"
        summary = "LOW RISK: No significant adverse findings. Vendor passes automated screening."
        recommendations = "Proceed with standard onboarding."

    return {
        "score": round(score, 2),
        "tier": tier,
        "summary": summary,
        "critical": counts["critical"],
        "high": counts["high"],
        "medium": counts["medium"],
        "low": counts["low"],
        "recommendations": recommendations
    }
