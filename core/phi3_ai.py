"""
Intégration du modèle OpenAI (chat completions) pour SmartEtude
Client HTTP vers l'API OpenAI à la place d'un modèle local ou OpenQI
"""
from typing import Dict, Any, List
import logging
import requests
from django.conf import settings

logger = logging.getLogger(__name__)


class Phi3AI:
    """Client OpenAI compatible avec l'ancienne interface Phi-3"""

    def __init__(self, model_name: str | None = None):
        # Nom du modèle OpenAI
        self.model_name = model_name or getattr(settings, "AI_MODEL", "gpt-4o-mini")
        # Endpoint et clé API
        self.base_url = getattr(settings, "OPENAI_BASE_URL", "https://api.openai.com")
        self.api_key = getattr(settings, "OPENAI_API_KEY", "")

        # Paramètres de génération
        self.max_tokens = getattr(settings, "AI_MAX_TOKENS", 800)
        self.temperature = getattr(settings, "AI_TEMPERATURE", 0.7)

        # Compat pour les vues existantes
        self.is_loaded = True
        self.device = "remote"
        self.last_error_message: str | None = None

        if not self.api_key:
            logger.warning("OPENAI_API_KEY manquant. Configurez-le dans vos variables d'environnement.")

    # Ancienne API appelait load_model; ici, rien à charger
    def load_model(self) -> bool:
        return True

    def generate_summary(self, text: str, level: str = "intermediate", language: str = "french") -> Dict[str, Any]:
        try:
            system_prompt = self._get_system_prompt("summary", level, language)
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Résume ce texte de manière {level} en {language}:\n\n{text[:16000]}"},
            ]
            result = self._chat_completion(messages)
            return {
                "success": True,
                "summary": result,
                "model": self.model_name,
                "level": level,
                "language": language,
            }
        except Exception as e:
            logger.error(f"Erreur génération résumé: {e}")
            return {"success": False, "error": str(e)}

    def generate_quiz(self, text: str, num_questions: int = 5, difficulty: str = "medium", language: str = "french") -> Dict[str, Any]:
        try:
            system_prompt = self._get_system_prompt("quiz", difficulty, language)
            messages = [
                {"role": "system", "content": system_prompt + """

FORMAT STRICT REQUIS:
Génère un mélange de questions QCM et Vrai/Faux. Pour chaque question, utilise EXACTEMENT ce format:

POUR LES QUESTIONS QCM:
1. [Texte de la question uniquement, sans options ni réponses]

A) [Option A]
B) [Option B] 
C) [Option C]
D) [Option D]

Réponse correcte: [A/B/C/D]

POUR LES QUESTIONS VRAI/FAUX:
2. [Texte de la question uniquement, sans options ni réponses]

Vrai
Faux

Réponse correcte: [Vrai/Faux]

IMPORTANT: 
- Mélange environ 60% de QCM et 40% de Vrai/Faux
- Ne mélange JAMAIS la question avec les options ou la réponse
- Chaque question doit être sur une ligne séparée
- Les options doivent être clairement séparées
- La réponse correcte doit être sur une ligne séparée
- Pas d'explications dans le texte de la question
- Pour Vrai/Faux, utilise simplement "Vrai" et "Faux" comme options
"""},
                {"role": "user", "content": f"Crée {num_questions} questions de niveau {difficulty} en {language} basées sur ce texte:\n\n{text[:20000]}"},
            ]
            result = self._chat_completion(messages)
            return {
                "success": True,
                "quiz_text": result,
                "model": self.model_name,
                "num_questions": num_questions,
                "difficulty": difficulty,
                "language": language,
            }
        except Exception as e:
            logger.error(f"Erreur génération quiz: {e}")
            return {"success": False, "error": str(e)}

    def chat_with_course(self, course_text: str, question: str, language: str = "french") -> Dict[str, Any]:
        try:
            system_prompt = self._get_system_prompt("chat", "intermediate", language)
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Contexte du cours:\n{course_text[:18000]}\n\nQuestion: {question}"},
            ]
            result = self._chat_completion(messages)
            return {
                "success": True,
                "answer": result,
                "model": self.model_name,
                "language": language,
            }
        except Exception as e:
            logger.error(f"Erreur chat: {e}")
            return {"success": False, "error": str(e)}

    def _get_system_prompt(self, task: str, level: str, language: str) -> str:
        prompts = {
            "summary": {
                "french": f"Tu es un assistant IA spécialisé dans la création de résumés éducatifs. Crée des résumés clairs, structurés et adaptés au niveau {level}. Utilise des émojis et une mise en forme claire.",
                "english": f"You are an AI assistant specialized in creating educational summaries. Create clear, structured summaries adapted to {level} level. Use emojis and clear formatting.",
            },
            "quiz": {
                "french": f"Tu es un assistant IA spécialisé dans la création de quiz éducatifs. Crée des questions de niveau {level} avec des réponses claires et des explications.",
                "english": f"You are an AI assistant specialized in creating educational quizzes. Create {level} level questions with clear answers and explanations.",
            },
            "chat": {
                "french": f"Tu es un assistant IA éducatif. Réponds aux questions des étudiants en te basant sur le contenu du cours fourni. Sois précis, pédagogique et adapté au niveau {level}.",
                "english": f"You are an educational AI assistant. Answer student questions based on the provided course content. Be precise, pedagogical and adapted to {level} level.",
            },
        }
        return prompts.get(task, {}).get(language, prompts[task]["french"])

    def _chat_completion(self, messages: List[Dict[str, str]]) -> str:
        """Appelle l'API OpenAI Chat Completions et retourne le texte"""
        if not self.api_key:
            raise RuntimeError("OPENAI_API_KEY n'est pas configuré.")

        url = f"{self.base_url.rstrip('/')}/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload: Dict[str, Any] = {
            "model": self.model_name,
            "messages": messages,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
        }

        resp = requests.post(url, json=payload, headers=headers, timeout=60)
        if resp.status_code >= 400:
            try:
                detail = resp.json()
            except Exception:
                detail = resp.text
            raise RuntimeError(f"OpenAI API error {resp.status_code}: {detail}")

        data = resp.json()
        # Format supposé proche d'OpenAI: choices[0].message.content
        content = (
            data.get("choices", [{}])[0]
            .get("message", {})
            .get("content", "")
        )
        if not content:
            # Fallback commun si l'API retourne 'text'
            content = data.get("choices", [{}])[0].get("text", "")
        return content.strip()

    def get_model_info(self) -> Dict[str, Any]:
        return {
            "model_name": self.model_name,
            "device": self.device,
            "is_loaded": self.is_loaded,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "provider": "openai",
            "base_url": self.base_url,
        }


# Instance globale (API compatible)
phi3_ai = Phi3AI()
