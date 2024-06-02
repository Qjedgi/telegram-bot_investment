import asyncio
import os
from datetime import datetime, timedelta
from tinkoff.invest import AsyncClient
from dotenv import load_dotenv, find_dotenv
from reportlab.platypus import SimpleDocTemplate, Paragraph
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.pagesizes import letter
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

load_dotenv(find_dotenv())
TOKEN = os.environ["TOKEN_TINKOFF"]

# Регистрация шрифта Arial
font_path = r'C:\Windows\Fonts\arial.ttf'  # Обновите этот путь в соответствии с местоположением Arial.ttf на вашем компьютере
pdfmetrics.registerFont(TTFont('Arial', font_path))

async def main():
    async with AsyncClient(TOKEN) as client:
        accounts = await client.users.get_accounts()
        operations = []

        for account in accounts.accounts:
            operations_response = await client.operations.get_operations(
                account_id=account.id,
                from_=datetime(2023, 9, 1),
                to=datetime.now()
            )

            for operation in operations_response.operations:
                operations.append({
                    "type": operation.type,
                    "payment": operation.payment.units + operation.payment.nano / 10 ** 9
                })

        # Группировка и сводка операций по типу
        summary = {}
        for operation in operations:
            if operation["type"] not in summary:
                summary[operation["type"]] = 0
            summary[operation["type"]] += operation["payment"]

        # Подготовка содержимого PDF
        story = []
        styles = getSampleStyleSheet()
        russian_style = ParagraphStyle(name='Russian', fontName='Arial', fontSize=12, leading=15)
        for key, value in summary.items():
            story.append(Paragraph(f"<b>{key}:</b><br/>{value:.2f}", russian_style))
        story.append(Paragraph("<b>Итого:</b><br/>" + str(sum(summary.values())), russian_style))

        # Генерация отчета PDF
        doc = SimpleDocTemplate("summary_report.pdf", pagesize=letter)
        doc.build(story)

if __name__ == "__main__":
    asyncio.run(main())