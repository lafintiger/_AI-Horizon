#!/usr/bin/env python3
"""
Academic References and Citations for AI-Horizon Scoring Methodologies

This module provides comprehensive academic citations and references for all scoring
algorithms and methodologies used in the AI-Horizon system, ensuring proper
attribution for NSF project documentation.
"""

from typing import Dict, List, Any
from dataclasses import dataclass


@dataclass
class Citation:
    """Academic citation with complete bibliographic information."""
    authors: List[str]
    title: str
    venue: str  # Journal, conference, or institution
    year: int
    doi: str = ""
    url: str = ""
    pages: str = ""
    volume: str = ""
    issue: str = ""
    publisher: str = ""
    citation_key: str = ""
    
    def format_apa(self) -> str:
        """Format citation in APA style."""
        author_str = ", ".join(self.authors)
        if len(self.authors) > 1:
            last_comma = author_str.rfind(", ")
            author_str = author_str[:last_comma] + ", & " + author_str[last_comma + 2:]
        
        citation = f"{author_str} ({self.year}). {self.title}. {self.venue}"
        
        if self.volume:
            citation += f", {self.volume}"
        if self.issue:
            citation += f"({self.issue})"
        if self.pages:
            citation += f", {self.pages}"
        
        if self.doi:
            citation += f". https://doi.org/{self.doi}"
        elif self.url:
            citation += f". {self.url}"
        
        return citation + "."
    
    def format_bibtex(self) -> str:
        """Format citation in BibTeX style."""
        bib_type = "article" if any(j in self.venue.lower() for j in ["journal", "transactions"]) else "inproceedings"
        
        key = self.citation_key or f"{self.authors[0].split()[-1].lower()}{self.year}"
        
        bibtex = f"@{bib_type}{{{key},\n"
        bibtex += f"  author = {{{' and '.join(self.authors)}}},\n"
        bibtex += f"  title = {{{self.title}}},\n"
        bibtex += f"  year = {{{self.year}}},\n"
        
        if bib_type == "article":
            bibtex += f"  journal = {{{self.venue}}},\n"
            if self.volume:
                bibtex += f"  volume = {{{self.volume}}},\n"
            if self.issue:
                bibtex += f"  number = {{{self.issue}}},\n"
        else:
            bibtex += f"  booktitle = {{{self.venue}}},\n"
        
        if self.pages:
            bibtex += f"  pages = {{{self.pages}}},\n"
        if self.publisher:
            bibtex += f"  publisher = {{{self.publisher}}},\n"
        if self.doi:
            bibtex += f"  doi = {{{self.doi}}},\n"
        if self.url:
            bibtex += f"  url = {{{self.url}}},\n"
        
        bibtex = bibtex.rstrip(",\n") + "\n}"
        return bibtex


