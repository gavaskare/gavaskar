!pip install torch transformers sentencepiece deepmultilingualpunctuation
!pip install youtube-transcript-api spacy deep-translator
!python -m spacy download en_core_web_sm

import spacy
from youtube_transcript_api import YouTubeTranscriptApi
from deep_translator import GoogleTranslator
import textwrap
import re

# Advanced Punctuation and Summarization ---
from deepmultilingualpunctuation import PunctuationModel
from transformers import pipeline

# Load spaCy for sentence splitting of the final summary
nlp = spacy.load('en_core_web_sm')

# --- NEW: Load AI Models (this may download models on the first run) ---
print("Loading AI models, this might take a moment on the first run...")
punc_model = PunctuationModel()
# Using a smaller, efficient model for summarization
summarizer = pipeline("summarization", model="t5-small")
print("Models loaded successfully!")
# --- END NEW ---


def get_video_id(youtube_link):
    """Extracts the video ID from a YouTube URL."""
    if "v=" in youtube_link:
        return youtube_link.split("v=")[1].split("&")[0]
    elif "youtu.be/" in youtube_link:
        return youtube_link.split("youtu.be/")[1].split("?")[0]
    return None

def get_transcript(video_id):
    """Fetches the transcript and combines it into a single text block."""
    try:
        transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
        # Combine all text parts into one single string
        full_transcript = " ".join([d['text'] for d in transcript_list])
        return full_transcript
    except Exception as e:
        return f"Error fetching transcript: {e}"

# --- NEW and IMPROVED: Punctuation and Capitalization Function ---
def enhance_transcript(text):
    """Restores punctuation and capitalizes standalone 'i' using an AI model."""
    # Restore punctuation
    punctuated_text = punc_model.restore_punctuation(text)

    # Capitalize standalone 'i' using regex for better accuracy
    corrected_text = re.sub(r'\b i \b', ' I ', punctuated_text)
    return corrected_text
# --- END NEW ---


# Abstractive Summarization Function ---
def summarize_abstractively(text, max_summary_length=150, min_summary_length=50):
    """
    Generates a concise, abstractive summary using a transformer model.
    The model creates new sentences to capture the key points.
    """
    if not text:
        return []

    try:
        # The summarizer pipeline returns a list with a dictionary
        summary_result = summarizer(text, max_length=max_summary_length, min_length=min_summary_length, do_sample=False)
        summary_text = summary_result[0]['summary_text']

        # Use spaCy to split the generated summary into distinct sentences (key points)
        doc = nlp(summary_text)
        return [sent.text.strip() for sent in doc.sents]
    except Exception as e:
        print(f"An error occurred during summarization: {e}")
        return ["Could not generate a summary due to an error."]
# --- END NEW ---


def translate_points(points, target_lang):
    """Translates a list of text points to the target language."""
    if not points or points[0].startswith("Could not"):
        return points # Return original points if they are an error message
    try:
        return [GoogleTranslator(source='auto', target=target_lang).translate(p) for p in points]
    except Exception as e:
        return [f"Translation error: {e}"]

def format_text_for_display(text, words_per_line=20):
    """Formats text to wrap at a certain width for better console display."""
    # A simple approximation for wrapping width
    return textwrap.fill(text, width=words_per_line * 6)

def main():
    print("🎥 Welcome to the AI-Powered YouTube Summary Chatbot 🎥")
    link = input("Enter the YouTube video URL: ").strip()
    video_id = get_video_id(link)
    if not video_id:
        print("Invalid YouTube URL.")
        return

    print("\n📄 Fetching transcript...")
    raw_transcript = get_transcript(video_id)
    if raw_transcript.startswith("Error"):
        print(raw_transcript)
        return

    print("\n✨ Enhancing transcript with punctuation & capitalization...")
    enhanced_transcript = enhance_transcript(raw_transcript)

    print("\n--- Full Enhanced Transcript ---\n")
    print(format_text_for_display(enhanced_transcript))
    print("\n✅ Transcript processed successfully!\n")

    print("\n🧠 Generating a concise summary...")
    key_points = summarize_abstractively(enhanced_transcript)
    if not key_points:
        print("Could not summarize the transcript.")
        return

    print("\n--- Key Points in English ---")
    for i, point in enumerate(key_points, 1):
        print(format_text_for_display(f"{i}. {point}"))
        print() # Add a blank line for readability

    print("\n🌐 Translate summary to a local Indian language?")
    print("Available options: Hindi, Tamil, Telugu, Bengali")
    lang_input = input("Enter language name or type 'no' to skip: ").strip().lower()
    lang_map = {"hindi": "hi", "tamil": "ta", "telugu": "te", "bengali": "bn"}

    if lang_input == "no":
        print("\nNo translation selected. Exiting chatbot. 👋")
    elif lang_input in lang_map:
        print(f"\n🔄 Translating summary to {lang_input.capitalize()}...")
        translated = translate_points(key_points, lang_map[lang_input])
        print(f"\n--- Key Points in {lang_input.capitalize()} ---")
        for i, point in enumerate(translated, 1):
            print(format_text_for_display(f"{i}. {point}"))
            print()
    else:
        print("\nInvalid language input. Exiting. 👋")

if __name__ == "__main__":
    main()
