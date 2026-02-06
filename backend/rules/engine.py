"""
Rule-based evaluation engine.
Computes deterministic scores using configurable weights.
Rules always override AI signals.
"""
import os
import re
import yaml
from typing import Optional

from api.schemas import (
    ParsedResume,
    ParsedJobDescription,
    EvaluationResult,
    ScoreBreakdown,
    ImprovementSuggestion,
    SkillMatch,
)
from .matchers import match_skills


class RuleEngine:
    """Deterministic rule-based evaluation engine."""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the engine with scoring configuration.
        
        Args:
            config_path: Path to config.yaml, defaults to same directory
        """
        if config_path is None:
            config_path = os.path.join(os.path.dirname(__file__), "config.yaml")
        
        self.config = self._load_config(config_path)
        self.weights = self.config["scoring"]["weights"]
        self.thresholds = self.config["scoring"]["match_thresholds"]
        self.penalties = self.config["scoring"]["penalties"]
        self.bounds = self.config["scoring"]["score_bounds"]
        self.enforcement = self.config["scoring"]["required_skill_enforcement"]
    
    def _load_config(self, path: str) -> dict:
        """Load configuration from YAML."""
        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    
    def evaluate(
        self,
        resume: ParsedResume,
        job_description: ParsedJobDescription,
    ) -> EvaluationResult:
        """
        Evaluate resume against job description.
        
        Args:
            resume: Parsed resume data
            job_description: Parsed job description data
        
        Returns:
            EvaluationResult with score, breakdown, and suggestions
        """
        # Step 1: Match skills
        skill_results = match_skills(
            resume_skills=[s.model_dump() for s in resume.skills],
            jd_required_skills=job_description.required_skills,
            jd_optional_skills=job_description.optional_skills,
            full_match_threshold=self.thresholds["full_match"],
            partial_match_threshold=self.thresholds["partial_match"],
        )
        
        # Step 2: Calculate component scores
        required_score = self._calculate_required_skills_score(skill_results)
        optional_score = self._calculate_optional_skills_score(skill_results)
        experience_score = self._calculate_experience_score(resume)
        education_score = self._calculate_education_score(resume, job_description)
        
        # Step 3: Apply weights
        weighted_score = (
            required_score * self.weights["required_skills"] +
            optional_score * self.weights["optional_skills"] +
            experience_score * self.weights["experience_depth"] +
            education_score * self.weights["education_match"]
        )
        
        # Step 4: Apply penalties
        penalties_applied = []
        penalty_total = 0
        
        missing_required_count = len(skill_results["missing_required"])
        if missing_required_count > 0:
            skill_penalty = missing_required_count * self.penalties["missing_required_skill"]
            skill_penalty = max(skill_penalty, self.penalties["max_penalty"])
            penalty_total += skill_penalty
            penalties_applied.append(
                f"{missing_required_count} missing required skill(s): {skill_penalty} points"
            )
        
        weighted_score += penalty_total
        
        # Step 5: Enforce required skill minimum
        if skill_results["stats"]["required_total"] > 0:
            required_ratio = (
                skill_results["stats"]["required_matched"] /
                skill_results["stats"]["required_total"]
            )
            if required_ratio < self.enforcement["minimum_required_matched"]:
                cap = self.enforcement["below_minimum_cap"]
                if weighted_score > cap:
                    weighted_score = cap
                    penalties_applied.append(
                        f"Score capped at {cap}: below {self.enforcement['minimum_required_matched']*100}% required skills matched"
                    )
        
        # Step 6: Bound final score
        final_score = self._bound_score(weighted_score)
        
        # Step 7: Generate explanation
        explanation = self._generate_explanation(
            final_score,
            skill_results,
            required_score,
            optional_score,
            experience_score,
            education_score,
        )
        
        # Step 8: Generate improvement suggestions
        suggestions = self._generate_suggestions(skill_results, resume)
        
        # Step 9: Analyze experience signals
        from api.schemas import ExperienceSignals, ConfidenceLevel
        
        ownership_verbs = ["led", "managed", "architected", "designed", "created", "spearheaded", "built", "developed"]
        leadership_verbs = ["led", "mentored", "managed", "supervised", "directed"]
        
        leadership_signals = []
        ownership_count = 0
        relevant_years = 0.0 # simplified placeholder
        
        if resume.experience:
             # Basic heuristic for years - simplistic for now
            relevant_years = len(resume.experience) * 1.5 
            
            for exp in resume.experience:
                text_lower = (exp.title + " " + exp.description + " " + " ".join(exp.responsibilities)).lower()
                if any(v in text_lower for v in leadership_verbs):
                    leadership_signals.append(f"Leadership detected in {exp.company}")
                
                # Check for ownership in title or action verbs
                if any(v in text_lower for v in ownership_verbs):
                    ownership_count += 1
        
        ownership_strength = "High" if ownership_count >= 2 else "Medium" if ownership_count > 0 else "Low"
        
        exp_signals = ExperienceSignals(
            relevant_years=relevant_years,
            ownership_strength=ownership_strength,
            leadership_signals=leadership_signals,
            responsibility_alignment=f"Found {ownership_count} roles with strong ownership signals."
        )
        
        # Determine overall confidence
        # High if we have good resume content and good JD coverage
        confidence = ConfidenceLevel.MEDIUM
        if len(resume.experience) > 0 and len(resume.skills) > 5 and len(job_description.required_skills) > 0:
            confidence = ConfidenceLevel.HIGH
        elif len(resume.skills) < 3:
            confidence = ConfidenceLevel.LOW
        
        # Build score breakdown
        breakdown = ScoreBreakdown(
            required_skills_score=required_score,
            optional_skills_score=optional_score,
            experience_depth_score=experience_score,
            education_match_score=education_score,
            weights_applied=self.weights,
            penalties_applied=penalties_applied,
        )
        
        return EvaluationResult(
            job_fit_score=final_score,
            confidence_level=confidence,
            score_breakdown=breakdown,
            skill_matches=skill_results["matches"],
            matched_count=skill_results["stats"]["matched_count"],
            partial_count=skill_results["stats"]["partial_count"],
            missing_count=skill_results["stats"]["missing_count"],
            explanation=explanation,
            experience_signals=exp_signals,
            improvement_suggestions=suggestions,
        )
    
    def _calculate_required_skills_score(self, skill_results: dict) -> float:
        """Calculate score for required skills (0-100)."""
        stats = skill_results["stats"]
        if stats["required_total"] == 0:
            return 100.0  # No requirements = full score
        
        matched = stats["required_matched"]
        partial = len(skill_results["partial_required"])
        total = stats["required_total"]
        
        # Full matches count as 100%, partial as 50%
        score = ((matched * 100) + (partial * 50)) / total
        return min(100.0, score)
    
    def _calculate_optional_skills_score(self, skill_results: dict) -> float:
        """Calculate score for optional skills (0-100)."""
        stats = skill_results["stats"]
        if stats["optional_total"] == 0:
            return 100.0  # No optional skills = full score
        
        matched = stats["optional_matched"]
        partial = len(skill_results["partial_optional"])
        total = stats["optional_total"]
        
        score = ((matched * 100) + (partial * 50)) / total
        return min(100.0, score)
    
    def _calculate_experience_score(self, resume: ParsedResume) -> float:
        """Calculate experience depth score (0-100)."""
        if not resume.experience:
            return 50.0  # Neutral if no experience section
        
        score = 50.0  # Base score
        signals = self.config.get("experience_signals", {})
        
        # Analyze experience descriptions
        for exp in resume.experience:
            text = exp.description.lower() + " ".join(exp.responsibilities).lower()
            
            # Check for leadership signals
            if "leadership" in signals:
                for pattern in signals["leadership"]["patterns"]:
                    if re.search(pattern, text, re.IGNORECASE):
                        score += 10 * signals["leadership"]["weight"]
                        break
            
            # Check for scale signals
            if "scale" in signals:
                for pattern in signals["scale"]["patterns"]:
                    if re.search(pattern, text, re.IGNORECASE):
                        score += 10 * signals["scale"]["weight"]
                        break
            
            # Check for technical depth
            if "technical_depth" in signals:
                for pattern in signals["technical_depth"]["patterns"]:
                    if re.search(pattern, text, re.IGNORECASE):
                        score += 8 * signals["technical_depth"]["weight"]
                        break
        
        return min(100.0, score)
    
    def _calculate_education_score(
        self,
        resume: ParsedResume,
        job_description: ParsedJobDescription,
    ) -> float:
        """Calculate education match score (0-100)."""
        if not resume.education:
            return 50.0  # Neutral if no education section
        
        education_config = self.config.get("education", {})
        degree_levels = education_config.get("degree_levels", {})
        
        # Find highest degree level
        max_score = 50.0
        for edu in resume.education:
            degree_lower = edu.degree.lower()
            for degree_type, score in degree_levels.items():
                if degree_type in degree_lower:
                    max_score = max(max_score, score)
                    break
        
        # Check field match if JD has education requirements
        if job_description.education_requirements:
            jd_edu = job_description.education_requirements.lower()
            for edu in resume.education:
                if edu.field_of_study:
                    # Simple keyword matching for field
                    if any(word in jd_edu for word in edu.field_of_study.lower().split()):
                        max_score += education_config.get("field_match_bonus", 10)
                        break
        
        return min(100.0, max_score)
    
    def _bound_score(self, score: float) -> int:
        """Bound score to configured min/max."""
        bounded = max(self.bounds["min"], min(self.bounds["max"], score))
        return round(bounded)
    
    def _generate_explanation(
        self,
        score: int,
        skill_results: dict,
        required_score: float,
        optional_score: float,
        experience_score: float,
        education_score: float,
    ) -> str:
        """Generate human-readable explanation."""
        stats = skill_results["stats"]
        
        explanation = f"""Your job-fit score is {score}/100.

