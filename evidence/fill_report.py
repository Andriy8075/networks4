# -*- coding: utf-8 -*-
"""Fill Lab 4 report with captured console outputs, PCAP analysis and screenshots."""

from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor, Twips

ROOT = Path(r"c:\Users\Admin\projects\NetworkLabs")
SOURCE = ROOT / "lab2" / "Ашомка_Андрій_ІМ-34_ЛР2.docx"
TARGET = ROOT / "lab4" / "Ашомка_Андрій_ІМ-34_ЛР4.docx"
EVIDENCE = ROOT / "lab4" / "evidence"
CONSOLE = EVIDENCE / "console"
SHOTS = EVIDENCE / "shots"
NGINX = EVIDENCE / "nginx"
COLOR = RGBColor(0x1F, 0x29, 0x37)


def read_text(path: Path, max_chars: int = 3500) -> str:
    text = path.read_text(encoding="utf-8", errors="replace").strip()
    if len(text) > max_chars:
        text = text[:max_chars] + "\n…[обрізано]"
    return text


def console_block(cwd: str, command: str, output: str = "", host: str = "andrii@DESKTOP-7BD93CN") -> str:
    """Format like Lab2: prompt with path + command + output."""
    prompt = f"{host}:{cwd}$ {command}"
    body = (output or "").strip()
    # If the saved evidence already starts with the same prompt, keep it as-is.
    if body.startswith(host + ":") or body.startswith("andrii@"):
        return body
    if body:
        return f"{prompt}\n{body}"
    return prompt


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
    write_cell(cell, text, size=9)
    borders(cell)
    return table


def grid(doc, rows, header=True):
    table = doc.add_table(rows=len(rows), cols=len(rows[0]))
    width(table)
    for r_index, row in enumerate(rows):
        for c_index, value in enumerate(row):
            cell = table.cell(r_index, c_index)
            write_cell(cell, value, bold=header and r_index == 0, size=9)
            borders(cell)
            if header and r_index == 0:
                shade(cell, "F3F4F6")
    spacer = doc.add_paragraph()
    spacer.paragraph_format.space_before = Twips(0)
    spacer.paragraph_format.space_after = Twips(60)
    return table


def picture(doc, name):
    path = SHOTS / name
    if not path.is_file():
        one_cell(doc, f"[немає файлу скріна: {name}]")
        return
    paragraph = doc.add_paragraph()
    paragraph.paragraph_format.first_line_indent = Twips(0)
    paragraph.paragraph_format.space_after = Twips(120)
    run = paragraph.add_run()
    run.add_picture(str(path), width=Cm(15.2))


