import base64
import re
from typing import Literal
from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph import (
    StateGraph,
    START,
    END,
)
from interview_ai.statee import InterviewState
from interview_ai.prompts import (
    FIRST_QUESTION_PROMPT,
    NEXT_QUESTION_PROMPT,
)
from speech.stt import SpeechToText
from speech.tts import TextToSpeech
###  FALLBACK NEXT-QUESTION PROMPT   ###
FALLBACK_NEXT_QUESTION_PROMPT = """
You are a professional technical interviewer.

Role:
{role}

Difficulty:
{difficulty}

Previous Questions:
{previous_questions}

Candidate's Latest Answer:
{transcript}

Generate ONE next interview question.

Rules:
- Ask exactly ONE question.
- Do not provide the answer.
- Do not evaluate the candidate.
- Do not use XML.
- Do not use JSON.
- Do not add explanations.
- Do not repeat a previous question.
- Keep it relevant to the role.
- Match the difficulty.
- Return ONLY the question text.
"""
class AIInterviewGraph:
    MAX_QUESTIONS = 5
    def __init__(
        self,
        llm,
    ):
        self.llm = llm
        ###  PROMPTS   ###
        self.first_question_prompt = (
            ChatPromptTemplate.from_template(
                FIRST_QUESTION_PROMPT
            )
        )
        self.next_question_prompt = (
            ChatPromptTemplate.from_template(
                NEXT_QUESTION_PROMPT
            )
        )
        self.fallback_question_prompt = (
            ChatPromptTemplate.from_template(
                FALLBACK_NEXT_QUESTION_PROMPT
            )
        )
        ###  SPEECH SERVICES   ###
        self.stt = SpeechToText(
            model_size="base",
            device="cpu",
            compute_type="int8",
        )
        self.tts = TextToSpeech(
            voice="en-US-AriaNeural",
        )
        ###  BUILD GRAPH   ###
        self.graph = self._build_graph()
    ###  BUILD LANGGRAPH   ###
    def _build_graph(self):
        builder = StateGraph(
            InterviewState
        )
        builder.add_node(
            "route_action",
            self.route_action,
        )
        builder.add_node(
            "first_question",
            self.first_question,
        )
        builder.add_node(
            "transcribe",
            self.transcribe,
        )
        builder.add_node(
            "evaluate",
            self.evaluate,
        )
        builder.add_node(
            "check_completion",
            self.check_completion,
        )
        builder.add_node(
            "advance_question",
            self.advance_question,
        )
        builder.add_node(
            "final_evaluation",
            self.final_evaluation,
        )
        builder.add_node(
            "speak_question",
            self.speak_question,
        )
        ###  START   ###
        builder.add_edge(
            START,
            "route_action",
        )
        ###  INITIAL ROUTING   ###
        builder.add_conditional_edges(
            "route_action",
            self.route_after_action,
            {
                "start": "first_question",
                "answer": "transcribe",
                "final": "final_evaluation",
                "end": END,
            },
        )
        ###  FIRST QUESTION   ###
        builder.add_edge(
            "first_question",
            "speak_question",
        )
        ###  ANSWER FLOW   ###
        builder.add_edge(
            "transcribe",
            "evaluate",
        )
        builder.add_edge(
            "evaluate",
            "check_completion",
        )
        ###  COMPLETION   ###
        builder.add_conditional_edges(
            "check_completion",
            self.route_after_completion,
            {
                "next": "advance_question",
                "final": "final_evaluation",
            },
        )
        ###  NEXT QUESTION   ###
        builder.add_edge(
            "advance_question",
            "speak_question",
        )
        ###  FINAL  ###
        builder.add_edge(
            "final_evaluation",
            END,
        )
        ###  SPEAK  ###
        builder.add_edge(
            "speak_question",
            END,
        )
        return builder.compile()
    ###  ROUTE ACTION   ###
    def route_action(
        self,
        state: InterviewState,
    ):
        return {
            "action": state.get(
                "action",
                "end",
            )
        }
    ###   ACTION ROUTING   ###
    @staticmethod
    def route_after_action(
        state: InterviewState,
    ) -> Literal[
        "start",
        "answer",
        "final",
        "end",
    ]:
        action = state.get(
            "action",
            "end",
        )
        if action == "start":
            return "start"
        if action == "answer":
            return "answer"
        if action == "final":
            return "final"
        return "end"
    ### FIRST QUESTION   ###
    def first_question(
        self,
        state: InterviewState,
    ):
        response = self.llm.invoke(
            self.first_question_prompt.format_messages(
                role=state["role"],
                difficulty=state["difficulty"],
            )
        )
        question = self._extract_text(
            response
        )
        question = self._clean_question(
            question
        )
        if not question:
            raise ValueError(
                "LLM returned an empty first question."
            )
        return {
            "question_number": 1,
            "max_questions": self.MAX_QUESTIONS,
            "completed_questions": 0,
            "current_question": question,
            "previous_questions": [
                question
            ],
            "conversation": [],
            "status": "running",
        }
    ###   STT   ###
    def transcribe(
        self,
        state: InterviewState,
    ):
        transcript = self.stt.transcribe(
            audio_bytes=state["audio_bytes"],
            language="en",
        )
        if not transcript.strip():
            raise ValueError(
                "Could not understand the answer."
            )
        return {
            "transcript": transcript.strip()
        }
    ###  EVALUATION   ###
    def evaluate(
        self,
        state: InterviewState,
    ):
        previous_questions = state.get(
            "previous_questions",
            [],
        )
        conversation = state.get(
            "conversation",
            [],
        )
        ###  MAIN EVALUATION CALL   ###
        response = self.llm.invoke(
            self.next_question_prompt.format_messages(
                role=state["role"],
                difficulty=state["difficulty"],
                question_number=(
                    state["question_number"]
                ),
                previous_questions=(
                    "\n".join(
                        previous_questions
                    )
                    if previous_questions
                    else "None"
                ),
                conversation=(
                    "\n".join(
                        conversation
                    )
                    if conversation
                    else "None"
                ),
                transcript=state["transcript"],
            )
        )
        raw_text = self._extract_text(
            response
        )
        ###  PARSE   ###
        evaluation, next_question = (
            self._parse_evaluation_response(
                raw_text
            )
        )
        ###  FALLBACK   ###
        if not next_question:
            next_question = (
                self._generate_fallback_question(
                    role=state["role"],
                    difficulty=state["difficulty"],
                    previous_questions=previous_questions,
                    transcript=state["transcript"],
                )
            )
        if not next_question:
            raise ValueError(
                "Could not generate next question."
            )
        ###  SCORE   ###
        score = self._extract_score(
            evaluation
        )
        ###  CONVERSATION   ###
        current_question = (
            state["current_question"]
        )
        transcript = (
            state["transcript"]
        )
        new_conversation = (
            conversation
            + [
                f"Interviewer: {current_question}",
                f"Candidate: {transcript}",
                f"Evaluation: {evaluation}",
            ]
        )
        completed_questions = (
            state.get(
                "completed_questions",
                0,
            )
            + 1
        )
        return {
            "evaluation": evaluation,
            "score": score,
            "transcript": transcript,
            "completed_questions": completed_questions,
            "conversation": new_conversation,
            "next_question": next_question,
        }
    ###   FALLBACK QUESTION GENERATOR   ###
    def _generate_fallback_question(
        self,
        role: str,
        difficulty: str,
        previous_questions,
        transcript: str,
    ) -> str:
        response = self.llm.invoke(
            self.fallback_question_prompt.format_messages(
                role=role,
                difficulty=difficulty,
                previous_questions=(
                    "\n".join(
                        previous_questions
                    )
                    if previous_questions
                    else "None"
                ),
                transcript=transcript,
            )
        )
        question = self._extract_text(
            response
        )
        return self._clean_question(
            question
        )
    ###  CHECK COMPLETION   ###
    def check_completion(
        self,
        state: InterviewState,
    ):
        completed = state.get(
            "completed_questions",
            0,
        )
        if completed >= self.MAX_QUESTIONS:
            return {
                "status": "completed"
            }
        return {
            "status": "running"
        }
    ###  COMPLETION ROUTING   ###
    @staticmethod
    def route_after_completion(
        state: InterviewState,
    ) -> Literal[
        "next",
        "final",
    ]:
        completed = state.get(
            "completed_questions",
            0,
        )
        if (
            completed
            >= AIInterviewGraph.MAX_QUESTIONS
        ):
            return "final"
        return "next"
    ###   NEXT QUESTION / ADVANCE QUESTION    ###
    def advance_question(
        self,
        state: InterviewState,
    ):
        next_question = state.get(
            "next_question",
            "",
        )
        if not next_question:
            raise ValueError(
                "Next question is empty."
            )
        next_question = (
            self._clean_question(
                next_question
            )
        )
        previous_questions = (
            state.get(
                "previous_questions",
                [],
            )
        )
        return {
            "question_number": (
                state["completed_questions"]
                + 1
            ),
            "current_question": next_question,
            "previous_questions": (
                previous_questions
                + [next_question]
            ),
            "next_question": "",
            "status": "running",
        }

    def next_question(
        self,
        state: InterviewState,
    ):
        return self.advance_question(state)
    ###  FINAL EVALUATION   ###
    def final_evaluation(
        self,
        state: InterviewState,
    ):
        completed = state.get(
            "completed_questions",
            0,
        )
        conversation = state.get(
            "conversation",
            [],
        )
        evaluations = []
        for item in conversation:
            if item.startswith(
                "Evaluation:"
            ):
                evaluations.append(
                    item.replace(
                        "Evaluation:",
                        "",
                        1,
                    ).strip()
                )

        # Handle early quit with zero completed questions
        if completed == 0 or not evaluations:
            return {
                "final_report": (
                    "### ℹ️ Interview Ended Early\n\n"
                    "No interview questions were answered during this session. "
                    "Start a new interview session and answer at least one question "
                    "to generate a detailed technical evaluation report!"
                ),
                "final_average_score": 0.0,
                "status": "completed",
            }

        from interview_ai.prompts import (
            FINAL_EVALUATION_PROMPT,
        )
        final_prompt = (
            ChatPromptTemplate.from_template(
                FINAL_EVALUATION_PROMPT
            )
        )
        response = self.llm.invoke(
            final_prompt.format_messages(
                role=state["role"],
                difficulty=state["difficulty"],
                completed_questions=completed,
                conversation="\n".join(
                    conversation
                ),
                evaluations="\n".join(
                    evaluations
                ),
            )
        )
        report = self._extract_text(
            response
        )
        report = self._clean_final_report(
            report
        )
        scores = []
        for evaluation in evaluations:
            score = self._extract_score(
                evaluation
            )
            if score > 0:
                scores.append(score)
        if scores:
            average_score = round(
                sum(scores) / len(scores),
                1,
            )
        else:
            average_score = 0.0
        return {
            "final_report": report,
            "final_average_score": average_score,
            "status": "completed",
        }
    ###  TTS   ###
    def speak_question(
        self,
        state: InterviewState,
    ):
        question = state.get(
            "current_question",
            "",
        )
        if not question:
            return {
                "audio_base64": ""
            }
        try:
            audio = self.tts.generate(
                question
            )
            audio_base64 = (
                base64.b64encode(
                    audio
                ).decode(
                    "utf-8"
                )
            )
        except Exception:
            audio_base64 = ""

        return {
            "audio_base64": audio_base64
        }
    ###  START   ###
    def start(
        self,
        role: str,
        difficulty: str,
        interview_id: str,
    ):
        state: InterviewState = {
            "interview_id": interview_id,
            "role": role,
            "difficulty": difficulty,
            "action": "start",
            "question_number": 0,
            "max_questions": self.MAX_QUESTIONS,
            "completed_questions": 0,
            "status": "starting",
            "previous_questions": [],
            "conversation": [],
        }
        return self.graph.invoke(
            state
        )
    ###   ANSWER   ###
    def answer(
        self,
        interview_id: str,
        role: str,
        difficulty: str,
        question_number: int,
        current_question: str,
        previous_questions,
        conversation,
        completed_questions,
        audio_bytes: bytes,
    ):
        state: InterviewState = {
            "interview_id": interview_id,
            "role": role,
            "difficulty": difficulty,
            "action": "answer",
            "question_number": question_number,
            "max_questions": self.MAX_QUESTIONS,
            "completed_questions": completed_questions,
            "current_question": current_question,
            "previous_questions": previous_questions,
            "conversation": conversation,
            "audio_bytes": audio_bytes,
            "status": "running",
        }
        return self.graph.invoke(
            state
        )
    ###   FINALIZE   ###
    def finalize(
        self,
        interview_id: str,
        role: str,
        difficulty: str,
        question_number: int,
        previous_questions,
        conversation,
        completed_questions,
    ):
        state: InterviewState = {
            "interview_id": interview_id,
            "role": role,
            "difficulty": difficulty,
            "action": "final",
            "question_number": question_number,
            "max_questions": self.MAX_QUESTIONS,
            "completed_questions": completed_questions,
            "previous_questions": previous_questions,
            "conversation": conversation,
            "status": "stopping",
        }
        return self.graph.invoke(
            state
        )
    ###  TEXT EXTRACTION   ###
    @staticmethod
    def _extract_text(
        response,
    ) -> str:
        content = getattr(
            response,
            "content",
            response,
        )
        if isinstance(
            content,
            list,
        ):
            parts = []
            for item in content:
                if isinstance(
                    item,
                    dict,
                ):
                    text = item.get(
                        "text"
                    )
                    if text:
                        parts.append(
                            str(text)
                        )
                else:
                    parts.append(
                        str(item)
                    )
            return "\n".join(
                parts
            ).strip()
        return str(
            content
        ).strip()
    ###  RESPONSE PARSER   ###
    @staticmethod
    def _parse_evaluation_response(
        text: str,
    ):
        text = text.strip()
        ###  XML FORMAT   ###
        evaluation_match = re.search(
            r"<evaluation>\s*(.*?)\s*</evaluation>",
            text,
            flags=(
                re.IGNORECASE
                | re.DOTALL
            ),
        )
        question_match = re.search(
            r"<next_question>\s*(.*?)\s*</next_question>",
            text,
            flags=(
                re.IGNORECASE
                | re.DOTALL
            ),
        )
        evaluation = (
            evaluation_match.group(1).strip()
            if evaluation_match
            else ""
        )
        next_question = (
            question_match.group(1).strip()
            if question_match
            else ""
        )
        ###  LABEL FORMAT   ###
        if not next_question:
            label_match = re.search(
                r"NEXT[_ ]?QUESTION\s*:\s*(.*)$",
                text,
                flags=(
                    re.IGNORECASE
                    | re.DOTALL
                ),
            )
            if label_match:
                next_question = (
                    label_match.group(1).strip()
                )
        ###  QUESTION MARK FALLBACK    ###
        if not next_question:
            sentences = re.split(
                r"(?<=[?])\s+",
                text,
            )
            possible_questions = [
                item.strip()
                for item in sentences
                if "?" in item
            ]
            if possible_questions:
                next_question = (
                    possible_questions[-1]
                )
        return (
            evaluation,
            next_question,
        )
    ###   CLEAN QUESTION   ###
    @staticmethod
    def _clean_question(
        question: str,
    ) -> str:
        question = question.strip()
        question = re.sub(
            r"<next_question>|</next_question>",
            "",
            question,
            flags=re.IGNORECASE,
        )
        question = re.sub(
            r"^NEXT[_ ]?QUESTION\s*:\s*",
            "",
            question,
            flags=re.IGNORECASE,
        )
        question = re.sub(
            r"^Question\s*\d*\s*:\s*",
            "",
            question,
            flags=re.IGNORECASE,
        )
        return question.strip()
    ###  SCORE   ###
    @staticmethod
    def _extract_score(
        text: str,
    ) -> float:
        if not text:
            return 0.0
        patterns = [
            r"score\s*[:\-]?\s*(\d+(?:\.\d+)?)",
            r"(\d+(?:\.\d+)?)\s*/\s*10",
        ]
        for pattern in patterns:
            match = re.search(
                pattern,
                text,
                flags=re.IGNORECASE,
            )
            if match:
                try:
                    score = float(
                        match.group(1)
                    )
                    return max(
                        0.0,
                        min(
                            10.0,
                            score,
                        ),
                    )
                except ValueError:
                    pass
        return 0.0
    ###   CLEAN FINAL REPORT   ###
    @staticmethod
    def _clean_final_report(
        report: str,
    ) -> str:
        report = re.sub(
            r"<final_report>",
            "",
            report,
            flags=re.IGNORECASE,
        )
        report = re.sub(
            r"</final_report>",
            "",
            report,
            flags=re.IGNORECASE,
        )
        return report.strip()