This score reflects:
• {stats['required_matched']} of {stats['required_total']} required skills matched ({required_score:.0f}% score)
• {stats['optional_matched']} of {stats['optional_total']} preferred skills matched ({optional_score:.0f}% score)
• Experience depth score: {experience_score:.0f}%
• Education alignment score: {education_score:.0f}%

"""
        
        if skill_results["missing_required"]:
            explanation += f"Missing required skills: {', '.join(skill_results['missing_required'][:5])}\n"
        
        if skill_results["partial_required"]:
            explanation += f"Partially matched skills: {', '.join(skill_results['partial_required'][:5])}\n"
        
        return explanation.strip()
    
    def _generate_suggestions(
        self,
        skill_results: dict,
        resume: ParsedResume,
    ) -> list[ImprovementSuggestion]:
        """Generate actionable improvement suggestions."""
        suggestions = []
        max_suggestions = self.config.get("output", {}).get("max_suggestions", 5)
        
        # Priority 1: Missing required skills
        for skill in skill_results["missing_required"][:3]:
            suggestions.append(ImprovementSuggestion(
                category="Missing Skill",
                priority=1,
                suggestion=f"Add '{skill}' to your resume with specific examples of usage",
                affected_skills=[skill],
            ))
        
        # Priority 2: Partially matched skills need more evidence
        for skill in skill_results["partial_required"][:2]:
            suggestions.append(ImprovementSuggestion(
                category="Strengthen Evidence",
                priority=2,
                suggestion=f"Provide more concrete examples for '{skill}' in your experience section",
                affected_skills=[skill],
            ))
        
        # Priority 3: Experience section improvements
        if not resume.experience:
            suggestions.append(ImprovementSuggestion(
                category="Experience",
                priority=3,
                suggestion="Add a detailed work experience section with responsibilities and achievements",
            ))
        else:
            # Check for metrics
            has_metrics = any(
                re.search(r'\d+%|\d+ (users|customers|requests)', 
                         " ".join(exp.responsibilities))
                for exp in resume.experience
            )
            if not has_metrics:
                suggestions.append(ImprovementSuggestion(
                    category="Quantify Impact",
                    priority=3,
                    suggestion="Add quantifiable metrics to your experience (e.g., 'Improved performance by 40%')",
                ))
        
        # Priority 4: Missing optional skills
        for skill in skill_results["missing_optional"][:2]:
            suggestions.append(ImprovementSuggestion(
                category="Nice to Have",
                priority=4,
                suggestion=f"Consider adding '{skill}' if you have experience with it",
                affected_skills=[skill],
            ))
        
        return suggestions[:max_suggestions]


# Module-level convenience function
_engine_instance = None


def get_engine() -> RuleEngine:
    """Get singleton engine instance."""
    global _engine_instance
    if _engine_instance is None:
        _engine_instance = RuleEngine()
    return _engine_instance


def evaluate(resume: ParsedResume, job_description: ParsedJobDescription) -> EvaluationResult:
    """Convenience function to evaluate resume."""
    return get_engine().evaluate(resume, job_description)
