"""
Query Intent Mapper
Maps user queries to relevant TOC section types for targeted retrieval
"""

from typing import List, Dict
import re


class QueryIntentMapper:
    """
    Maps natural language queries to TOC section types

    Example:
        mapper = QueryIntentMapper()
        sections = mapper.get_section_types("What is the well depth?")
        # Returns: ['depth', 'borehole']
    """

    def __init__(self):
        # Keyword → section type mapping
        # Based on analysis of 101 TOC entries from 7 wells
        self.keyword_to_section = {
            # Depth-related queries (Sub-Challenge 2)
            'depth': ['depth', 'borehole'],
            'depths': ['depth', 'borehole'],
            'md': ['depth', 'trajectory'],
            'measured depth': ['depth', 'trajectory'],
            'tvd': ['depth', 'trajectory'],
            'true vertical depth': ['depth', 'trajectory'],
            'vertical': ['depth', 'trajectory'],

            # Casing-related queries (Sub-Challenge 2)
            'casing': ['casing'],
            'casings': ['casing'],
            'diameter': ['casing'],
            'inner diameter': ['casing'],
            'id': ['casing'],
            'tubing': ['casing'],
            'completion': ['casing', 'technical_summary'],

            # Trajectory-related queries
            'trajectory': ['trajectory', 'depth'],
            'directional': ['trajectory', 'depth'],
            'survey': ['trajectory', 'depth'],
            'deviation': ['trajectory', 'depth'],
            'inclination': ['trajectory', 'depth'],

            # Borehole/well data queries
            'borehole': ['borehole', 'depth'],
            'well data': ['borehole', 'technical_summary'],
            'well name': ['borehole', 'technical_summary'],
            'location': ['borehole'],

            # General/summary queries
            'summary': ['technical_summary'],
            'technical summary': ['technical_summary'],
            'overview': ['technical_summary', 'borehole'],
            'specifications': ['borehole', 'casing', 'depth', 'technical_summary'],

            # Drilling-related
            'drilling': ['technical_summary'],
            'mud': ['technical_summary'],
            'fluid': ['technical_summary'],

            # Geology-related
            'geology': ['technical_summary'],
            'formation': ['technical_summary'],
            'reservoir': ['technical_summary'],
        }

        # Section type descriptions (for logging/debugging)
        self.section_descriptions = {
            'casing': 'Casing and tubing specifications (ID, OD, depth)',
            'depth': 'Depth measurements (MD, TVD, KOP, EOB)',
            'borehole': 'General well data (name, location, operator)',
            'trajectory': 'Directional drilling data (survey, deviation)',
            'technical_summary': 'Operations summary, technical details',
        }

    def get_section_types(self, query: str) -> List[str]:
        """
        Map user query to relevant section types

        Args:
            query: Natural language query (e.g., "What is the well depth?")

        Returns:
            List of section types to search, ordered by relevance
            Returns all section types if no keywords match

        Example:
            >>> mapper = QueryIntentMapper()
            >>> mapper.get_section_types("What is the measured depth?")
            ['depth', 'trajectory']
        """
        query_lower = query.lower()
        section_types = []
        matched_keywords = []

        # Match keywords (longest first to handle multi-word phrases)
        sorted_keywords = sorted(self.keyword_to_section.keys(),
                                 key=len, reverse=True)

        for keyword in sorted_keywords:
            if keyword in query_lower:
                sections = self.keyword_to_section[keyword]
                section_types.extend(sections)
                matched_keywords.append(keyword)

        # Remove duplicates while preserving order
        section_types = list(dict.fromkeys(section_types))

        # If no match, search all sections (fallback)
        if not section_types:
            section_types = ['casing', 'depth', 'borehole', 'trajectory', 'technical_summary']

        return section_types

    def get_section_info(self, section_type: str) -> str:
        """
        Get human-readable description of a section type

        Args:
            section_type: Section type (e.g., 'depth')

        Returns:
            Description string
        """
        return self.section_descriptions.get(section_type, 'Unknown section type')

    def analyze_query(self, query: str) -> Dict:
        """
        Detailed query analysis with matched keywords and sections

        Args:
            query: Natural language query

        Returns:
            Dict with query analysis details

        Example:
            >>> mapper = QueryIntentMapper()
            >>> mapper.analyze_query("What is the casing inner diameter?")
            {
                'query': 'What is the casing inner diameter?',
                'keywords': ['inner diameter', 'casing'],
                'section_types': ['casing'],
                'descriptions': ['Casing and tubing specifications (ID, OD, depth)']
            }
        """
        section_types = self.get_section_types(query)

        # Find matched keywords
        query_lower = query.lower()
        matched = []
        sorted_keywords = sorted(self.keyword_to_section.keys(),
                                 key=len, reverse=True)
        for keyword in sorted_keywords:
            if keyword in query_lower and keyword not in matched:
                matched.append(keyword)

        # Get descriptions
        descriptions = [self.get_section_info(st) for st in section_types]

        return {
            'query': query,
            'keywords': matched,
            'section_types': section_types,
            'descriptions': descriptions,
        }


def main():
    """Test the query intent mapper"""
    mapper = QueryIntentMapper()

    # Test queries (from Sub-Challenge 1 & 2)
    test_queries = [
        "What is the well depth?",
        "What is the measured depth?",
        "What is the casing inner diameter?",
        "What is the well trajectory?",
        "Summarize the well completion",
        "What are the well specifications?",
        "What is the true vertical depth?",
        "What drilling fluid was used?",
    ]

    print("="*80)
    print("QUERY INTENT MAPPER - TEST RESULTS")
    print("="*80)

    for query in test_queries:
        print(f"\nQuery: {query}")
        analysis = mapper.analyze_query(query)
        print(f"  Matched keywords: {', '.join(analysis['keywords'])}")
        print(f"  Target sections: {', '.join(analysis['section_types'])}")


if __name__ == '__main__':
    main()
