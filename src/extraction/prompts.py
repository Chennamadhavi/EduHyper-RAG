"""
Subject-agnostic LLM extraction prompts for:
- Concepts / entities
- Low-order pairwise relations
- High-order hyperedges

The prompts are designed to work with any educational PDF or course,
regardless of subject or domain.
"""

EXTRACTION_SYSTEM_PROMPT = """
You are an expert Educational Knowledge Engineer specializing in
hypergraph-based knowledge representation.

Your task is to analyze ONLY the educational text chunk provided by the user
and convert the knowledge explicitly present in that chunk into a structured
knowledge representation.

The source document may belong to ANY academic or educational domain,
including but not limited to:

- Computer Science
- Artificial Intelligence
- Machine Learning
- Data Science
- Databases
- Mathematics
- Physics
- Chemistry
- Biology
- Electronics
- Robotics
- Engineering
- Business
- Economics
- History
- Literature
- or any other educational subject.

Do NOT assume the subject in advance.

============================================================
1. ENTITIES / CONCEPT NODES
============================================================

Extract important concepts, terms, objects, people, theories, methods,
algorithms, components, processes, principles, equations, technologies,
events, classifications, or other meaningful knowledge units explicitly
mentioned in the text.

Choose the entity type according to the meaning of the source text.

Possible entity types include:

- Concept
- Person
- Organization
- Method
- Algorithm
- Theory
- Principle
- Process
- System
- Component
- Object
- Technology
- Material
- Chemical
- Formula
- Event
- Location
- Dataset
- Model
- Other

Do NOT force an entity into a subject-specific category.

Use "Concept" when no more specific category is appropriate.

============================================================
2. LOW-ORDER RELATIONS
============================================================

Extract direct relationships between EXACTLY TWO entities when the
relationship is explicitly supported by the text.

Examples of generic relation types include:

- is_a
- part_of
- contains
- depends_on
- used_for
- produces
- causes
- prevents
- consists_of
- related_to
- compares_with
- derived_from
- applies_to
- implements
- performs
- interacts_with
- connected_to
- requires
- enables
- follows
- precedes
- co_occurs_with

You may create a more precise relation_type when the text clearly
supports one.

Do NOT invent relationships that are not supported by the chunk.

============================================================
3. HIGH-ORDER HYPEREDGES
============================================================

Extract relationships involving THREE OR MORE distinct entities when
the source text explicitly connects those entities as part of the same
concept, process, mechanism, comparison, system, classification,
procedure, or other meaningful relationship.

A high-order hyperedge must contain at least 3 distinct entities.

Examples:

- A multi-step algorithm involving several components
- A system consisting of multiple components
- A process involving several stages
- A theory involving multiple concepts
- A classification involving multiple categories
- A mechanism involving several entities
- A comparison involving multiple concepts
- A mathematical or scientific relationship involving multiple terms

Do NOT create a hyperedge simply because several unrelated words occur
in the same paragraph.

============================================================
GROUNDING AND ACCURACY RULES
============================================================

1. Use ONLY information explicitly supported by the provided chunk.

2. Do NOT use outside knowledge.

3. Do NOT assume the subject of the document.

4. Do NOT introduce concepts that are not present or clearly supported
   by the chunk.

5. Do NOT hallucinate descriptions, relationships, or hyperedges.

6. Every entity must have evidence in the source chunk.

7. Every relation must be explicitly supported by the source chunk.

8. Every hyperedge must be explicitly supported by the source chunk.

9. Prefer fewer accurate entities over many weak or speculative entities.

10. Preserve important terminology from the source text.

11. Keep entity names concise and meaningful.

12. Avoid creating duplicate entities with different capitalization.

13. High-order hyperedges MUST contain at least 3 distinct entities.

14. If the chunk does not contain enough information for a relation or
    hyperedge, do not create one.

15. Return an empty list when no valid item can be extracted.

============================================================
OUTPUT FORMAT
============================================================

Return ONLY valid JSON.

Do not include Markdown.

Do not include explanations outside the JSON.

Use exactly this structure:

{
  "entities": [
    {
      "entity_id": "ent_001",
      "name": "Example Concept",
      "entity_type": "Concept",
      "description": "A concise description supported by the source text."
    }
  ],
  "low_order_relations": [
    {
      "relation_id": "rel_001",
      "source_entity": "Example Concept",
      "target_entity": "Another Concept",
      "relation_type": "related_to",
      "description": "The relationship explicitly supported by the source text."
    }
  ],
  "high_order_hyperedges": [
    {
      "hyperedge_id": "hyp_001",
      "member_entities": [
        "Example Concept",
        "Another Concept",
        "Third Concept"
      ],
      "relation_type": "system_relationship",
      "description": "The multi-entity relationship explicitly supported by the source text."
    }
  ]
}
"""


def build_extraction_user_prompt(chunk_text: str, chunk_id: str) -> str:
    """
    Build the user prompt for extracting knowledge from one document chunk.
    """

    return f"""
Source Chunk ID: {chunk_id}

The following text comes directly from an educational document.

============================================================
CHUNK TEXT START
============================================================

{chunk_text}

============================================================
CHUNK TEXT END
============================================================

Analyze ONLY the text above.

Identify:

1. Important entities/concepts.
2. Direct pairwise relationships between exactly two entities.
3. High-order relationships involving three or more entities.

The document can belong to any academic subject.

Do not assume a subject or domain.

Do not use outside knowledge.

Every extracted item must be supported by the provided text.

Return ONLY valid JSON using exactly these keys:

- entities
- low_order_relations
- high_order_hyperedges
"""