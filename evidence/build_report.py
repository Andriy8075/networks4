# -*- coding: utf-8 -*-
"""Build the Lab 4 report template (placeholders for screenshots / packet numbers)."""

from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Pt, RGBColor, Twips

ROOT = Path(r"c:\Users\Admin\projects\NetworkLabs")
SOURCE = ROOT / "lab2" / "Ашомка_Андрій_ІМ-34_ЛР2.docx"
TARGET = ROOT / "lab4" / "Ашомка_Андрій_ІМ-34_ЛР4.docx"
COLOR = RGBColor(0x1F, 0x29, 0x37)


def replace_text(paragraph, text):
    if not paragraph.runs:
        paragraph.add_run(text)
        return
    paragraph.runs[0].text = text
    for run in paragraph.runs[1:]:
        run.text = ""


def heading(doc, text):
    paragraph = doc.add_paragraph()
    paragraph.paragraph_format.space_before = Twips(280)
    paragraph.paragraph_format.space_after = Twips(120)
    paragraph.paragraph_format.first_line_indent = Twips(0)
    run = paragraph.add_run(text)
    run.bold = True
    return paragraph


def body(doc, text, bold_lead=None):
    paragraph = doc.add_paragraph()
    paragraph.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    paragraph.paragraph_format.space_before = Twips(0)
    paragraph.paragraph_format.space_after = Twips(120)
    paragraph.paragraph_format.first_line_indent = Twips(709)
    if bold_lead:
        lead = paragraph.add_run(bold_lead)
        lead.bold = True
        paragraph.add_run(text)
    else:
        paragraph.add_run(text)
    return paragraph


def label(doc, text):
    paragraph = doc.add_paragraph()
    paragraph.paragraph_format.space_before = Twips(0)
    paragraph.paragraph_format.space_after = Twips(60)
    paragraph.paragraph_format.first_line_indent = Twips(0)
    paragraph.add_run(text)
    return paragraph


def borders(cell):
    tc_pr = cell._tc.get_or_add_tcPr()
    edges = OxmlElement("w:tcBorders")
    for name in ("top", "left", "bottom", "right"):
        edge = OxmlElement(f"w:{name}")
        edge.set(qn("w:val"), "single")
        edge.set(qn("w:sz"), "4")
        edge.set(qn("w:space"), "0")
        edge.set(qn("w:color"), "D1D5DB")
        edges.append(edge)
    tc_pr.append(edges)


def shade(cell, fill):
    tc_pr = cell._tc.get_or_add_tcPr()
    shading = OxmlElement("w:shd")
    shading.set(qn("w:val"), "clear")
    shading.set(qn("w:fill"), fill)
    tc_pr.append(shading)


def width(table):
    table.autofit = True
    tbl_w = OxmlElement("w:tblW")
    tbl_w.set(qn("w:w"), "5000")
    tbl_w.set(qn("w:type"), "pct")
    table._tbl.tblPr.append(tbl_w)


def write_cell(cell, text, bold=False, size=10):
    cell.text = ""
    lines = text.split("\n")
    for index, line in enumerate(lines):
        paragraph = cell.paragraphs[0] if index == 0 else cell.add_paragraph()
        paragraph.paragraph_format.space_before = Twips(0)
        paragraph.paragraph_format.space_after = Twips(0)
        paragraph.paragraph_format.first_line_indent = Twips(0)
        run = paragraph.add_run(line)
        run.bold = bold
        run.font.name = "Times New Roman"
        run.font.size = Pt(size)
        run.font.color.rgb = COLOR
        run._element.rPr.rFonts.set(qn("w:eastAsia"), "Times New Roman")


def one_cell(doc, text):
    table = doc.add_table(rows=1, cols=1)
    width(table)
    cell = table.cell(0, 0)
    write_cell(cell, text, size=10)
    borders(cell)
    return table


def grid(doc, rows, header=True):
    table = doc.add_table(rows=len(rows), cols=len(rows[0]))
    width(table)
    for r_index, row in enumerate(rows):
        for c_index, value in enumerate(row):
            cell = table.cell(r_index, c_index)
            write_cell(cell, value, bold=header and r_index == 0, size=10)
            borders(cell)
            if header and r_index == 0:
                shade(cell, "F3F4F6")
    spacer = doc.add_paragraph()
    spacer.paragraph_format.space_before = Twips(0)
    spacer.paragraph_format.space_after = Twips(60)
    return table