class AcademicReferences:
    """
    Comprehensive academic references for AI-Horizon methodologies.
    
    This class maintains all citations and references used in the scoring
    algorithms, quality metrics, and analytical methodologies.
    """
    
    def __init__(self):
        self.citations = self._initialize_citations()
    
    def _initialize_citations(self) -> Dict[str, Citation]:
        """Initialize all academic citations used in the system."""
        return {
            # Content Quality Scoring References
            "flesch_kincaid": Citation(
                authors=["Flesch, R.", "Kincaid, J. P.", "Fishburne, R. P.", "Chissom, B. S."],
                title="Derivation of New Readability Formulas (Automated Readability Index, Fog Count and Flesch Reading Ease Formula) for Navy Enlisted Personnel",
                venue="Institute for Simulation and Training, University of Central Florida",
                year=1975,
                citation_key="flesch1975derivation",
                url="https://apps.dtic.mil/sti/citations/ADA006655"
            ),
            
            "information_theory": Citation(
                authors=["Shannon, C. E."],
                title="A Mathematical Theory of Communication",
                venue="The Bell System Technical Journal",
                year=1948,
                volume="27",
                issue="3",
                pages="379-423",
                doi="10.1002/j.1538-7305.1948.tb01338.x",
                citation_key="shannon1948mathematical"
            ),
            
            # Source Credibility Scoring References
            "domain_authority": Citation(
                authors=["Moz Inc."],
                title="Domain Authority: A Comprehensive Guide to Moz's Website Authority Metric",
                venue="Moz Technical Documentation",
                year=2023,
                url="https://moz.com/learn/seo/domain-authority",
                citation_key="moz2023domain"
            ),
            
            "academic_credibility": Citation(
                authors=["Hirsch, J. E."],
                title="An index to quantify an individual's scientific research output",
                venue="Proceedings of the National Academy of Sciences",
                year=2005,
                volume="102",
                issue="46",
                pages="16569-16572",
                doi="10.1073/pnas.0507655102",
                citation_key="hirsch2005index"
            ),
            
            "source_reliability": Citation(
                authors=["Castillo, C.", "Mendoza, M.", "Poblete, B."],
                title="Information credibility on twitter",
                venue="Proceedings of the 20th International Conference on World Wide Web",
                year=2011,
                pages="675-684",
                doi="10.1145/1963405.1963500",
                citation_key="castillo2011information"
            ),
            
            # Semantic Similarity and Classification References
            "sentence_transformers": Citation(
                authors=["Reimers, N.", "Gurevych, I."],
                title="Sentence-BERT: Sentence Embeddings using Siamese BERT-Networks",
                venue="Proceedings of the 2019 Conference on Empirical Methods in Natural Language Processing and the 9th International Joint Conference on Natural Language Processing (EMNLP-IJCNLP)",
                year=2019,
                pages="3982-3992",
                doi="10.18653/v1/D19-1410",
                citation_key="reimers2019sentence"
            ),
            
            "bert_embeddings": Citation(
                authors=["Devlin, J.", "Chang, M. W.", "Lee, K.", "Toutanova, K."],
                title="BERT: Pre-training of Deep Bidirectional Transformers for Language Understanding",
                venue="Proceedings of the 2019 Conference of the North American Chapter of the Association for Computational Linguistics: Human Language Technologies",
                year=2019,
                pages="4171-4186",
                doi="10.18653/v1/N19-1423",
                citation_key="devlin2019bert"
            ),
            
            "cosine_similarity": Citation(
                authors=["Singhal, A."],
                title="Modern Information Retrieval: A Brief Overview",
                venue="IEEE Data Engineering Bulletin",
                year=2001,
                volume="24",
                issue="4",
                pages="35-43",
                citation_key="singhal2001modern"
            ),
            
            # Text Classification and Feature Engineering
            "tfidf_weighting": Citation(
                authors=["Salton, G.", "Buckley, C."],
                title="Term-weighting approaches in automatic text retrieval",
                venue="Information Processing & Management",
                year=1988,
                volume="24",
                issue="5",
                pages="513-523",
                doi="10.1016/0306-4573(88)90021-0",
                citation_key="salton1988term"
            ),
            
            "feature_selection": Citation(
                authors=["Yang, Y.", "Pedersen, J. O."],
                title="A comparative study on feature selection in text categorization",
                venue="Proceedings of the 14th International Conference on Machine Learning",
                year=1997,
                pages="412-420",
                citation_key="yang1997comparative"
            ),
            
            # Machine Learning and Classification Algorithms
            "logistic_regression": Citation(
                authors=["Hosmer Jr, D. W.", "Lemeshow, S.", "Sturdivant, R. X."],
                title="Applied logistic regression",
                venue="John Wiley & Sons",
                year=2013,
                publisher="John Wiley & Sons",
                citation_key="hosmer2013applied"
            ),
            
            "naive_bayes": Citation(
                authors=["McCallum, A.", "Nigam, K."],
                title="A comparison of event models for naive bayes text classification",
                venue="AAAI-98 workshop on learning for text categorization",
                year=1998,
                pages="41-48",
                citation_key="mccallum1998comparison"
            ),
            
            # Information Retrieval and Search Methodologies
            "query_expansion": Citation(
                authors=["Carpineto, C.", "Romano, G."],
                title="A survey of automatic query expansion in information retrieval",
                venue="ACM Computing Surveys",
                year=2012,
                volume="44",
                issue="1",
                pages="1-50",
                doi="10.1145/2071389.2071390",
                citation_key="carpineto2012survey"
            ),
            
            "relevance_feedback": Citation(
                authors=["Rocchio, J."],
                title="Relevance feedback in information retrieval",
                venue="The SMART Retrieval System: Experiments in Automatic Document Processing",
                year=1971,
                pages="313-323",
                citation_key="rocchio1971relevance"
            ),
            
            # Evaluation Metrics and Validation
            "precision_recall": Citation(
                authors=["Manning, C. D.", "Raghavan, P.", "Schütze, H."],
                title="Introduction to information retrieval",
                venue="Cambridge University Press",
                year=2008,
                publisher="Cambridge University Press",
                citation_key="manning2008introduction"
            ),
            
            "f1_score": Citation(
                authors=["Rijsbergen, C. J. V."],
                title="Information Retrieval",
                venue="Butterworth-Heinemann",
                year=1979,
                publisher="Butterworth-Heinemann",
                citation_key="rijsbergen1979information"
            ),
            
            # Content Analysis and Topic Modeling
            "lda_topic_modeling": Citation(
                authors=["Blei, D. M.", "Ng, A. Y.", "Jordan, M. I."],
                title="Latent dirichlet allocation",
                venue="Journal of Machine Learning Research",
                year=2003,
                volume="3",
                pages="993-1022",
                citation_key="blei2003latent"
            ),
            
            "content_analysis": Citation(
                authors=["Krippendorff, K."],
                title="Content analysis: An introduction to its methodology",
                venue="Sage Publications",
                year=2018,
                publisher="Sage Publications",
                citation_key="krippendorff2018content"
            ),
            
            # Cybersecurity Workforce and AI Impact Studies
            "cybersecurity_workforce": Citation(
                authors=["NICE Cybersecurity Workforce Framework"],
                title="National Initiative for Cybersecurity Education (NICE) Cybersecurity Workforce Framework",
                venue="NIST Special Publication 800-181 Revision 1",
                year=2020,
                doi="10.6028/NIST.SP.800-181r1",
                citation_key="nice2020framework"
            ),
            
            "ai_workforce_impact": Citation(
                authors=["Brynjolfsson, E.", "Mitchell, T."],
                title="What can machine learning do? Workforce implications",
                venue="Science",
                year=2017,
                volume="358",
                issue="6370",
                pages="1530-1534",
                doi="10.1126/science.aap8062",
                citation_key="brynjolfsson2017machine"
            ),
            
            # Scoring Formula Development References
            "weighted_scoring": Citation(
                authors=["Saaty, T. L."],
                title="The analytic hierarchy process: planning, priority setting, resource allocation",
                venue="McGraw-Hill International Book Co.",
                year=1980,
                publisher="McGraw-Hill",
                citation_key="saaty1980analytic"
            ),
            
            "normalization_techniques": Citation(
                authors=["Han, J.", "Pei, J.", "Kamber, M."],
                title="Data mining: concepts and techniques",
                venue="Elsevier",
                year=2011,
                publisher="Elsevier",
                citation_key="han2011data"
            )
        }
    
    def get_citation(self, key: str) -> Citation:
        """Get a specific citation by key."""
        if key not in self.citations:
            raise KeyError(f"Citation '{key}' not found")
        return self.citations[key]
    
    def get_citations_for_component(self, component: str) -> List[Citation]:
        """Get all citations relevant to a specific system component."""
        component_mappings = {
            "quality_scoring": [
                "flesch_kincaid", "information_theory", "tfidf_weighting", 
                "content_analysis", "weighted_scoring", "normalization_techniques"
            ],
            "credibility_scoring": [
                "domain_authority", "academic_credibility", "source_reliability",
                "weighted_scoring", "normalization_techniques"
            ],
            "content_classification": [
                "sentence_transformers", "bert_embeddings", "cosine_similarity",
                "tfidf_weighting", "feature_selection", "logistic_regression",
                "naive_bayes"
            ],
            "search_methodology": [
                "query_expansion", "relevance_feedback", "information_theory",
                "precision_recall", "f1_score"
            ],
            "topic_modeling": [
                "lda_topic_modeling", "sentence_transformers", "bert_embeddings"
            ],
            "workforce_analysis": [
                "cybersecurity_workforce", "ai_workforce_impact", "content_analysis"
            ]
        }
        
        if component not in component_mappings:
            return []
        
        return [self.citations[key] for key in component_mappings[component]]
    
    def format_bibliography(self, component: str = None, style: str = "apa") -> str:
        """
        Generate a formatted bibliography for a component or all citations.
        
        Args:
            component: Specific component to generate bibliography for
            style: Citation style ("apa" or "bibtex")
            
        Returns:
            Formatted bibliography string
        """
        if component:
            citations = self.get_citations_for_component(component)
        else:
            citations = list(self.citations.values())
        
        # Sort citations by author and year
        citations.sort(key=lambda c: (c.authors[0], c.year))
        
        if style.lower() == "apa":
            return "\n\n".join(c.format_apa() for c in citations)
        elif style.lower() == "bibtex":
            return "\n\n".join(c.format_bibtex() for c in citations)
        else:
            raise ValueError(f"Unsupported citation style: {style}")
    
    def get_scoring_formula_documentation(self) -> Dict[str, Dict[str, Any]]:
        """
        Get comprehensive documentation for all scoring formulas with references.
        
        Returns:
            Dictionary with formula documentation and citations
        """
        return {
            "content_quality_score": {
                "formula": "0.3 * content_length_score + 0.2 * keyword_density + 0.2 * readability_score + 0.3 * structure_score",
                "description": "Weighted combination of content metrics to assess article quality and depth",
                "components": {
                    "content_length_score": "Normalized score based on article length (min-max normalization)",
                    "keyword_density": "TF-IDF weighted density of domain-relevant keywords",
                    "readability_score": "Flesch-Kincaid readability assessment",
                    "structure_score": "Assessment of content organization and formatting"
                },
                "citations": [
                    self.get_citation("flesch_kincaid"),
                    self.get_citation("tfidf_weighting"),
                    self.get_citation("normalization_techniques"),
                    self.get_citation("weighted_scoring")
                ],
                "validation": "Weights determined through expert judgment following Analytic Hierarchy Process principles"
            },
            
            "credibility_score": {
                "formula": "0.4 * source_authority + 0.3 * domain_expertise + 0.2 * publication_recency + 0.1 * citation_count",
                "description": "Multi-factor assessment of source credibility and authority",
                "components": {
                    "source_authority": "Domain authority and institutional credibility assessment",
                    "domain_expertise": "Relevance of source domain to cybersecurity field",
                    "publication_recency": "Temporal relevance weighting (exponential decay)",
                    "citation_count": "Academic or professional citation metrics where available"
                },
                "citations": [
                    self.get_citation("domain_authority"),
                    self.get_citation("academic_credibility"),
                    self.get_citation("source_reliability"),
                    self.get_citation("weighted_scoring")
                ],
                "validation": "Weights based on information science research on source credibility"
            },
            
            "semantic_similarity": {
                "formula": "cosine_similarity(sentence_bert_embedding(query), sentence_bert_embedding(content))",
                "description": "Semantic similarity calculation using pre-trained BERT embeddings",
                "components": {
                    "sentence_bert_embedding": "Pre-trained SBERT model for semantic embeddings",
                    "cosine_similarity": "Angular similarity measure between embedding vectors"
                },
                "citations": [
                    self.get_citation("sentence_transformers"),
                    self.get_citation("bert_embeddings"),
                    self.get_citation("cosine_similarity")
                ],
                "validation": "SBERT model validated on semantic textual similarity benchmarks"
            },
            
            "category_confidence": {
                "formula": "sigmoid(weighted_indicator_score) * content_quality_modifier",
                "description": "Confidence score for category classification based on indicator presence",
                "components": {
                    "weighted_indicator_score": "TF-IDF weighted sum of category-specific indicators",
                    "sigmoid": "Sigmoid function for probability normalization",
                    "content_quality_modifier": "Quality-based confidence adjustment"
                },
                "citations": [
                    self.get_citation("tfidf_weighting"),
                    self.get_citation("logistic_regression"),
                    self.get_citation("feature_selection")
                ],
                "validation": "Indicator weights derived from cybersecurity domain analysis"
            }
        }


