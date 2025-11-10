"""
Build Ground Truth Dataset for RAG Evaluation

This script helps manually create ground truth answers by:
1. Loading test questions
2. Querying the RAG system
3. Displaying answers for human validation
4. Saving validated answers as ground truth
"""

import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from rag_system import WellReportRAG


def load_test_questions():
    """Load test questions from JSON"""
    questions_file = Path(__file__).parent / 'test_questions.json'
    with open(questions_file, 'r') as f:
        return json.load(f)


def save_ground_truth(ground_truth):
    """Save ground truth to JSON"""
    output_file = Path(__file__).parent / 'ground_truth.json'
    with open(output_file, 'w') as f:
        json.dump(ground_truth, f, indent=2)
    print(f"\nGround truth saved to {output_file}")


def build_ground_truth_interactive():
    """Interactive ground truth builder"""

    print("="*80)
    print("GROUND TRUTH BUILDER")
    print("="*80)
    print("\nThis will query the RAG system and ask you to validate answers.")
    print("You can:")
    print("  - Press ENTER to accept the answer")
    print("  - Type 'edit' to modify the answer")
    print("  - Type 'skip' to skip this question")
    print("  - Type 'quit' to save and exit")
    print("="*80)

    # Load test questions
    test_data = load_test_questions()

    # Initialize RAG system
    print("\nInitializing RAG system...")
    rag = WellReportRAG()
    print("RAG system ready!\n")

    # Ground truth storage
    ground_truth = {
        "metadata": {
            "created": "2025-11-08",
            "method": "manual_validation",
            "total_questions": 0,
            "validated": 0
        },
        "answers": {}
    }

    question_count = 0
    validated_count = 0

    # Process each category
    for category_name, category_data in test_data['categories'].items():
        print(f"\n{'='*80}")
        print(f"CATEGORY: {category_name.upper()}")
        print(f"Description: {category_data['description']}")
        print(f"Expected Accuracy: {category_data['expected_accuracy']}")
        print(f"{'='*80}\n")

        for question_item in category_data['questions']:
            question_count += 1
            q_id = question_item['id']
            question = question_item['question']
            well = question_item.get('well')
            expected_info = question_item['expected_info']

            print(f"\n[{question_count}] {q_id}: {question}")
            if well:
                print(f"    Well: {well}")
            print(f"    Expected info: {', '.join(expected_info)}")

            # Query RAG system
            print("\n    Querying RAG system...")
            try:
                result = rag.query(question, well_name=well, n_results=5)
                answer = result['answer']
                sources = result.get('sources', [])

                print(f"\n    RAG ANSWER:")
                print(f"    {'-'*70}")
                print(f"    {answer}")
                print(f"    {'-'*70}")
                print(f"    Sources: {len(sources)} chunks retrieved")

                # Show sources
                if sources:
                    print(f"\n    Top sources:")
                    for i, source in enumerate(sources[:3], 1):
                        section = source.get('section_title', 'Unknown')
                        page = source.get('page', 'Unknown')
                        print(f"      {i}. Section: {section}, Page: {page}")

            except Exception as e:
                print(f"\n    ERROR querying RAG: {e}")
                answer = f"ERROR: {e}"

            # Validate answer
            while True:
                user_input = input("\n    [ENTER=accept, edit, skip, quit]: ").strip().lower()

                if user_input == '':
                    # Accept answer as-is
                    ground_truth['answers'][q_id] = {
                        "question": question,
                        "well": well,
                        "category": category_name,
                        "answer": answer,
                        "expected_info": expected_info,
                        "sources": [
                            {
                                "section": s.get('section_title', ''),
                                "page": s.get('page', '')
                            } for s in sources[:3]
                        ] if sources else [],
                        "validated": True,
                        "modified": False
                    }
                    validated_count += 1
                    print(f"    ✓ Answer accepted\n")
                    break

                elif user_input == 'edit':
                    print("\n    Enter the correct answer (or press ENTER to cancel):")
                    new_answer = input("    > ").strip()
                    if new_answer:
                        ground_truth['answers'][q_id] = {
                            "question": question,
                            "well": well,
                            "category": category_name,
                            "answer": new_answer,
                            "expected_info": expected_info,
                            "original_rag_answer": answer,
                            "sources": [],
                            "validated": True,
                            "modified": True
                        }
                        validated_count += 1
                        print(f"    ✓ Modified answer saved\n")
                        break
                    else:
                        print("    Cancelled, try again")

                elif user_input == 'skip':
                    ground_truth['answers'][q_id] = {
                        "question": question,
                        "well": well,
                        "category": category_name,
                        "answer": answer,
                        "expected_info": expected_info,
                        "validated": False,
                        "skipped": True
                    }
                    print(f"    ⊘ Skipped\n")
                    break

                elif user_input == 'quit':
                    print("\n    Saving and quitting...")
                    ground_truth['metadata']['total_questions'] = question_count
                    ground_truth['metadata']['validated'] = validated_count
                    save_ground_truth(ground_truth)
                    return

                else:
                    print("    Invalid input. Use: ENTER, edit, skip, or quit")

    # Save final ground truth
    ground_truth['metadata']['total_questions'] = question_count
    ground_truth['metadata']['validated'] = validated_count
    save_ground_truth(ground_truth)

    print(f"\n{'='*80}")
    print(f"GROUND TRUTH BUILDING COMPLETE")
    print(f"{'='*80}")
    print(f"Total questions: {question_count}")
    print(f"Validated: {validated_count}")
    print(f"Coverage: {100*validated_count/question_count:.1f}%")
    print(f"{'='*80}\n")


def build_ground_truth_from_docs():
    """Alternative: Build ground truth by manually reading docs"""

    print("\n" + "="*80)
    print("MANUAL GROUND TRUTH TEMPLATE")
    print("="*80)
    print("\nThis creates a template for manually entering answers from PDFs.")
    print("You'll need to read the PDFs and fill in the correct answers.\n")

    test_data = load_test_questions()

    ground_truth = {
        "metadata": {
            "created": "2025-11-08",
            "method": "manual_from_documents",
            "total_questions": 0,
            "instructions": "Fill in the 'answer' field for each question by reading the PDF"
        },
        "answers": {}
    }

    question_count = 0

    for category_name, category_data in test_data['categories'].items():
        for question_item in category_data['questions']:
            question_count += 1
            q_id = question_item['id']

            ground_truth['answers'][q_id] = {
                "question": question_item['question'],
                "well": question_item.get('well'),
                "category": category_name,
                "expected_info": question_item['expected_info'],
                "answer": "TODO: Fill in from PDF",
                "source_page": "TODO: Page number",
                "source_section": "TODO: Section name",
                "confidence": "high/medium/low",
                "notes": ""
            }

    ground_truth['metadata']['total_questions'] = question_count

    # Save template
    template_file = Path(__file__).parent / 'ground_truth_template.json'
    with open(template_file, 'w') as f:
        json.dump(ground_truth, f, indent=2)

    print(f"Template saved to {template_file}")
    print(f"Total questions: {question_count}")
    print(f"\nNext steps:")
    print(f"1. Open {template_file}")
    print(f"2. For each question, read the PDF and fill in the answer")
    print(f"3. Rename to ground_truth.json when done")
    print("="*80 + "\n")


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Build ground truth dataset')
    parser.add_argument('--mode', choices=['interactive', 'template'], default='interactive',
                       help='Interactive: query RAG and validate, Template: create manual template')

    args = parser.parse_args()

    if args.mode == 'interactive':
        build_ground_truth_interactive()
    else:
        build_ground_truth_from_docs()