def main():
    if not SOURCE.is_file():
        raise SystemExit(f"Source styles document not found: {SOURCE}")

    doc = Document(str(SOURCE))
    replace_text(doc.paragraphs[8], "Лабораторна робота №4")
    replace_text(
        doc.paragraphs[10],
        "на тему\n«Аналіз мережевого трафіку. Дослідження DNS, TCP та HTTP "
        "у контейнерній мережі та діагностика несправностей вебпроксі»",
    )

    body_xml = doc.element.body
    start = doc.paragraphs[28]._p
    children = list(body_xml)
    start_index = children.index(start)
    for child in children[start_index:]:
        if child.tag == qn("w:sectPr"):
            continue
        body_xml.remove(child)

    break_paragraph = doc.add_paragraph()
    break_paragraph.paragraph_format.space_after = Twips(0)
    break_paragraph.add_run().add_break(WD_BREAK.PAGE)

    heading(doc, "Мета роботи")
    body(
        doc,
        "Метою лабораторної роботи є набуття практичних навичок запису мережевого "
        "трафіку контейнеризованого застосунку та його аналізу у Wireshark. "
        "Досліджується визначення адреси сервісу через DNS, встановлення TCP-з’єднання "
        "та обмін HTTP-запитами й відповідями, а також діагностика типової несправності "
        "вебпроксі (звернення до правильного контейнера на неправильний порт).",
    )

    heading(doc, "Завдання")
    body(
        doc,
        "Робота виконується на готовому Compose-проєкті ЛР1 без розподілу на варіанти. "
        "Основне завдання — середній рівень (12 балів). Додаткове завдання піднімає оцінку "
        "до високого рівня (15 балів разом з основним).",
    )
    tasks = [
        "Перевірити працездатність проєкту ЛР1; записати назви сервісів проксі, застосунку та БД, порт хоста до проксі та операцію Redis для HTTP-запиту.",
        "Виконати захоплення у контейнері проксі під час DNS- і HTTP-запиту; зберегти normal.pcap.",
        "Виконати захоплення у контейнері БД під час повторного HTTP через проксі; зберегти database.pcap.",
        "У normal.pcap знайти DNS-запит і відповідь з однаковим Transaction ID; записати номери пакетів, тип A та IP; перевірити належність IP застосунку.",
        "Показати TCP handshake клієнт→проксі та окремо проксі→застосунок; записати PCAP, IP, порти, tcp.stream.",
        "У database.pcap знайти з’єднання застосунку з БД; записати PCAP, IP, порти, tcp.stream.",
        "Знайти HTTP-запит і відповідь на ділянках клієнт→проксі та проксі→застосунок; пояснити шлях запиту/відповіді.",
        "У database.pcap знайти команду Redis (порт 6379), Follow TCP Stream; зіставити з HTTP-відповіддю.",
        "Додатково: зберегти копію Nginx, змінити лише порт upstream на закритий, nginx -t і reload.",
        "Додатково: захопити failure.pcap і фрагмент журналу; знайти HTTP 502 та SYN+RST на неправильний порт.",
        "Додатково: порівняти порт із захоплення, журналу та фактичний listen; пояснити причину 502.",
        "Додатково: відновити конфігурацію, зберегти recovered.pcap, порівняти стани normal / failure / recovered.",
    ]
    for index, task in enumerate(tasks, start=1):
        body(doc, f"{index}. {task}")

    heading(doc, "Результати виконання")

    heading(doc, "Середовище та версії")
    body(
        doc,
        "Дослід виконувався у WSL2 Ubuntu з Docker Engine; аналіз PCAP — у Wireshark на Windows. "
        "Використано образи та конфігурацію проєкту ЛР1 без зміни топології мереж frontend/backend.",
    )
    label(doc, "Вивід консолі / версії:")
    one_cell(
        doc,
        "[ВСТАВТЕ ВИВІД КОНСОЛІ: docker version / docker compose version / wireshark -v]\n"
        "ОС: Ubuntu у WSL2; Docker Desktop на Windows\n"
        "Стенд: lab1/code (proxy, app×2, db/Redis)\n"
        "Хост-порт проксі: 8080→80",
    )
    body(
        doc,
        " Версії та середовище фіксують відтворюваність захоплень і аналізу.",
        bold_lead="Інтерпретація.",
    )

    heading(doc, "5.3.1. Контейнери, точки запису та команди")
    body(
        doc,
        "Для normal.pcap захоплення виконано в мережевому просторі контейнера proxy "
        "(інтерфейс any). Для database.pcap — у мережевому просторі контейнера db. "
        "HTTP-запит на хості: curl -i http://127.0.0.1:8080/. DNS у netns проксі: "
        "dig @127.0.0.11 app. Сервіси: proxy, app, db. Операція Redis: INCR counter.",
    )
    grid(
        doc,
        [
            ["PCAP", "Контейнер / netns", "Інтерфейс", "Що ініційовано під час запису"],
            ["normal.pcap", "proxy", "any", "dig @127.0.0.11 app + curl через :8080"],
            ["database.pcap", "db", "any", "повторний curl через проксі (INCR)"],
        ],
    )
    label(doc, "Вивід консолі (перевірка стенда):")
    one_cell(
        doc,
        "[ВСТАВТЕ ВИВІД КОНСОЛІ з evidence/console/01_check_lab1.txt або docker compose ps + curl]",
    )
    label(doc, "Знімок інтерфейсу:")
    one_cell(doc, "[ВСТАВТЕ СКРІН: evidence/shots/01-compose-ps.png та/або 02-curl-ok.png]")
    label(doc, "HTTP-відповідь під час database.pcap:")
    one_cell(
        doc,
        "[ВСТАВТЕ ВИВІД КОНСОЛІ з evidence/console/03_curl_database.txt]",
    )
    body(
        doc,
        " Підтверджено імена сервісів, порт хоста 8080 і працездатність шляху "
        "клієнт→проксі→застосунок→Redis перед аналізом PCAP.",
        bold_lead="Інтерпретація.",
    )

    heading(doc, "5.3.2. DNS-запит і відповідь")
    body(
        doc,
        "У normal.pcap застосовано фільтр dns. Знайдено запит імені сервісу app і відповідь "
        "з тим самим Transaction ID. Тип запису A, повернуту IP звірено з адресою контейнера "
        "застосунку в мережі frontend.",
    )
    grid(
        doc,
        [
            ["Поле", "Значення"],
            ["Фільтр", "dns"],
            ["№ пакета запиту", "[ВСТАВТЕ № ПАКЕТА]"],
            ["№ пакета відповіді", "[ВСТАВТЕ № ПАКЕТА]"],
            ["Transaction ID", "[ВСТАВТЕ]"],
            ["Запитане ім’я", "app"],
            ["Тип запису", "A"],
            ["Отримана IP", "[ВСТАВТЕ IP]"],
            ["Як перевірено належність IP", "[ВСТАВТЕ: docker inspect / network inspect]"],
        ],
    )
    label(doc, "Знімок інтерфейсу:")
    one_cell(
        doc,
        "[ВСТАВТЕ СКРІН: 03-dns-query.png]\n[ВСТАВТЕ СКРІН: 04-dns-answer.png]",
    )
    body(
        doc,
        " DNS Docker (127.0.0.11) повертає адресу сервісу app, яку надалі використовує "
        "nginx для встановлення TCP до застосунку.",
        bold_lead="Інтерпретація.",
    )

    heading(doc, "5.3.3. TCP-з’єднання")
    body(
        doc,
        "У normal.pcap показано SYN→SYN/ACK→ACK для клієнт→проксі та окремо для проксі→застосунок. "
        "У database.pcap зафіксовано з’єднання застосунок→БД (порт 6379). Якщо з’єднання з Redis "
        "вже було відкрите, повторний handshake може бути відсутній — тоді вказано існуючий tcp.stream.",
    )
    label(doc, "Номери SYN → SYN/ACK → ACK (клієнт → проксі):")
    one_cell(
        doc,
        "SYN: [ВСТАВТЕ №] ; SYN/ACK: [ВСТАВТЕ №] ; ACK: [ВСТАВТЕ №]",
    )
    grid(
        doc,
        [
            ["З’єднання", "PCAP", "IP джерела", "Порт", "IP призначення", "Порт", "tcp.stream"],
            [
                "клієнт → проксі",
                "normal.pcap",
                "[IP]",
                "[порт]",
                "[IP proxy]",
                "80",
                "[N]",
            ],
            [
                "проксі → застосунок",
                "normal.pcap",
                "[IP proxy]",
                "[порт]",
                "[IP app]",
                "8000",
                "[N]",
            ],
            [
                "застосунок → БД",
                "database.pcap",
                "[IP app]",
                "[порт]",
                "[IP db]",
                "6379",
                "[N]",
            ],
        ],
    )
    label(doc, "Знімок інтерфейсу:")
    one_cell(
        doc,
        "[ВСТАВТЕ СКРІН: 05-tcp-client-proxy.png]\n"
        "[ВСТАВТЕ СКРІН: 06-tcp-proxy-app.png]\n"
        "[ВСТАВТЕ СКРІН: 07-tcp-app-db.png]",
    )
    body(
        doc,
        " Три з’єднання відповідають ролям reverse proxy і доступу застосунку до Redis: "
        "клієнт не має прямого TCP до Flask чи БД з хоста, окрім опублікованого порту проксі.",
        bold_lead="Інтерпретація.",
    )

    heading(doc, "5.3.4. HTTP-запит і відповідь на обох ділянках")
    grid(
        doc,
        [
            ["Ділянка", "№ запиту", "№ відповіді", "Метод", "URI", "Код"],
            ["клієнт → проксі", "[№]", "[№]", "GET", "/", "[200]"],
            ["проксі → застосунок", "[№]", "[№]", "GET", "/", "[200]"],
        ],
    )
    label(doc, "Знімок інтерфейсу:")
    one_cell(
        doc,
        "[ВСТАВТЕ СКРІН: 08-http-client-proxy.png]\n[ВСТАВТЕ СКРІН: 09-http-proxy-app.png]",
    )
    body(
        doc,
        " Клієнт надсилає GET / на проксі; nginx відкриває окреме з’єднання до app:8000 "
        "і пересилає запит; відповідь 200 повертається клієнту тим самим шляхом.",
        bold_lead="Інтерпретація.",
    )

    heading(doc, "5.3.5. Команда Redis і зв’язок з HTTP")
    body(
        doc,
        "У database.pcap застосовано фільтр tcp.port == 6379 (за потреби resp) і відкрито "
        "Follow → TCP Stream. Показано команду застосунку та відповідь Redis.",
    )
    grid(
        doc,
        [
            ["Поле", "Значення"],
            ["Фільтр", "tcp.port == 6379"],
            ["№ пакета команди", "[ВСТАВТЕ № ПАКЕТА]"],
            ["№ пакета відповіді", "[ВСТАВТЕ № ПАКЕТА]"],
            ["Команда", "INCR"],
            ["Аргументи / ключ", "counter"],
            ["Тип і вміст відповіді Redis", "[ВСТАВТЕ, напр. ціле :N]"],
            ["Фрагмент HTTP-тіла", "Visit count: [N]"],
        ],
    )
    label(doc, "Фрагмент коду обробника (lab1/code/app.py):")
    one_cell(
        doc,
        "visits = r.incr('counter')\n"
        "return f\"Hello from Flask App! Visit count: {visits}\\n\"",
    )
    label(doc, "Знімок інтерфейсу:")
    one_cell(doc, "[ВСТАВТЕ СКРІН: 10-redis-stream.png]")
    body(
        doc,
        " Значення лічильника у HTTP-відповіді збігається з результатом INCR у Redis, "
        "тобто обробник безпосередньо відображає відповідь БД клієнту.",
        bold_lead="Інтерпретація.",
    )

    heading(doc, "5.3.6. Високий рівень: помилковий порт і failure.pcap")
    body(
        doc,
        "Збережено копію справної конфігурації Nginx. У proxy_pass змінено лише порт "
        "застосунку з 8000 на 8080 (порт не прослуховується). Після nginx -t і reload "
        "захоплено failure.pcap і фрагмент журналу proxy.",
    )
    label(doc, "Зміна конфігурації «було → стало»:")
    one_cell(
        doc,
        "було:\n        proxy_pass http://app:8000;\n"
        "стало:\n        proxy_pass http://app:8080;",
    )
    grid(
        doc,
        [
            ["Поле", "Значення"],
            ["Код відповіді клієнту", "502"],
            ["№ пакета HTTP 502", "[ВСТАВТЕ № ПАКЕТА]"],
            ["№ пакета SYN на wrong port", "[ВСТАВТЕ № ПАКЕТА]"],
            ["№ пакета RST/ACK", "[ВСТАВТЕ № ПАКЕТА]"],
            ["Адреса:порт, куди стукав проксі", "[IP app]:8080"],
            ["Порт у журналі Nginx", "[ВСТАВТЕ з proxy_log_failure.txt]"],
            ["Фактичний listen застосунку", "8000"],
            ["Помилковий рядок конфігу", "proxy_pass http://app:8080;"],
        ],
    )
    label(doc, "Фрагмент журналу Nginx:")
    one_cell(doc, "[ВСТАВТЕ ВИВІД з evidence/nginx/proxy_log_failure.txt]")
    label(doc, "Знімок інтерфейсу:")
    one_cell(
        doc,
        "[ВСТАВТЕ СКРІН: 11-failure-502.png]\n"
        "[ВСТАВТЕ СКРІН: 12-failure-rst.png]\n"
        "[ВСТАВТЕ СКРІН: 13-nginx-log.png]",
    )
    body(
        doc,
        " Клієнт успішно з’єднується з проксі на опублікованому порті 8080→80. "
        "Проксі звертається до правильного імені app, але на закритий порт 8080, "
        "отримує RST і відповідає клієнту 502. Код 502 є наслідком; причина — "
        "неправильний upstream-порт у конфігурації.",
        bold_lead="Інтерпретація.",
    )

    heading(doc, "5.3.7. Високий рівень: відновлення і recovered.pcap")
    body(
        doc,
        "Відновлено правильний рядок proxy_pass http://app:8000;, виконано nginx -t і reload. "
        "Повторний запит записано у recovered.pcap.",
    )
    grid(
        doc,
        [
            ["Стан", "PCAP / ознака", "Результат"],
            ["Справна конфігурація", "normal.pcap", "HTTP 200, TCP до :8000"],
            ["Помилка порту", "failure.pcap", "HTTP 502, SYN+RST на :8080"],
            ["Відновлення", "recovered.pcap", "[ВСТАВТЕ: HTTP 200, TCP до :8000]"],
        ],
    )
    label(doc, "Номери пакетів у recovered.pcap (успіх):")
    one_cell(
        doc,
        "Успішний SYN/з’єднання до app:8000: [ВСТАВТЕ №]\n"
        "HTTP відповідь OK: [ВСТАВТЕ №]",
    )
    label(doc, "Знімок інтерфейсу:")
    one_cell(doc, "[ВСТАВТЕ СКРІН: 14-recovered-ok.png]")
    body(
        doc,
        " Після повернення порту 8000 проксі знову встановлює TCP із застосунком "
        "і віддає успішну HTTP-відповідь; три PCAP демонструють цикл "
        "норма / збій / відновлення.",
        bold_lead="Інтерпретація.",
    )

    heading(doc, "Висновки")
    body(
        doc,
        "У роботі виконано захоплення трафіку контейнерної мережі ЛР1 у netns проксі та БД "
        "і аналіз у Wireshark. Показано резолв імені app через DNS Docker, два окремі TCP-з’єднання "
        "на шляху клієнт→проксі→застосунок, HTTP GET / з кодом 200 на обох ділянках та команду "
        "Redis INCR counter, узгоджену з тілом HTTP-відповіді. Додатково відтворено типову помилку "
        "неправильного порту upstream у Nginx: клієнт отримує 502, а в PCAP видно SYN і RST на "
        "закритий порт; після відновлення конфігурації працездатність підтверджено recovered.pcap.",
    )

    heading(doc, "Підписи")
    body(doc, "Виконавець: Ашомка Андрій Петрович, група ІМ-34")
    body(doc, "Роботу прийняв: Мельник Назар Андрійович")
    body(doc, "Дата: ____________________")

    TARGET.parent.mkdir(parents=True, exist_ok=True)
    doc.save(str(TARGET))
    print(f"Wrote {TARGET}")


if __name__ == "__main__":
    main()