def main():
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
        "Робота виконана на готовому Compose-проєкті ЛР1. Основне завдання — аналіз "
        "DNS/TCP/HTTP/Redis. Додаткове — відтворення помилкового порту Nginx (502) і відновлення.",
    )
    for index, task in enumerate(
        [
            "Перевірити працездатність ЛР1; зафіксувати сервіси proxy/app/db, порт 8080 та операцію Redis.",
            "Захопити трафік у netns proxy → normal.pcap (dig + curl).",
            "Захопити трафік у netns db → database.pcap (повторний curl).",
            "Знайти DNS query/answer з однаковим Transaction ID і перевірити IP app.",
            "Показати TCP handshake клієнт→проксі та проксі→app.",
            "Знайти з’єднання app→Redis у database.pcap.",
            "Знайти HTTP на ділянках клієнт→проксі та проксі→app.",
            "Показати команду Redis і зв’язок з HTTP Visit count.",
            "Додатково: зламати upstream-порт Nginx (8000→8080), failure.pcap, журнал.",
            "Додатково: знайти 502 і SYN+RST на :8080; пояснити причину.",
            "Додатково: відновити конфіг, recovered.pcap, порівняти три стани.",
        ],
        start=1,
    ):
        body(doc, f"{index}. {task}")

    heading(doc, "Результати виконання")
    heading(doc, "Середовище та версії")
    body(
        doc,
        "Захоплення виконувалось у WSL2 Ubuntu з Docker Engine; аналіз PCAP — у Wireshark 4.6.10 на Windows. "
        "Використано стенд ЛР1 без зміни топології мереж frontend (172.29.0.0/24) і backend (172.30.0.0/24).",
    )
    versions = CONSOLE / "00_versions.txt"
    one_cell(
        doc,
        (read_text(versions) if versions.exists() else "")
        + "\n\n"
        + console_block(
            "/mnt/c/Users/Admin/projects/NetworkLabs/lab4/evidence/pcaps",
            "# аналіз PCAP: Wireshark 4.6.10 (Windows GUI) / tshark",
            "Wireshark 4.6.10 (Windows)\n"
            "Хост-порт проксі: 8080→80\n"
            "Захоплення: tcpdump -i any у мережевому просторі контейнера (sidecar netshoot / nsenter).",
        ),
    )
    body(
        doc,
        " Версії та середовище фіксують відтворюваність захоплень і аналізу.",
        bold_lead="Інтерпретація.",
    )

    heading(doc, "5.3.1. Контейнери, точки запису та команди")
    body(
        doc,
        "Для normal.pcap захоплення виконано в мережевому просторі контейнера proxy (інтерфейс any). "
        "Для database.pcap — у мережевому просторі контейнера db. HTTP: curl -i http://127.0.0.1:8080/. "
        "DNS у netns проксі: dig @127.0.0.11 app. Сервіси: proxy, app (дві репліки), db (Redis). "
        "Операція Redis у коді: r.incr('counter') на GET /.",
    )
    grid(
        doc,
        [
            ["PCAP", "Контейнер / netns", "Інтерфейс", "Що ініційовано під час запису"],
            ["normal.pcap", "proxy", "any", "dig @127.0.0.11 app + curl :8080"],
            ["database.pcap", "db", "any", "повторний curl через проксі (INCR)"],
            ["failure.pcap", "proxy", "any", "curl після app:8080 у Nginx"],
            ["recovered.pcap", "proxy", "any", "curl після відновлення app:8000"],
        ],
    )
    label(doc, "Вивід консолі (перевірка стенда):")
    one_cell(doc, read_text(CONSOLE / "01_check_lab1.txt", 2500))
    label(doc, "Знімок інтерфейсу:")
    picture(doc, "01-compose-ps.png")
    picture(doc, "02-curl-ok.png")
    label(doc, "HTTP-відповідь під час database.pcap:")
    one_cell(doc, read_text(CONSOLE / "03_curl_database.txt", 1200))
    label(doc, "DNS dig під час normal.pcap:")
    one_cell(doc, read_text(CONSOLE / "02_dig_app.txt", 800))
    label(doc, "IP контейнерів app (перевірка DNS):")
    one_cell(doc, read_text(CONSOLE / "02_app_ips.txt", 800))
    body(
        doc,
        " Підтверджено імена сервісів proxy/app/db, порт хоста 8080 і працездатність шляху "
        "клієнт→проксі→застосунок→Redis перед аналізом PCAP.",
        bold_lead="Інтерпретація.",
    )

    heading(doc, "5.3.2. DNS-запит і відповідь")
    body(
        doc,
        "У normal.pcap застосовано фільтр dns. Знайдено запит імені app і відповідь із тим самим "
        "Transaction ID 0x6f7d. Тип A повернув адреси обох реплік застосунку в мережі frontend.",
    )
    grid(
        doc,
        [
            ["Поле", "Значення"],
            ["Фільтр", "dns"],
            ["№ пакета запиту", "1"],
            ["№ пакета відповіді", "2"],
            ["Transaction ID", "0x6f7d"],
            ["Запитане ім’я", "app"],
            ["Тип запису", "A"],
            ["Отримана IP", "172.29.0.3, 172.29.0.2"],
            [
                "Як перевірено належність IP",
                "docker inspect / network inspect frontend: code-app-1=172.29.0.2, code-app-2=172.29.0.3",
            ],
        ],
    )
    label(doc, "Знімок інтерфейсу (фільтр dns):")
    picture(doc, "03-dns-query.png")
    picture(doc, "04-dns-answer.png")
    body(
        doc,
        " DNS Docker (127.0.0.11) повертає адреси сервісу app у мережі frontend; "
        "nginx далі встановлює TCP до однієї з реплік (у цьому захопленні — 172.29.0.3:8000).",
        bold_lead="Інтерпретація.",
    )

    heading(doc, "5.3.3. TCP-з’єднання")
    body(
        doc,
        "У normal.pcap показано повний handshake клієнт→проксі (stream 0) і проксі→застосунок (stream 1). "
        "У database.pcap обмін із Redis іде вже відкритим з’єднанням app→db на порт 6379 "
        "(повторний handshake для цього запиту відсутній — це допускає методичка).",
    )
    label(doc, "Номери SYN → SYN/ACK → ACK (клієнт → проксі):")
    one_cell(doc, "SYN: 3 ; SYN/ACK: 4 ; ACK: 5")
    label(doc, "Номери SYN → SYN/ACK → ACK (проксі → застосунок):")
    one_cell(doc, "SYN: 8 ; SYN/ACK: 9 ; ACK: 10")
    grid(
        doc,
        [
            ["З’єднання", "PCAP", "IP джерела", "Порт", "IP призначення", "Порт", "tcp.stream"],
            ["клієнт → проксі", "normal.pcap", "172.29.0.1", "60826", "172.29.0.4", "80", "0"],
            ["проксі → застосунок", "normal.pcap", "172.29.0.4", "53528", "172.29.0.3", "8000", "1"],
            ["застосунок → БД", "database.pcap", "172.30.0.4", "53104", "172.30.0.2", "6379", "0"],
        ],
    )
    label(doc, "Знімок інтерфейсу:")
    picture(doc, "05-tcp-client-proxy.png")
    picture(doc, "06-tcp-proxy-app.png")
    picture(doc, "07-tcp-app-db.png")
    body(
        doc,
        " Три з’єднання відповідають reverse proxy і доступу Flask до Redis: "
        "клієнт закінчує TCP на nginx (порт 80), проксі сам відкриває TCP до app:8000, "
        "а застосунок ходить у Redis у мережі backend на 6379.",
        bold_lead="Інтерпретація.",
    )

    heading(doc, "5.3.4. HTTP-запит і відповідь на обох ділянках")
    grid(
        doc,
        [
            ["Ділянка", "№ запиту", "№ відповіді", "Метод", "URI", "Код"],
            ["клієнт → проксі", "6", "18", "GET", "/", "200"],
            ["проксі → застосунок", "11", "15", "GET", "/", "200"],
        ],
    )
    label(doc, "Знімок інтерфейсу:")
    picture(doc, "08-http-client-proxy.png")
    picture(doc, "09-http-proxy-app.png")
    body(
        doc,
        " Клієнт надсилає GET / на проксі; nginx відкриває окреме з’єднання до app:8000 "
        "і пересилає запит; відповідь 200 повертається клієнту тим самим шляхом.",
        bold_lead="Інтерпретація.",
    )

    heading(doc, "5.3.5. Команда Redis і зв’язок з HTTP")
    body(
        doc,
        "У database.pcap застосовано фільтр tcp.port == 6379. У payload пакетів видно RESP-команду "
        "збільшення ключа counter і цілу відповідь Redis. Клієнт redis-py у цьому захопленні "
        "надіслав INCRBY counter 1 (еквівалент інкременту лічильника з app.py: r.incr('counter')).",
    )
    grid(
        doc,
        [
            ["Поле", "Значення"],
            ["Фільтр", "tcp.port == 6379"],
            ["№ пакета команди", "1"],
            ["№ пакета відповіді", "2"],
            ["Команда", "INCRBY"],
            ["Аргументи / ключ", "counter, 1"],
            ["Тип і вміст відповіді Redis", "ціле :206"],
            ["Фрагмент HTTP-тіла (той самий запит)", "Visit count: 206 (див. curl database.pcap)"],
        ],
    )
    label(doc, "Фрагмент коду обробника (lab1/code/app.py):")
    one_cell(
        doc,
        console_block(
            "/mnt/c/Users/Admin/projects/NetworkLabs/lab1/code",
            "sed -n '10,16p' app.py",
            "    try:\n"
            "        visits = r.incr('counter')\n"
            "        return f\"Hello from Flask App! Visit count: {visits}\\n\"\n"
            "    except Exception as e:\n"
            "        return f\"Database error: {str(e)}\\n\", 500",
        ),
    )
    label(doc, "Вивід curl під час database.pcap:")
    one_cell(doc, read_text(CONSOLE / "03_curl_database.txt", 900))
    label(doc, "Знімок інтерфейсу:")
    picture(doc, "10-redis-stream.png")
    body(
        doc,
        " Значення лічильника у HTTP-відповіді узгоджується з відповіддю Redis (:206): "
        "обробник Flask безпосередньо відображає результат інкременту ключа counter.",
        bold_lead="Інтерпретація.",
    )

    heading(doc, "5.3.6. Високий рівень: помилковий порт і failure.pcap")
    body(
        doc,
        "Збережено копію справної конфігурації Nginx. У proxy_pass змінено лише порт застосунку "
        "з 8000 на 8080. Після nginx -t і reload захоплено failure.pcap і фрагмент журналу proxy. "
        "Клієнт отримав HTTP 502; у PCAP видно SYN на :8080 і RST/ACK у відповідь.",
    )
    label(doc, "Зміна конфігурації «було → стало»:")
    one_cell(doc, read_text(NGINX / "was_became.txt", 400))
    label(doc, "Перевірка nginx -t:")
    one_cell(doc, read_text(CONSOLE / "04_nginx_t.txt", 600))
    label(doc, "Відповідь curl (очікується 502):")
    one_cell(doc, read_text(CONSOLE / "05_curl_failure.txt", 1200))
    grid(
        doc,
        [
            ["Поле", "Значення"],
            ["Код відповіді клієнту", "502"],
            ["№ пакета HTTP 502", "13"],
            ["№ пакета SYN на wrong port", "9 (також 11 на другу репліку)"],
            ["№ пакета RST/ACK", "10 (також 12)"],
            ["Адреса:порт, куди стукав проксі", "172.29.0.2:8080 і 172.29.0.3:8080"],
            ["Порт у журналі Nginx", "upstream http://172.29.0.2:8080/ (і .3:8080)"],
            ["Фактичний listen застосунку", "8000"],
            ["Помилковий рядок конфігу", "proxy_pass http://app:8080;"],
        ],
    )
    label(doc, "Фрагмент журналу Nginx:")
    one_cell(doc, read_text(NGINX / "proxy_log_failure.txt", 2200))
    label(doc, "Знімок інтерфейсу:")
    picture(doc, "11-failure-502.png")
    picture(doc, "12-failure-rst.png")
    picture(doc, "13-nginx-log.png")
    body(
        doc,
        " Клієнт успішно з’єднується з проксі на опублікованому 8080→80. "
        "Проксі звертається до правильного імені app, але на закритий порт 8080, "
        "отримує Connection refused / RST і відповідає клієнту 502. "
        "Код 502 — наслідок; причина — неправильний upstream-порт у конфігурації.",
        bold_lead="Інтерпретація.",
    )

    heading(doc, "5.3.7. Високий рівень: відновлення і recovered.pcap")
    body(
        doc,
        "Відновлено рядок proxy_pass http://app:8000;, виконано nginx -t і reload. "
        "Повторний запит записано у recovered.pcap: знову SYN на порт 8000 і HTTP 200.",
    )
    label(doc, "Відновлення / перевірка:")
    restore_parts = []
    for name in (
        "06_nginx_restore.txt",
        "06_curl_ok_after_restore.txt",
        "07_curl_recovered.txt",
    ):
        path = CONSOLE / name
        if path.exists():
            restore_parts.append(read_text(path, 1500))
    one_cell(doc, "\n\n".join(restore_parts) if restore_parts else "[немає файлу відновлення]")
    grid(
        doc,
        [
            ["Стан", "PCAP / ознака", "Результат"],
            ["Справна конфігурація", "normal.pcap", "HTTP 200, TCP до :8000"],
            ["Помилка порту", "failure.pcap", "HTTP 502, SYN+RST на :8080"],
            ["Відновлення", "recovered.pcap", "HTTP 200 (пакети 13/16), SYN до :8000 (пакети 6–7)"],
        ],
    )
    label(doc, "Знімок інтерфейсу:")
    picture(doc, "14-recovered-ok.png")
    body(
        doc,
        " Після повернення порту 8000 проксі знову встановлює TCP із застосунком "
        "і віддає успішну HTTP-відповідь; три PCAP демонструють цикл норма / збій / відновлення.",
        bold_lead="Інтерпретація.",
    )

    heading(doc, "Висновки")
    body(
        doc,
        "У роботі виконано захоплення трафіку контейнерної мережі ЛР1 у netns проксі та БД "
        "і аналіз у Wireshark. Показано резолв імені app через DNS Docker (Transaction ID 0x6f7d, "
        "A-записи 172.29.0.2/172.29.0.3), два окремі TCP-з’єднання на шляху клієнт→проксі→застосунок, "
        "HTTP GET / з кодом 200 на обох ділянках та інкремент ключа counter у Redis, узгоджений "
        "з тілом HTTP-відповіді. Додатково відтворено помилку неправильного порту upstream у Nginx: "
        "клієнт отримує 502, а в PCAP видно SYN і RST на :8080; після відновлення конфігурації "
        "працездатність підтверджено recovered.pcap.",
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
