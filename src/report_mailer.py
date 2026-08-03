"""Generate an AI-infrastructure report as a PDF and notify a developer-tools user."""

from __future__ import annotations

import argparse
from datetime import date
from pathlib import Path

from infrai_email import infrai, new_idempotency_key


def report_text(report_date: date) -> str:
    return (
        f"Developer tools report - {report_date.isoformat()}\n\n"
        "Conclusion: retrieval quality is easiest to improve when the agent records "
        "which sources it used, because that makes an answer inspectable before the "
        "next prompt or model change obscures the reason for it.\n\n"
        "This report treats a RAG system as two connected loops: retrieval chooses "
        "context and the agent turns context into a tool decision. Start with source "
        "citations in traces; compare that focused signal with a larger prompt rewrite "
        "before changing several variables at once.\n"
    )


def write_pdf(text: str, destination: Path) -> Path:
    """Write a compact single-page PDF using only Python's standard library."""
    escaped_lines = [line.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)") for line in text.splitlines()]
    commands = ["BT", "/F1 11 Tf", "72 750 Td"]
    for line in escaped_lines:
        commands.append(f"({line}) Tj")
        commands.append("0 -16 Td")
    commands.append("ET")
    stream = "\n".join(commands).encode("latin-1", errors="replace")
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 5 0 R >> >> /Contents 4 0 R >>",
        b"<< /Length " + str(len(stream)).encode() + b" >>\nstream\n" + stream + b"\nendstream",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    ]
    pdf = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for index, obj in enumerate(objects, start=1):
        offsets.append(len(pdf))
        pdf.extend(f"{index} 0 obj\n".encode())
        pdf.extend(obj)
        pdf.extend(b"\nendobj\n")
    start_xref = len(pdf)
    pdf.extend(f"xref\n0 {len(objects) + 1}\n0000000000 65535 f \n".encode())
    for offset in offsets[1:]:
        pdf.extend(f"{offset:010d} 00000 n \n".encode())
    pdf.extend(f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{start_xref}\n%%EOF\n".encode())
    destination.write_bytes(pdf)
    return destination


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate a developer-tools report and email its summary.")
    parser.add_argument("--to", required=True, help="Recipient email address")
    parser.add_argument("--output", default="developer-tools-report.pdf", help="PDF destination")
    args = parser.parse_args()

    today = date.today()
    text = report_text(today)
    pdf_path = write_pdf(text, Path(args.output))
    result = infrai.email.send(
        {
            "to": args.to,
            "subject": f"Developer tools report: {today.isoformat()}",
            "text": f"Your generated PDF report is ready at {pdf_path.resolve()}.\n\n{text}",
        },
        new_idempotency_key(),
    )
    print(f"Generated {pdf_path} and sent report email: {result['message_id']}")


if __name__ == "__main__":
    main()
