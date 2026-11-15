"""
Standardized Educational Benchmark Dataset for EduHyperRAG Evaluation.
Contains 10 curated questions across difficulty levels (Easy, Medium, Hard/Multi-hop),
with reference ground truth answers and ground truth source chunk IDs.
"""

from typing import Any, Dict, List
from pydantic import BaseModel, Field


class EvaluationQuestion(BaseModel):
    """Schema for a single benchmark evaluation item."""
    question_id: str
    question: str
    category: str
    difficulty: str  # 'Easy', 'Medium', 'Hard'
    reference_answer: str
    ground_truth_chunk_ids: List[str]
    ground_truth_concepts: List[str]


BENCHMARK_DATASET: List[EvaluationQuestion] = [
    EvaluationQuestion(
        question_id="Q01",
        question="What is the overall chemical equation summarizing oxygenic photosynthesis?",
        category="Factual Recall",
        difficulty="Easy",
        reference_answer="The overall equation for oxygenic photosynthesis is 6 CO2 + 6 H2O + Light Energy --> C6H12O6 + 6 O2.",
        ground_truth_chunk_ids=["photosynthesis_chapter_semantic_0000"],
        ground_truth_concepts=["Photosynthesis"],
    ),
    EvaluationQuestion(
        question_id="Q02",
        question="Where are Photosystem II and Photosystem I localized within the chloroplast?",
        category="Structural Localization",
        difficulty="Medium",
        reference_answer="Photosystem II (PSII) is predominantly localized in the appressed regions of grana thylakoids, whereas Photosystem I (PSI) is localized in non-appressed regions (stroma lamellae and outer grana margins) exposed to the stroma.",
        ground_truth_chunk_ids=["photosynthesis_chapter_semantic_0000"],
        ground_truth_concepts=["Photosystem II", "Photosystem I", "Chloroplast", "Stroma"],
    ),
    EvaluationQuestion(
        question_id="Q03",
        question="What absorption peaks characterize Chlorophyll a and Chlorophyll b?",
        category="Pigment Spectroscopy",
        difficulty="Easy",
        reference_answer="Chlorophyll a has maximum absorption peaks in the blue (~430 nm) and red (~660 nm) regions. Chlorophyll b absorbs blue-green (~450 nm) and red-orange (~640 nm) light.",
        ground_truth_chunk_ids=["photosynthesis_chapter_semantic_0001"],
        ground_truth_concepts=["Chlorophyll a", "Chlorophyll b"],
    ),
    EvaluationQuestion(
        question_id="Q04",
        question="How does water photolysis work in Photosystem II to produce oxygen?",
        category="Mechanism",
        difficulty="Medium",
        reference_answer="Photosystem II reaction center P680 loses an electron upon photon absorption. P680+ extracts e- from water via the Oxygen-Evolving Complex (Mn4CaO5 cluster), splitting water: 2 H2O -> 4 H+ + 4 e- + O2.",
        ground_truth_chunk_ids=["photosynthesis_chapter_semantic_0001"],
        ground_truth_concepts=["Photosystem II", "P680", "Oxygen-Evolving Complex", "Water Photolysis"],
    ),
    EvaluationQuestion(
        question_id="Q05",
        question="How does electron flow connect Plastoquinone, Cytochrome b6f, and Plastocyanin?",
        category="Electron Transport Pathway",
        difficulty="Hard",
        reference_answer="Pheophytin transfers electrons to plastoquinone (PQ), which shuttles them to Cytochrome b6f while pumping protons into the thylakoid lumen. Cytochrome b6f then reduces plastocyanin (PC), which delivers electrons to PSI P700.",
        ground_truth_chunk_ids=["photosynthesis_chapter_semantic_0002"],
        ground_truth_concepts=["Plastoquinone", "Cytochrome b6f", "Plastocyanin", "Photosystem I"],
    ),
    EvaluationQuestion(
        question_id="Q06",
        question="What is the difference between Non-Cyclic and Cyclic Photophosphorylation?",
        category="Pathway Comparison",
        difficulty="Medium",
        reference_answer="Non-cyclic photophosphorylation involves both PSII and PSI, producing ATP, NADPH, and O2. Cyclic photophosphorylation involves PSI only, recycling electrons through PQ and Cytochrome b6f to produce ATP without NADPH or O2 release.",
        ground_truth_chunk_ids=["photosynthesis_chapter_semantic_0003"],
        ground_truth_concepts=["Photosystem II", "Photosystem I", "Plastoquinone", "Ferredoxin"],
    ),
    EvaluationQuestion(
        question_id="Q07",
        question="What enzyme catalyzes initial carbon fixation in the Calvin Cycle and what product is formed?",
        category="Enzymatic Catalysis",
        difficulty="Easy",
        reference_answer="Rubisco (Ribulose-1,5-bisphosphate carboxylase-oxygenase) combines CO2 with RuBP (5-carbon) to yield two molecules of 3-phosphoglycerate (3-PGA).",
        ground_truth_chunk_ids=["photosynthesis_chapter_semantic_0003"],
        ground_truth_concepts=["Calvin Cycle", "Rubisco", "RuBP", "3-PGA"],
    ),
    EvaluationQuestion(
        question_id="Q08",
        question="How do C4 plants suppress photorespiration through spatial separation?",
        category="Comparative Adaptation",
        difficulty="Hard",
        reference_answer="C4 plants use Kranz anatomy. In mesophyll cells, CO2 is fixed by PEP carboxylase into OAA/malate (no oxygenase activity). Malate is transported to bundle sheath cells and decarboxylated, releasing CO2 at high concentration directly around Rubisco.",
        ground_truth_chunk_ids=["photosynthesis_chapter_semantic_0004"],
        ground_truth_concepts=["C4 Pathway", "PEP Carboxylase", "Rubisco", "Stroma"],
    ),
    EvaluationQuestion(
        question_id="Q09",
        question="How do CAM plants achieve temporal separation of carbon fixation?",
        category="Ecological Physiology",
        difficulty="Medium",
        reference_answer="CAM plants open stomata at night to absorb CO2, fixing it via PEP carboxylase into malic acid stored in vacuoles. During daytime, stomata close to prevent water loss, and stored malic acid is decarboxylated in the stroma to feed Rubisco.",
        ground_truth_chunk_ids=["photosynthesis_chapter_semantic_0005"],
        ground_truth_concepts=["CAM Pathway", "PEP Carboxylase", "Rubisco"],
    ),
    EvaluationQuestion(
        question_id="Q10",
        question="According to Blackman's Law of Limiting Factors, how does CO2 concentration affect photosynthesis?",
        category="Limiting Factors",
        difficulty="Medium",
        reference_answer="Under Blackman's Law, photosynthetic rate is limited by the factor present at the slowest rate. CO2 is often the major limiting factor (~400 ppm). Increasing CO2 concentration boosts C3 photosynthetic rate up to saturation around 500 ppm.",
        ground_truth_chunk_ids=["photosynthesis_chapter_semantic_0005"],
        ground_truth_concepts=["Rubisco", "Calvin Cycle"],
    ),
]


def load_benchmark_dataset() -> List[EvaluationQuestion]:
    """Returns the benchmark evaluation dataset."""
    return BENCHMARK_DATASET
