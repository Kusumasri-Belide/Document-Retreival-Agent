import os
from backend.config import DOCS_DIR, PROCESSED_DIR

# Unstructured import blocks (install unstructured with extras if you want better OCR)
from unstructured.partition.pdf import partition_pdf
from unstructured.partition.docx import partition_docx
from unstructured.partition.ppt import partition_ppt
from unstructured.partition.pptx import partition_pptx

def _write_txt(base_name: str, text: str):
    out_path = os.path.join(PROCESSED_DIR, base_name + ".txt")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(text)

def _extract_text_generic(path: str) -> str:
    # Fallback for .txt / .csv / etc.
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()

def _join(elems):
    return "\n".join([e.text for e in elems if getattr(e, "text", None)])

def extract_all():
    for root, _, files in os.walk(DOCS_DIR):
        for fn in files:
            fp = os.path.join(root, fn)
            rel = os.path.relpath(fp, DOCS_DIR)
            base = os.path.splitext(rel)[0].replace("\\", "__").replace("/", "__")

            try:
                if fn.lower().endswith(".pdf"):
                    text = _join(partition_pdf(filename=fp))
                elif fn.lower().endswith(".docx"):
                    text = _join(partition_docx(filename=fp))
                elif fn.lower().endswith(".pptx"):
                    text = _join(partition_pptx(filename=fp))
                elif fn.lower().endswith(".ppt"):
                    text = _join(partition_ppt(filename=fp))
                elif fn.lower().endswith(".txt") or fn.lower().endswith(".csv"):
                    text = _extract_text_generic(fp)
                else:
                    # Unknown -> try generic read
                    text = _extract_text_generic(fp)
                if text and text.strip():
                    _write_txt(base, text)
                    print(f"📝 Processed → {base}.txt")
            except Exception as e:
                print(f"⚠️  Failed to process {rel}: {e}")

    print("✅ Extraction finished: see data/processed/")

if __name__ == "__main__":
    os.makedirs(PROCESSED_DIR, exist_ok=True)
    extract_all()