# Global reference manager instance
academic_refs = AcademicReferences()


def get_formula_documentation(formula_name: str) -> Dict[str, Any]:
    """Get documentation for a specific scoring formula."""
    docs = academic_refs.get_scoring_formula_documentation()
    if formula_name not in docs:
        raise KeyError(f"Formula documentation for '{formula_name}' not found")
    return docs[formula_name]


def get_bibliography_for_component(component: str, style: str = "apa") -> str:
    """Get formatted bibliography for a system component."""
    return academic_refs.format_bibliography(component, style)


def export_all_references(output_file: str, style: str = "apa"):
    """Export all references to a file."""
    bibliography = academic_refs.format_bibliography(style=style)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(f"# AI-Horizon Academic References\n\n")
        f.write(f"Complete bibliography of academic sources used in AI-Horizon methodologies.\n\n")
        f.write(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write(f"---\n\n{bibliography}")


if __name__ == "__main__":
    # Example usage and testing
    from datetime import datetime
    
    print("🔍 AI-Horizon Academic References System")
    print("=" * 50)
    
    # Test individual citation
    citation = academic_refs.get_citation("flesch_kincaid")
    print("Sample Citation (APA):")
    print(citation.format_apa())
    print()
    
    # Test component bibliography
    print("Quality Scoring Bibliography:")
    print(academic_refs.format_bibliography("quality_scoring"))
    print()
    
    # Test formula documentation
    quality_docs = get_formula_documentation("content_quality_score")
    print("Content Quality Score Documentation:")
    print(f"Formula: {quality_docs['formula']}")
    print(f"Description: {quality_docs['description']}")
    print("Citations:")
    for cite in quality_docs['citations']:
        print(f"  - {cite.format_apa()}") 